# AWS Tools

This directory contains scripts and utilities for AWS operations related to the RevOps AI Framework.

## Directory Structure

- **s3/**: Scripts for S3 bucket operations
- **lambda/**: Lambda function utilities
- **common/**: Shared utilities and helper functions

## Setup

### Virtual Environment

AWS tools require a Python virtual environment with necessary dependencies. To set up:

```bash
# From the project root directory
# 1. Create virtual environment (if not already done)
python3 -m venv aws_tools_env

# 2. Activate virtual environment (fish shell)
source aws_tools_env/bin/activate.fish

# 3. Install dependencies
pip install boto3
```

### AWS Credentials

1. Copy the template credentials file:
   ```bash
   cp aws_tools/credentials.template.ini aws_tools/credentials.ini
   ```

2. Edit `aws_tools/credentials.ini` and add your AWS credentials:
   ```ini
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY_HERE
   aws_secret_access_key = YOUR_SECRET_KEY_HERE
   region_name = us-west-2
   ```

## Usage

Each script should have detailed documentation within its file. Always run scripts from the project root directory with the virtual environment active.

```bash
# Activate the virtual environment
source aws_tools_env/bin/activate.fish

# Run a script (e.g., to upload schema_knowledge.md to S3)
python aws_tools/s3/upload_to_s3.py
```

### Command-line Arguments

Scripts support command-line arguments for flexibility:

```bash
# Example: Upload a specific file to a specific S3 location
python aws_tools/s3/upload_to_s3.py --file /path/to/file.txt --bucket my-bucket --key path/in/bucket/file.txt
```

## Available Scripts

- **s3/upload_to_s3.py**: Upload files to specified S3 bucket paths
  - Default: Uploads schema_knowledge.md to s3://revops-s3-bucket/revops-ai-framework/schema-information/
  - Arguments:
    - `--file` or `-f`: Local file path to upload
    - `--bucket` or `-b`: S3 bucket name
    - `--key` or `-k`: S3 object key (path in S3)
