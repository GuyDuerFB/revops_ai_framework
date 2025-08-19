#!/usr/bin/env python3
"""
Agent Creation Script for RevOps AI Framework
Creates new agent directory structure with templated instructions
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from typing import Optional


class AgentCreator:
    """Creates new agent directory structure with templated instructions"""
    
    def __init__(self, agent_name: str, description: str = ""):
        self.agent_name = agent_name.strip()
        self.description = description.strip() if description else "A specialized agent for the RevOps AI Framework"
        self.sanitized_name = self._sanitize_name(agent_name)
        
        # Get repository root (assuming script is in .github/scripts/)
        self.repo_root = Path(__file__).parent.parent.parent
        self.agents_dir = self.repo_root / "agents"
        self.agent_dir = self.agents_dir / self.sanitized_name
        self.template_file = self.agents_dir / "generic_agent_instructions_template_bedrock_ai_framework.md"
        
    def _sanitize_name(self, name: str) -> str:
        """Sanitize agent name for directory naming conventions"""
        # Convert to lowercase
        sanitized = name.lower().strip()
        
        # Replace invalid characters with hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '-', sanitized)
        
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Strip leading/trailing hyphens
        sanitized = sanitized.strip('-')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed-agent"
            
        return sanitized
    
    def _validate_name(self) -> tuple[bool, Optional[str]]:
        """Validate the sanitized agent name"""
        if len(self.sanitized_name) < 3:
            return False, f"Agent name too short after sanitization: '{self.sanitized_name}' (minimum 3 characters)"
        
        if len(self.sanitized_name) > 50:
            return False, f"Agent name too long after sanitization: '{self.sanitized_name}' (maximum 50 characters)"
        
        # Check for reserved names
        reserved_names = {
            'manager-agent', 'deal-analysis-agent', 'lead-analysis-agent', 
            'data-agent', 'web-search-agent', 'execution-agent',
            'generic-agent-instructions-template-bedrock-ai-framework'
        }
        
        if self.sanitized_name in reserved_names:
            return False, f"Agent name '{self.sanitized_name}' is reserved"
        
        return True, None
    
    def _process_template(self, template_content: str) -> str:
        """Process the template file and replace placeholders"""
        processed = template_content
        
        # Create a formatted agent name for display
        display_name = self.agent_name.title().replace('-', ' ').replace('_', ' ')
        
        # Replace template placeholders with agent-specific values
        replacements = {
            '<AGENT_NAME>': display_name,
            '\\<AGENT\\_NAME>': display_name.replace(' ', ' '),  # Handle escaped version
            '<PRIMARY_OBJECTIVE>': f"[CUSTOMIZE: Primary objective for {display_name}]",
            '<KEY_EXPERTISE_A>': "[CUSTOMIZE: First area of expertise]",
            '<KEY_EXPERTISE_B>': "[CUSTOMIZE: Second area of expertise]", 
            '<KEY_EXPERTISE_C>': "[CUSTOMIZE: Third area of expertise]",
            '<TRIGGER_EVENTS>': f"[CUSTOMIZE: Events that trigger {display_name}]",
            '<INPUT_ARTIFACTS>': "[CUSTOMIZE: Input data/artifacts]",
            '<OUTPUT_ARTIFACTS>': "[CUSTOMIZE: Output data/artifacts]",
            '<QUALITY_CRITERIA>': "[CUSTOMIZE: Quality criteria for outputs]",
            '<DOMAIN_WORKFLOWS>': "[CUSTOMIZE: Relevant workflow files]",
            '<AGENT_DOMAIN>': display_name.split()[0] if display_name.split() else "Agent",
            '<SQL_OR_PSEUDOCODE_FOR_PRIMARY_RETRIEVAL>': "-- CUSTOMIZE: Primary data query",
            '<SQL_OR_PSEUDOCODE_FOR_SECONDARY_RETRIEVAL>': "-- CUSTOMIZE: Secondary data query",
            '<SECTION_TITLE_A>': "[CUSTOMIZE: First Output Section]",
            '<SECTION_TITLE_B>': "[CUSTOMIZE: Second Output Section]",
            '<SECTION_TITLE_C>': "[CUSTOMIZE: Third Output Section]",
            '<FIELD_1_LABEL>': "[CUSTOMIZE: Field 1]",
            '<FIELD_1_VALUE>': "[CUSTOMIZE: Field 1 Value]",
            '<FIELD_2_LABEL>': "[CUSTOMIZE: Field 2]",
            '<FIELD_2_VALUE>': "[CUSTOMIZE: Field 2 Value]",
            '<FIELD_3_LABEL>': "[CUSTOMIZE: Field 3]",
            '<FIELD_3_VALUE>': "[CUSTOMIZE: Field 3 Value]",
            '<SUBSECTION_1_LABEL>': "[CUSTOMIZE: Subsection 1]",
            '<SUBSECTION_2_LABEL>': "[CUSTOMIZE: Subsection 2]",
            '<DIMENSION_1>': "[CUSTOMIZE: Analysis Dimension 1]",
            '<DIMENSION_2>': "[CUSTOMIZE: Analysis Dimension 2]",
            '<DIMENSION_3>': "[CUSTOMIZE: Analysis Dimension 3]",
            '<DIMENSION_N>': "[CUSTOMIZE: Analysis Dimension N]",
            '<SCOPE_ENTITY>': "[CUSTOMIZE: Scope Entity Type]"
        }
        
        for placeholder, replacement in replacements.items():
            processed = processed.replace(placeholder, replacement)
        
        # Add customization note at the top
        customization_note = f"""# {display_name} Instructions — RevOps AI Framework

> **🔧 CUSTOMIZATION REQUIRED**
> 
> This file was generated from the agent template for agent: **{display_name}**
> Created: {self._get_current_timestamp()}
> Description: {self.description}
> 
> **TODO: Replace all [CUSTOMIZE: ...] placeholders with actual agent-specific content**
> **TODO: Define the exact output format in the "Required Output Format" section**
> **TODO: Specify the data sources and queries for your agent's domain**

---

"""
        
        # Remove the template usage instructions from the top
        lines = processed.split('\n')
        filtered_lines = []
        skip_until_separator = False
        found_separator = False
        
        for line in lines:
            if line.strip().startswith('> **How to Use This Template**'):
                skip_until_separator = True
                continue
            elif skip_until_separator and line.strip() == '---':
                found_separator = True
                continue
            elif skip_until_separator and not found_separator:
                continue
            else:
                filtered_lines.append(line)
        
        processed = '\n'.join(filtered_lines)
        
        # Add the customization note at the beginning
        processed = customization_note + processed
        
        return processed
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in readable format"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def create_agent_structure(self) -> bool:
        """Create the agent directory structure and instructions file"""
        try:
            print(f"🤖 Creating agent: {self.agent_name}")
            print(f"📁 Sanitized directory name: {self.sanitized_name}")
            print(f"📝 Description: {self.description}")
            
            # Validate inputs
            is_valid, error_msg = self._validate_name()
            if not is_valid:
                print(f"❌ {error_msg}")
                return False
            
            # Check if directory already exists
            if self.agent_dir.exists():
                print(f"❌ Agent directory already exists: {self.agent_dir}")
                print("   Please choose a different name or remove the existing directory")
                return False
            
            # Check if template file exists
            if not self.template_file.exists():
                print(f"❌ Template file not found: {self.template_file}")
                return False
            
            # Read template file
            print(f"📖 Reading template from: {self.template_file}")
            try:
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            except Exception as e:
                print(f"❌ Error reading template file: {e}")
                return False
            
            # Create directory
            print(f"📁 Creating directory: {self.agent_dir}")
            self.agent_dir.mkdir(parents=True, exist_ok=False)
            
            # Process template and create instructions file
            instructions_file = self.agent_dir / "instructions.md"
            print(f"📝 Processing template and creating: {instructions_file}")
            
            processed_content = self._process_template(template_content)
            
            with open(instructions_file, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            print(f"✅ Successfully created agent structure")
            print(f"   Directory: {self.agent_dir}")
            print(f"   Instructions: {instructions_file}")
            
            # Provide next steps
            print(f"\n🔧 Next Steps:")
            print(f"   1. Edit {instructions_file}")
            print(f"   2. Replace all [CUSTOMIZE: ...] placeholders")
            print(f"   3. Define the exact output format")
            print(f"   4. Test the instructions")
            print(f"   5. Use the 'Deploy Agent' workflow to deploy to AWS")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating agent structure: {e}")
            # Cleanup on failure
            if self.agent_dir.exists():
                try:
                    shutil.rmtree(self.agent_dir)
                    print(f"🧹 Cleaned up partially created directory")
                except:
                    pass
            return False


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Create new agent directory structure for RevOps AI Framework'
    )
    parser.add_argument(
        '--agent-name',
        required=True,
        help='Name of the new agent'
    )
    parser.add_argument(
        '--description',
        default='',
        help='Brief description of the agent purpose'
    )
    
    args = parser.parse_args()
    
    try:
        creator = AgentCreator(args.agent_name, args.description)
        success = creator.create_agent_structure()
        
        if success:
            print(f"\n🎉 Agent creation completed successfully!")
            # Set GitHub Actions output if running in GitHub Actions
            if os.getenv('GITHUB_ACTIONS'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f"agent-name={creator.sanitized_name}\n")
                    f.write(f"agent-dir=agents/{creator.sanitized_name}\n")
            sys.exit(0)
        else:
            print(f"\n❌ Agent creation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Agent creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
