#!/usr/bin/env python3
"""
Update the config.json file to add the FIREBOLT_ACCOUNT_NAME environment variable
"""

import json
import os
import shutil

def update_config():
    config_path = 'config.json'
    backup_path = 'config.json.update_backup'
    
    # Create a backup
    shutil.copy2(config_path, backup_path)
    print(f"Created backup of config.json at {backup_path}")
    
    # Load the config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update the firebolt_query Lambda environment variables
    if 'lambda_functions' in config and 'firebolt_query' in config['lambda_functions']:
        env_vars = config['lambda_functions']['firebolt_query'].get('environment_variables', {})
        if 'FIREBOLT_ACCOUNT' in env_vars and 'FIREBOLT_ACCOUNT_NAME' not in env_vars:
            env_vars['FIREBOLT_ACCOUNT_NAME'] = env_vars['FIREBOLT_ACCOUNT']
            config['lambda_functions']['firebolt_query']['environment_variables'] = env_vars
            print(f"Added FIREBOLT_ACCOUNT_NAME={env_vars['FIREBOLT_ACCOUNT_NAME']} to firebolt_query Lambda")
    
    # Save the updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Config file updated successfully")

if __name__ == "__main__":
    update_config()
