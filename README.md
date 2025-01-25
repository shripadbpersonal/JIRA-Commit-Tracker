# JIRA Commit Tracker

## Project Description
JIRA Commit Tracker is a Python script that interacts with JIRA and Git to generate commit tables. It automates the process of retrieving commit messages from a Git repository, querying JIRA issues, and compiling the results into a structured format. This tool is useful for teams that want to track the status of their work items based on recent commits.

## Installation Instructions
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jira-commit-tracker.git
   ```
2. Navigate to the project directory:
   ```
   cd jira-commit-tracker
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the script, use the following command:
```
python src/jira_commit_table.py config.json
```
Make sure to replace `config.json` with the path to your configuration file.

## Configuration
The configuration file (`config.json`) should include the following parameters:
- `jira_base_url`: The base URL for your JIRA instance.
- `ticket_prefixes`: A list of ticket prefixes to look for in commit messages.
- `ignored_statuses`: A list of JIRA statuses to ignore.
- `logging_enabled`: A boolean to enable or disable logging.
- `slack_url`: The URL for sending messages to Slack.
- `slack_channel`: The Slack channel to send messages to.
- `repo_url`: The URL of the Git repository.
- `branch`: The branch to check out.
- `directory`: The directory to clone the repository into.
- `skipped_tickets`: A list of tickets to skip in the report.
- `days_from_today`: The number of days to look back for commits.

## Contribution Guidelines
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch and create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.