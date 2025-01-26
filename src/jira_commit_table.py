import subprocess
import re
import datetime
import requests
import json
import sys
import logging
from prettytable import PrettyTable
import os
import certifi
import boto3
import textwrap
import time  # Import the time module

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
        sys.exit(1)

def configure_logging(logging_enabled):
    if logging_enabled:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.CRITICAL)  # Only log critical errors

def clone_or_pull_repo(repo_url, branch, directory):
    try:
        if not os.path.exists(directory):
            subprocess.run(['git', 'clone', repo_url, directory], check=True)
        os.chdir(directory)
        subprocess.run(['git', 'checkout', branch], check=True)
        subprocess.run(['git', 'pull'], check=True)
        logging.info(f"Checked out and pulled latest code for branch {branch} in repository {repo_url}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to clone or pull repo: {e}")
        sys.exit(1)

def get_git_log(days_from_today):
    try:
        since_date = (datetime.datetime.now() - datetime.timedelta(days=days_from_today)).strftime('%Y-%m-%d')
        result = subprocess.run(['git', 'log', '--since', since_date, '--pretty=format:%H|%an|%ad|%s', '--date=short'], check=True, stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get git log: {e}")
        sys.exit(1)

def parse_commit_messages(log, ticket_prefixes):
    commits = []
    ticket_pattern = re.compile(r'\b(?:' + '|'.join(ticket_prefixes) + r')-\d+\b')
    latest_commits = {}

    for line in log.splitlines():
        parts = line.split('|', 3)
        if len(parts) == 4:
            commit_hash, author, date, message = parts
            tickets = ticket_pattern.findall(message)
            for ticket in tickets:
                if ticket not in latest_commits or latest_commits[ticket]['date'] < date:
                    latest_commits[ticket] = {
                        'hash': commit_hash,
                        'author': author,
                        'date': date,
                        'message': message,
                        'tickets': tickets
                    }

    commits = list(latest_commits.values())
    return commits

def get_jira_issues(tickets, jira_base_url, jira_token, max_retries=3, backoff_factor=1):
    if not tickets:
        logging.warning("No tickets found in commit messages.")
        return {}
    
    issue_details = {}
    original_to_new_ticket_map = {}
    total_retries = 0
    start_time = time.time()
    
    for ticket in tickets:
        retries = 0
        while retries < max_retries:
            try:
                logging.debug(f"Starting individual query for ticket: {ticket}")
                url = f"{jira_base_url}/rest/api/2/issue/{ticket}"
                headers = {
                    "Authorization": f"Bearer {jira_token}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    issue = response.json()
                    key = issue['key']
                    status = issue['fields']['status']['name']
                    assignee = issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else "Unassigned"
                    summary = issue['fields']['summary']
                    issue_details[key] = {
                        "status": status,
                        "assignee": assignee,
                        "summary": summary
                    }
                    original_to_new_ticket_map[ticket] = key
                    logging.debug(f"Individual query successful for ticket: {ticket} assignee {assignee} status {status}")
                    logging.debug(f"Updated issue_details: {issue_details}")
                    break
                else:
                    logging.error(f"Failed to retrieve JIRA issue {ticket}: {response.status_code} - {response.text}")
                    retries += 1
                    total_retries += 1
                    time.sleep(backoff_factor * (2 ** retries))
            except requests.RequestException as e:
                logging.error(f"Request exception for ticket {ticket}: {e}")
                retries += 1
                total_retries += 1
                time.sleep(backoff_factor * (2 ** retries))
    
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Total execution time for JIRA requests: {execution_time:.2f} seconds")
    logging.info(f"Total retries: {total_retries}")
    
    logging.debug(f"Issue details after individual queries: {issue_details}")
    logging.debug(f"Original to new ticket map: {original_to_new_ticket_map}")

    return issue_details, original_to_new_ticket_map, execution_time, total_retries

def build_tables(commits, jira_base_url, jira_token, ignored_statuses, skipped_tickets):
    # Summary table for statuses
    status_table = PrettyTable()
    status_table.field_names = ["Status", "Number of Tickets"]

    # Detailed table
    detailed_table = PrettyTable()
    detailed_table.field_names = ["No", "Commit Date", "Assignee", "Status", "JIRA Ticket"]
    detailed_table.align["JIRA Ticket"] = "l"  # Left align the "JIRA Ticket" column

    # Collect all tickets
    all_tickets = {ticket for commit in commits for ticket in commit["tickets"] if ticket != "Unknown"}
    logging.info(f"All tickets collected from commits: {all_tickets}")
    issue_details, original_to_new_ticket_map, execution_time, total_retries = get_jira_issues(all_tickets, jira_base_url, jira_token)

    # Count tickets by status and assignee
    status_counts = {}
    assignee_counts = {}
    unassigned_count = 0
    for ticket, details in issue_details.items():
        if ticket in skipped_tickets:
            continue  # Skip specified tickets
        status = details["status"]
        assignee = details["assignee"]
        if status in ignored_statuses:
            continue  # Skip ignored statuses
        if assignee == "Unassigned":
            unassigned_count += 1
        else:
            assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    # Add rows to status table
    for status, count in status_counts.items():
        status_table.add_row([status, count])

    # Add rows to detailed table
    sr_no = 1
    seen_tickets = set()
    for commit in commits:
        for ticket in commit["tickets"]:
            if ticket in skipped_tickets:
                continue  # Skip specified tickets
            logging.debug(f"Processing ticket: {ticket}")
            # Use the new ticket key if it exists
            new_ticket = original_to_new_ticket_map.get(ticket, ticket)
            if new_ticket in issue_details and new_ticket not in seen_tickets:
                details = issue_details[new_ticket]
                if details["status"] in ignored_statuses:
                    continue  # Skip ignored statuses
                jira_url = f"{jira_base_url}/browse/{new_ticket}"
                summary = textwrap.shorten(details["summary"], width=50, placeholder="...")
                detailed_table.add_row([sr_no, commit["date"], details["assignee"], details["status"], f"==> {summary}\n{jira_url}"])
                seen_tickets.add(new_ticket)
                sr_no += 1
            elif new_ticket not in seen_tickets:
                # Include tickets not found in JIRA with "Unknown" status and assignee
                logging.debug(f"Ticket {ticket} not found in JIRA batch query, adding as Unknown")
                detailed_table.add_row([sr_no, commit["date"], "Unknown", "Unknown", f"*Unknown*\n{jira_base_url}/browse/{ticket}"])
                detailed_table.add_row(["-"*10, "-"*10, "-"*10, "-"*10, "-"*10])  # Add a line between rows
                seen_tickets.add(new_ticket)
                sr_no += 1

    return status_table, detailed_table, unassigned_count, execution_time, total_retries

def send_slack_message(slack_url, slack_token, channel, message):
    headers = {
        "Content-type": "application/json",
        "Authorization": f'Bearer {slack_token}',
    }
    data = {
        "channel": channel,
        "text": message
    }
    logging.info(f"Sending Slack message to channel {channel} with payload: {json.dumps(data, indent=2)}")
    response = requests.post(slack_url, headers=headers, data=json.dumps(data))
    logging.info(f"Slack API response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        logging.error(f"Failed to send Slack message: {response.status_code} - {response.text}")

def send_slack_messages(slack_url, slack_token, channel, messages):
    for message in messages:
        send_slack_message(slack_url, slack_token, channel, message)

def split_table_message(table, max_length=3500):
    table_str = table.get_string()
    messages = []
    while len(table_str) > max_length:
        split_index = table_str.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        messages.append(f"```\n{table_str[:split_index]}\n```")
        table_str = table_str[split_index:].strip()
    messages.append(f"```\n{table_str}\n```")
    return messages

def get_parameter_from_ssm(parameter_name):
    ssm_client = boto3.client('ssm', region_name='us-east-2')
    try:
        parameter = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return parameter['Parameter']['Value']
    except Exception as e:
        logging.error(f"Failed to retrieve parameter {parameter_name} from SSM: {e}")
        return None

def main(config_file):
    config = load_config(config_file)
    jira_base_url = config["jira_base_url"]
    ticket_prefixes = config["ticket_prefixes"]
    days_from_today = config.get("days_from_today", 30)  # Default to 30 days if not specified
    ignored_statuses = config.get("ignored_statuses", [])  # Default to empty list if not specified
    logging_enabled = config.get("logging_enabled", False)  # Default to False (disabled)
    slack_channel = config.get("slack_channel", "")  # Default to empty string if not specified
    slack_url = config.get("slack_url", "https://slack.com/api/chat.postMessage")  # Default Slack URL
    repo_url = config.get("repo_url", "")
    branch = config.get("branch", "")
    directory = config.get("directory", "aamp")
    skipped_tickets = config.get("skipped_tickets", [])  # Get skipped tickets from config

    # Configure logging
    configure_logging(logging_enabled)

    # Retrieve JIRA token and Slack token from environment variables or AWS SSM Parameter Store
    #jira_token = os.getenv('JIRA_TOKEN') 
    jira_token = get_parameter_from_ssm('/example_token/jiraToken')
    
    #slack_token = os.getenv('SLACK_TOKEN')
    slack_token = get_parameter_from_ssm('/example_token/slackToken')

    if not jira_token:
        logging.error("JIRA_TOKEN environment variable not set and failed to retrieve from SSM")
        sys.exit(1)
    if not slack_token:
        logging.error("SLACK_TOKEN environment variable not set and failed to retrieve from SSM")
        sys.exit(1)

    # Clone or pull the repository
    if repo_url and branch:
        clone_or_pull_repo(repo_url, branch, directory)

    git_log = get_git_log(days_from_today)
    logging.info(f"Git log:\n{git_log}")
    commits = parse_commit_messages(git_log, ticket_prefixes)
    logging.info(f"Parsed commits: {commits}")
    commits.sort(key=lambda x: x["date"])  # Sort by commit date
    status_table, detailed_table, unassigned_count, execution_time, total_retries = build_tables(commits, jira_base_url, jira_token, ignored_statuses, skipped_tickets)

    # Print tables
    print(f"\nAAMP Repo Checked In Ticket List From Last {days_from_today} Days\n")
    print("Order Of Verification:\n")
    print(detailed_table)
    print(status_table)

    # Print unassigned tickets
    print(f"\nUnassigned Tickets: {unassigned_count}")

    # Print execution stats
    execution_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nExecution Stats:\nExecution DateTime: {execution_datetime}\nTotal Execution Time: {execution_time:.2f} seconds\nTotal Retries: {total_retries}")

    # Send Slack message
    if slack_channel:
        header_message = f"\n`AAMP Repo Checked In Ticket List From Last {days_from_today} Days`\n"
        order_message = f"\n*Order Of Verification*\n"
        detailed_messages = split_table_message(detailed_table)
        status_message = f"```\n{status_table}\n```"
        unassigned_message = f"*Unassigned Tickets: {unassigned_count}*\n"
        execution_datetime_message = f"\nExecution DateTime: {execution_datetime}"
        messages = [header_message, order_message] + detailed_messages + [status_message, unassigned_message, execution_datetime_message]
        send_slack_messages(slack_url, slack_token, slack_channel, messages)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <config_file>")
        logging.error("Example: python jira_commit_table.py config.json")
        sys.exit(1)
    else:
        main(sys.argv[1])
