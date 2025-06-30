#!/usr/bin/env python3
"""
Deployment Validation Script for RevOps AI Framework

This script validates deployment configuration to catch common issues before deploying:
1. Checks for required environment variables across Lambda functions
2. Verifies the existence of requirements.txt files for each Lambda function
3. Validates that all required dependencies are included
4. Ensures paths in configuration files are correct

Usage: 
    python validate_deployment.py

"""

import os
import json
import sys
from pathlib import Path

# Constants
REQUIRED_ENV_VARS = {
    "firebolt_query": ["FIREBOLT_ACCOUNT_NAME", "FIREBOLT_ACCOUNT", "FIREBOLT_ENGINE", "FIREBOLT_DATABASE"],
    "firebolt_metadata": ["FIREBOLT_ACCOUNT", "FIREBOLT_ENGINE", "FIREBOLT_DATABASE"],
    "firebolt_writer": ["FIREBOLT_ACCOUNT", "FIREBOLT_ENGINE", "FIREBOLT_DATABASE"],
    "gong_retrieval": []  # Add required env vars for Gong if needed
}

REQUIRED_DEPENDENCIES = {
    "firebolt_metadata": ["requests"],
    "webhook": ["requests"],
    "gong_retrieval": []  # Add required dependencies for Gong if needed
}

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class DeploymentValidator:
    """Validates deployment configuration to prevent common issues."""

    def __init__(self, base_dir=None):
        """Initialize the validator with the project base directory."""
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default to the repository root (2 directories up from this script)
            self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.deployment_dir = self.base_dir / "deployment"
        self.config_path = self.deployment_dir / "config.json"
        self.secrets_path = self.deployment_dir / "secrets.json"
        
        self.issues = []
        self.warnings = []
        
    def load_config(self):
        """Load the configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValidationError(f"Failed to load config.json: {str(e)}")
    
    def load_secrets(self):
        """Load the secrets file if it exists."""
        try:
            with open(self.secrets_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.warnings.append(f"Failed to load secrets.json: {str(e)}")
            return {}

    def validate_environment_variables(self, config):
        """Check that all required environment variables are present in Lambda configs."""
        lambda_functions = config.get("lambda_functions", {})
        
        for lambda_name, required_vars in REQUIRED_ENV_VARS.items():
            if lambda_name not in lambda_functions:
                self.warnings.append(f"Lambda function '{lambda_name}' not found in config")
                continue
                
            lambda_config = lambda_functions[lambda_name]
            env_vars = lambda_config.get("environment_variables", {})
            
            for var in required_vars:
                if var not in env_vars:
                    self.issues.append(f"Missing environment variable '{var}' for Lambda '{lambda_name}'")
    
    def validate_dependencies(self, config):
        """Check that all Lambda functions have the required dependencies."""
        lambda_functions = config.get("lambda_functions", {})
        
        for lambda_name, required_deps in REQUIRED_DEPENDENCIES.items():
            if lambda_name not in lambda_functions:
                self.warnings.append(f"Lambda function '{lambda_name}' not found in config")
                continue
                
            lambda_config = lambda_functions[lambda_name]
            source_dir = lambda_config.get("source_dir", "")
            
            if not source_dir:
                self.issues.append(f"No source directory specified for Lambda '{lambda_name}'")
                continue
                
            # Convert relative path to absolute if needed
            if not os.path.isabs(source_dir):
                source_dir = self.base_dir / source_dir
                
            # Check if the directory exists
            if not os.path.isdir(source_dir):
                self.issues.append(f"Source directory '{source_dir}' for Lambda '{lambda_name}' does not exist")
                continue
                
            # Check for requirements.txt
            req_file = os.path.join(source_dir, "requirements.txt")
            if not os.path.exists(req_file):
                if required_deps:
                    self.issues.append(f"requirements.txt missing for Lambda '{lambda_name}' which needs dependencies: {required_deps}")
                    # Create a requirements file with required dependencies
                    self.create_requirements_file(source_dir, required_deps)
                continue
                
            # Check if required dependencies are in requirements.txt
            with open(req_file, 'r') as f:
                content = f.read()
                for dep in required_deps:
                    if not any(line.strip().startswith(dep) for line in content.splitlines()):
                        self.issues.append(f"Dependency '{dep}' missing from requirements.txt for Lambda '{lambda_name}'")
                        # Update the requirements file
                        self.update_requirements_file(req_file, dep)
    
    def create_requirements_file(self, dir_path, dependencies):
        """Create a requirements.txt file with the specified dependencies."""
        req_path = os.path.join(dir_path, "requirements.txt")
        try:
            with open(req_path, 'w') as f:
                for dep in dependencies:
                    if dep == "requests":
                        f.write("requests==2.31.0\n")
                    else:
                        f.write(f"{dep}\n")
            self.warnings.append(f"Created requirements.txt in {dir_path} with dependencies: {dependencies}")
        except Exception as e:
            self.warnings.append(f"Failed to create requirements.txt in {dir_path}: {str(e)}")
    
    def update_requirements_file(self, req_path, dependency):
        """Add a dependency to an existing requirements.txt file."""
        try:
            with open(req_path, 'a') as f:
                if dependency == "requests":
                    f.write("requests==2.31.0\n")
                else:
                    f.write(f"{dependency}\n")
            self.warnings.append(f"Added {dependency} to {req_path}")
        except Exception as e:
            self.warnings.append(f"Failed to update {req_path}: {str(e)}")
    
    def validate_source_paths(self, config):
        """Check that all source paths in config are valid."""
        lambda_functions = config.get("lambda_functions", {})
        
        for lambda_name, lambda_config in lambda_functions.items():
            source_dir = lambda_config.get("source_dir", "")
            
            if not source_dir:
                self.issues.append(f"No source directory specified for Lambda '{lambda_name}'")
                continue
                
            # Convert relative path to absolute if needed
            abs_path = source_dir
            if not os.path.isabs(source_dir):
                abs_path = os.path.join(self.base_dir, source_dir)
                
            # Check if the directory exists
            if not os.path.isdir(abs_path):
                self.issues.append(f"Source directory '{abs_path}' for Lambda '{lambda_name}' does not exist")
    
    def validate_all(self):
        """Run all validation checks."""
        try:
            config = self.load_config()
            self.secrets = self.load_secrets()
            
            self.validate_environment_variables(config)
            self.validate_dependencies(config)
            self.validate_source_paths(config)
            
            # Print the results
            if self.issues:
                print("\n❌ VALIDATION ISSUES:")
                for issue in self.issues:
                    print(f"  - {issue}")
                    
            if self.warnings:
                print("\n⚠️ WARNINGS:")
                for warning in self.warnings:
                    print(f"  - {warning}")
                    
            if not self.issues and not self.warnings:
                print("\n✅ All validations passed! The deployment configuration looks good.")
                return True
            elif not self.issues:
                print("\n✅ No critical issues found. There are some warnings, but deployment can proceed.")
                return True
            else:
                print("\n❌ Please fix the issues before proceeding with deployment.")
                return False
                
        except ValidationError as e:
            print(f"\n❌ Validation failed: {str(e)}")
            return False

def patch_deploy_script():
    """Patch the deploy.py script to include validation before deployment."""
    deploy_path = Path(__file__).parent / "deploy.py"
    backup_path = Path(__file__).parent / "deploy.py.bak"
    
    # Check if deploy.py exists
    if not deploy_path.exists():
        print(f"Cannot find deploy.py at {deploy_path}")
        return False
    
    # Create a backup
    import shutil
    shutil.copy2(deploy_path, backup_path)
    print(f"Backed up deploy.py to {backup_path}")
    
    # Read the content
    with open(deploy_path, 'r') as f:
        content = f.read()
    
    # Check if validation is already included
    if "validate_deployment" in content:
        print("Validation already included in deploy.py")
        return True
    
    # Find the main function
    main_pattern = "def main():"
    if main_pattern not in content:
        print("Could not find main() function in deploy.py")
        return False
    
    # Add import at the top
    import_line = "import validate_deployment\n"
    if import_line not in content:
        content = import_line + content
    
    # Add validation call in main function
    validation_code = """
    # Validate deployment configuration
    validator = validate_deployment.DeploymentValidator()
    if not validator.validate_all():
        if input("Validation failed. Do you want to continue anyway? (y/N): ").lower() != 'y':
            print("Deployment canceled.")
            return
    
"""
    
    # Insert the validation code after the main function
    main_index = content.find(main_pattern) + len(main_pattern)
    # Find the first line after the function definition
    next_line_index = content.find("\n", main_index) + 1
    
    # Insert the validation code
    content = content[:next_line_index] + validation_code + content[next_line_index:]
    
    # Write the updated content
    with open(deploy_path, 'w') as f:
        f.write(content)
    
    print("Successfully patched deploy.py to include validation checks.")
    return True

def main():
    """Main function to validate deployment configuration."""
    print("=== RevOps AI Framework Deployment Validator ===")
    
    validator = DeploymentValidator()
    result = validator.validate_all()
    
    if result and input("\nWould you like to patch deploy.py to include these validation checks? (y/N): ").lower() == 'y':
        patch_deploy_script()
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
