# JIRA Commit Tracker

## Project Description
The JIRA Commit Tracker is a Python utility that automates the process of retrieving commit messages from a Git repository, querying JIRA issues based on the commits, and compiling the results into structured tables. These tables can be output to the console or sent as messages to a Slack channel. The tool helps teams track the status of work items related to recent commits, making it easier to review progress and ensure alignment with project goals.

## Features
- **Git Integration**: Pulls commit logs from a specified repository and branch.
- **JIRA Querying**: Extracts JIRA ticket details based on commit messages and queries their status, assignee, and summary.
- **Slack Notifications**: Sends detailed commit summaries and status updates to a specified Slack channel.
- **Customizable Configurations**: Fully configurable via a JSON file to suit various workflows.
- **Execution Statistics**: Provides insights into execution time and retries for JIRA queries.

---

## Installation Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shripadbpersonal/JIRA-Commit-Tracker.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd JIRA-Commit-Tracker
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

To run the script, use the following command:
```bash
python src/jira_commit_table.py config.json
```
Make sure to replace `config.json` with the path to your configuration file.

---

## Configuration
The configuration file (`config.json`) should include the following parameters:

### Required Parameters:
- **`jira_base_url`**: The base URL of your JIRA instance (e.g., `https://yourcompany.atlassian.net`).
- **`ticket_prefixes`**: A list of JIRA ticket prefixes to look for in commit messages (e.g., `["PROJ", "BUG"]`).
- **`days_from_today`**: The number of days to look back for Git commits (default: `30`).
- **`repo_url`**: The URL of the Git repository to clone (e.g., `https://github.com/yourusername/yourrepo.git`).
- **`branch`**: The branch to check out (e.g., `main`).
- **`directory`**: The local directory where the repository should be cloned (e.g., `repo_directory`).

### Optional Parameters:
- **`ignored_statuses`**: A list of JIRA statuses to ignore (e.g., `["Closed", "Done"]`).
- **`logging_enabled`**: Enable or disable logging (`true` or `false`).
- **`slack_url`**: The Slack API endpoint for sending messages (default: `https://slack.com/api/chat.postMessage`).
- **`slack_channel`**: The **ID** of the Slack channel to send messages to (not the channel name). You can retrieve the channel ID using the Slack API or the workspace settings.
- **`skipped_tickets`**: A list of JIRA tickets to exclude from the report.

### Required Environment Variables:
To execute the script, you must provide the following environment variables or use AWS SSM Parameter Store:
- **`JIRA_TOKEN`**: A personal access token for authenticating with the JIRA API.
- **`SLACK_TOKEN`**: A bot token for sending messages to Slack.

### Example `config.json`:
```json
{
    "jira_base_url": "https://yourcompany.atlassian.net",
    "ticket_prefixes": ["PROJ", "BUG"],
    "days_from_today": 30,
    "repo_url": "https://github.com/yourusername/yourrepo.git",
    "branch": "main",
    "directory": "repo_directory",
    "ignored_statuses": ["Closed", "Done"],
    "logging_enabled": true,
    "slack_url": "https://slack.com/api/chat.postMessage",
    "slack_channel": "C12345678",  // Slack channel ID
    "skipped_tickets": ["PROJ-123", "BUG-456"]
}
```

---

## Example Output Tables

### Console Output Example

#### Detailed Commit Table
```
+----+------------+------------------+---------+---------------------------------------------------------------+
| No | Commit Date| Assignee         | Status  | JIRA Ticket                                                   |
+----+------------+------------------+---------+---------------------------------------------------------------+
| 1  | 2025-01-20 | John Doe         | In Progress | ==> Fix playback issue
https://yourcompany.atlassian.net/browse/PROJ-789 |
| 2  | 2025-01-19 | Unassigned       | Open    | *Unknown*
https://yourcompany.atlassian.net/browse/BUG-101 |
+----+------------+------------------+---------+---------------------------------------------------------------+
```

#### Status Summary Table
```
+----------------+-------------------+
| Status         | Number of Tickets|
+----------------+-------------------+
| In Progress    | 5                |
| Open           | 3                |
| Done           | 2                |
+----------------+-------------------+
```

### Slack Message Example

#### Header
```
`AAMP Repo Checked-In Ticket List From Last 30 Days`
```

#### Order of Verification
```
*Order of Verification*
```

#### Detailed Table (Split Messages)
```
```
+----+------------+------------------+---------+---------------------------------------------------------------+
| No | Commit Date| Assignee         | Status  | JIRA Ticket                                                   |
+----+------------+------------------+---------+---------------------------------------------------------------+
| 1  | 2025-01-20 | John Doe         | In Progress | ==> Fix playback issue
https://yourcompany.atlassian.net/browse/PROJ-789 |
```
```

#### Status Table
```
```
+----------------+-------------------+
| Status         | Number of Tickets|
+----------------+-------------------+
| In Progress    | 5                |
| Open           | 3                |
| Done           | 2                |
+----------------+-------------------+
```
```

#### Unassigned Tickets
```
*Unassigned Tickets: 3*
```

#### Execution Stats
```
Execution DateTime: 2025-01-25 14:30:00
Total Execution Time: 12.34 seconds
Total Retries: 2
```

---

## Contribution Guidelines
Contributions are welcome! Follow these steps:

1. **Fork the repository.**
2. **Create a new branch** for your feature or bug fix.
3. **Commit your changes** and push them to your branch.
4. **Submit a pull request** for review.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Support
For any issues, feel free to open an issue on the [GitHub repository](https://github.com/shripadbpersonal/JIRA-Commit-Tracker).

