"""
System Prompt Management and Fingerprinting
Handles system prompt detection, fingerprinting, and removal for conversation monitoring
"""

import hashlib
import json
import re
import logging
import boto3
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SystemPromptFingerprint:
    """System prompt fingerprint for identification and deduplication"""
    prompt_hash: str
    prompt_id: str
    agent_type: str
    version: str
    first_seen: str
    size_bytes: int
    usage_count: int
    patterns_matched: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SystemPromptStripper:
    """Advanced system prompt detection and removal engine"""
    
    def __init__(self, s3_bucket: Optional[str] = None):
        self.s3_client = boto3.client('s3') if s3_bucket else None
        self.s3_bucket = s3_bucket
        self.fingerprint_db: Dict[str, SystemPromptFingerprint] = {}
        self.load_known_fingerprints()
        
        # Enhanced detection patterns for different agent types
        self.agent_patterns = {
            'data_agent': [
                "# Data Analysis Agent Instructions",
                "You are the Data Analysis Agent for Firebolt",
                "You are a specialized Data Analysis Agent",
                "## Agent Purpose",
                "## Core Capabilities", 
                "## CRITICAL: Temporal Context Awareness",
                "**ALWAYS REMEMBER THE CURRENT DATE AND TIME CONTEXT**",
                "## Business Context and Customer Segmentation",
                "### Customer Type Classification in SQL",
                "**CRITICAL**: Always segment analysis by customer type",
                "### Required Analysis Patterns",
                "### SQL Query Patterns for Temporal Analysis",
                "### Customer Lifecycle Analysis",
                "## Best Practices",
                "## Function Calling",
                "### Firebolt SQL Query",
                "### Gong Data Analysis",
                "### Regional Analysis", 
                "### Lead Analysis",
                "### Owner and User Name Resolution",
                "## Temporal Analysis Guidelines"
            ],
            'deal_analysis_agent': [
                "# Deal Analysis Agent Instructions",
                "You are the Deal Analysis Agent",
                "## Deal Analysis Framework",
                "### MEDDPICC Analysis",
                "### Deal Qualification",
                "### Competitive Analysis",
                "## Deal Stages",
                "### Pipeline Analysis"
            ],
            'lead_analysis_agent': [
                "# Lead Analysis Agent Instructions", 
                "You are the Lead Analysis Agent",
                "## Lead Qualification Framework",
                "### Lead Scoring",
                "### Disqualification Reasons",
                "## Lead Processing"
            ],
            'manager_agent': [
                "# Manager Agent Instructions",
                "You are the Manager Agent",
                "## Agent Coordination",
                "### Agent Selection",
                "### Workflow Management",
                "## Collaboration Framework"
            ],
            'execution_agent': [
                "# Execution Agent Instructions",
                "You are the Execution Agent", 
                "## Action Execution",
                "### Webhook Management",
                "### External Integration"
            ]
        }
        
        # Generic system prompt patterns
        self.generic_patterns = [
            r"You are an? (?:AI|artificial intelligence) (?:assistant|agent)",
            r"Your role is to",
            r"System instruction",
            r"Prompt template", 
            r"Follow these instructions",
            r"You must always",
            r"Never reveal that you are",
            r"Do not mention that you are an AI",
            r"Instructions:\s*\n",
            r"Guidelines:\s*\n",
            r"Constraints:\s*\n",
            r"You should always",
            r"Remember to",
            r"Important notes",
            r"CRITICAL.*:",
            r"ALWAYS.*:",
            r"NEVER.*:"
        ]
        
        # Size-based detection thresholds
        self.size_thresholds = {
            'tiny': 1000,      # 1KB - likely not system prompt
            'small': 5000,     # 5KB - possible system prompt with multiple patterns
            'medium': 15000,   # 15KB - likely system prompt with fewer patterns
            'large': 25000,    # 25KB - almost certainly system prompt
            'massive': 40000   # 40KB+ - definitely system prompt
        }
    
    def load_known_fingerprints(self):
        """Load known system prompt fingerprints from S3 or local cache"""
        try:
            if self.s3_client and self.s3_bucket:
                # Try to load from S3
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.s3_bucket,
                        Key='system-prompts/fingerprint-db.json'
                    )
                    fingerprints_data = json.loads(response['Body'].read().decode('utf-8'))
                    
                    for fp_data in fingerprints_data:
                        fp = SystemPromptFingerprint(**fp_data)
                        self.fingerprint_db[fp.prompt_hash] = fp
                        
                    logger.info(f"Loaded {len(self.fingerprint_db)} system prompt fingerprints from S3")
                    
                except self.s3_client.exceptions.NoSuchKey:
                    logger.info("No existing fingerprint database found in S3, starting fresh")
                except Exception as e:
                    logger.warning(f"Failed to load fingerprints from S3: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading fingerprints: {e}")
    
    def save_fingerprints(self):
        """Save fingerprint database to S3"""
        try:
            if self.s3_client and self.s3_bucket:
                fingerprints_data = [fp.to_dict() for fp in self.fingerprint_db.values()]
                
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key='system-prompts/fingerprint-db.json',
                    Body=json.dumps(fingerprints_data, indent=2),
                    ContentType='application/json'
                )
                
                logger.info(f"Saved {len(self.fingerprint_db)} fingerprints to S3")
                
        except Exception as e:
            logger.error(f"Error saving fingerprints: {e}")
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for fingerprinting"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def detect_system_prompt(self, content: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive system prompt detection using multiple methods
        Returns (is_system_prompt, detection_details)
        """
        if not content or len(content) < 100:
            return False, {"reason": "too_short", "size": len(content)}
        
        detection_details = {
            "size_bytes": len(content),
            "patterns_matched": [],
            "agent_type_detected": None,
            "confidence_score": 0.0,
            "detection_methods": []
        }
        
        # Method 1: Known fingerprint check
        content_hash = self.calculate_content_hash(content)
        if content_hash in self.fingerprint_db:
            fp = self.fingerprint_db[content_hash]
            fp.usage_count += 1  # Increment usage counter
            detection_details.update({
                "detection_methods": ["fingerprint_match"],
                "confidence_score": 1.0,
                "agent_type_detected": fp.agent_type,
                "prompt_id": fp.prompt_id
            })
            return True, detection_details
        
        # Method 2: Agent-specific pattern matching
        for agent_type, patterns in self.agent_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern in content:
                    matches.append(pattern)
                    detection_details["patterns_matched"].append(pattern)
            
            if matches:
                pattern_ratio = len(matches) / len(patterns)
                confidence_boost = pattern_ratio * 0.6
                detection_details["confidence_score"] += confidence_boost
                
                if pattern_ratio >= 0.3:  # 30% of agent patterns matched
                    detection_details["agent_type_detected"] = agent_type
                    detection_details["detection_methods"].append("agent_pattern_match")
        
        # Method 3: Generic system prompt patterns
        generic_matches = 0
        for pattern in self.generic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                generic_matches += 1
                detection_details["patterns_matched"].append(f"generic:{pattern}")
        
        if generic_matches > 0:
            generic_confidence = min(generic_matches * 0.1, 0.4)  # Max 0.4 from generic patterns
            detection_details["confidence_score"] += generic_confidence
            detection_details["detection_methods"].append("generic_pattern_match")
        
        # Method 4: Size-based detection with adaptive thresholds
        size = len(content)
        size_confidence = 0.0
        
        if size >= self.size_thresholds['massive']:
            size_confidence = 0.8
        elif size >= self.size_thresholds['large']:
            size_confidence = 0.6 if len(detection_details["patterns_matched"]) > 0 else 0.3
        elif size >= self.size_thresholds['medium']:
            size_confidence = 0.4 if len(detection_details["patterns_matched"]) > 1 else 0.1
        elif size >= self.size_thresholds['small']:
            size_confidence = 0.2 if len(detection_details["patterns_matched"]) > 2 else 0.0
        
        detection_details["confidence_score"] += size_confidence
        if size_confidence > 0:
            detection_details["detection_methods"].append("size_based")
        
        # Method 5: Content structure analysis
        structure_indicators = [
            "## " in content,  # Multiple headers
            "### " in content,  # Sub-headers
            "**" in content and content.count("**") > 4,  # Bold formatting
            "CRITICAL" in content.upper(),
            "ALWAYS" in content.upper(), 
            "NEVER" in content.upper(),
            content.count('\n') > 50,  # Many lines
            "You are" in content[:200]  # Role definition at start
        ]
        
        structure_score = sum(structure_indicators) / len(structure_indicators)
        if structure_score > 0.4:
            detection_details["confidence_score"] += structure_score * 0.3
            detection_details["detection_methods"].append("structure_analysis")
        
        # Final decision
        is_system_prompt = detection_details["confidence_score"] >= 0.7
        
        # If detected and not in fingerprint DB, add it
        if is_system_prompt and content_hash not in self.fingerprint_db:
            self.add_to_fingerprint_db(content, content_hash, detection_details)
        
        return is_system_prompt, detection_details
    
    def add_to_fingerprint_db(self, content: str, content_hash: str, detection_details: Dict[str, Any]):
        """Add new system prompt to fingerprint database"""
        try:
            fingerprint = SystemPromptFingerprint(
                prompt_hash=content_hash,
                prompt_id=f"sp_{content_hash[:12]}_{datetime.utcnow().strftime('%Y%m%d')}",
                agent_type=detection_details.get("agent_type_detected", "unknown"),
                version="1.0",
                first_seen=datetime.utcnow().isoformat(),
                size_bytes=len(content),
                usage_count=1,
                patterns_matched=detection_details.get("patterns_matched", [])
            )
            
            self.fingerprint_db[content_hash] = fingerprint
            
            # Save the actual prompt content to S3 for reference
            if self.s3_client and self.s3_bucket:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=f'system-prompts/prompts/{fingerprint.prompt_id}.txt',
                    Body=content.encode('utf-8'),
                    ContentType='text/plain',
                    Metadata={
                        'agent-type': fingerprint.agent_type,
                        'size-bytes': str(fingerprint.size_bytes),
                        'confidence-score': str(detection_details.get("confidence_score", 0.0))
                    }
                )
            
            logger.info(f"Added new system prompt fingerprint: {fingerprint.prompt_id}")
            
        except Exception as e:
            logger.error(f"Error adding fingerprint: {e}")
    
    def strip_system_prompts_from_trace_content(self, trace_content: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Strip system prompts from Bedrock trace content
        Returns (cleaned_trace, removed_prompt_ids)
        """
        if not trace_content:
            return trace_content, []
        
        cleaned_trace = {}
        removed_prompt_ids = []
        
        for key, value in trace_content.items():
            if key == "modelInvocationInput" and isinstance(value, str):
                # Check if this is a system prompt
                is_system_prompt, details = self.detect_system_prompt(value)
                
                if is_system_prompt:
                    # Replace with reference
                    prompt_id = details.get("prompt_id", f"sp_{self.calculate_content_hash(value)[:12]}")
                    removed_prompt_ids.append(prompt_id)
                    
                    cleaned_trace[key] = json.dumps({
                        "system_prompt_removed": True,
                        "prompt_id": prompt_id,
                        "original_size_bytes": len(value),
                        "agent_type": details.get("agent_type_detected", "unknown"),
                        "confidence_score": details.get("confidence_score", 0.0)
                    })
                    
                    logger.info(f"Stripped system prompt {prompt_id} (size: {len(value)} bytes)")
                else:
                    cleaned_trace[key] = value
            
            elif key == "messages" and isinstance(value, list):
                # Process messages array
                cleaned_messages = []
                for msg in value:
                    if isinstance(msg, dict) and "content" in msg:
                        content = str(msg["content"])
                        is_system_prompt, details = self.detect_system_prompt(content)
                        
                        if is_system_prompt:
                            prompt_id = details.get("prompt_id", f"sp_{self.calculate_content_hash(content)[:12]}")
                            removed_prompt_ids.append(prompt_id)
                            
                            # Replace message with reference
                            cleaned_msg = {
                                **msg,
                                "content": f"[SYSTEM_PROMPT_REFERENCE:{prompt_id}]",
                                "original_size": len(content),
                                "system_prompt_detected": True
                            }
                            cleaned_messages.append(cleaned_msg)
                        else:
                            cleaned_messages.append(msg)
                    else:
                        cleaned_messages.append(msg)
                
                cleaned_trace[key] = cleaned_messages
            
            else:
                cleaned_trace[key] = value
        
        return cleaned_trace, removed_prompt_ids
    
    def preprocess_conversation_data(self, conversation_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Pre-process conversation data to strip system prompts before storage
        Returns (cleaned_data, stripping_stats)
        """
        if not conversation_data:
            return conversation_data, {}
        
        stripping_stats = {
            "total_prompts_removed": 0,
            "total_bytes_saved": 0,
            "agent_steps_processed": 0,
            "prompt_references": {},
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        # Process conversation structure
        if "conversation" in conversation_data:
            conversation = conversation_data["conversation"]
            
            # Process agent flow
            if "agent_flow" in conversation and isinstance(conversation["agent_flow"], list):
                cleaned_agent_flow = []
                
                for i, step in enumerate(conversation["agent_flow"]):
                    if isinstance(step, dict):
                        cleaned_step = {}
                        step_removed_prompts = []
                        
                        for key, value in step.items():
                            if key == "bedrock_trace_content" and value:
                                cleaned_trace, removed_ids = self.strip_system_prompts_from_trace_content(value)
                                cleaned_step[key] = cleaned_trace
                                step_removed_prompts.extend(removed_ids)
                                
                            elif key == "reasoning_text" and isinstance(value, str):
                                # Check reasoning text for system prompts
                                is_system_prompt, details = self.detect_system_prompt(value)
                                
                                if is_system_prompt:
                                    prompt_id = details.get("prompt_id", f"sp_reasoning_{i}")
                                    step_removed_prompts.append(prompt_id)
                                    
                                    cleaned_step[key] = f"[SYSTEM_PROMPT_REFERENCE:{prompt_id}]"
                                    stripping_stats["total_bytes_saved"] += len(value)
                                else:
                                    cleaned_step[key] = value
                            else:
                                cleaned_step[key] = value
                        
                        # Add prompt reference metadata if any prompts were removed
                        if step_removed_prompts:
                            cleaned_step["system_prompts_removed"] = step_removed_prompts
                            stripping_stats["prompt_references"][f"step_{i}"] = step_removed_prompts
                            stripping_stats["total_prompts_removed"] += len(step_removed_prompts)
                        
                        cleaned_agent_flow.append(cleaned_step)
                        stripping_stats["agent_steps_processed"] += 1
                    else:
                        cleaned_agent_flow.append(step)
                
                conversation["agent_flow"] = cleaned_agent_flow
        
        # Add stripping metadata to export metadata
        if "export_metadata" not in conversation_data:
            conversation_data["export_metadata"] = {}
        
        conversation_data["export_metadata"]["system_prompt_stripping"] = stripping_stats
        conversation_data["export_metadata"]["system_prompts_excluded"] = True
        conversation_data["export_metadata"]["preprocessing_applied"] = True
        
        # Save updated fingerprints periodically
        if stripping_stats["total_prompts_removed"] > 0:
            self.save_fingerprints()
        
        logger.info(f"System prompt preprocessing complete: {stripping_stats['total_prompts_removed']} prompts removed, {stripping_stats['total_bytes_saved']} bytes saved")
        
        return conversation_data, stripping_stats
    
    def get_prompt_content_by_id(self, prompt_id: str) -> Optional[str]:
        """Retrieve system prompt content by ID for debugging"""
        try:
            if self.s3_client and self.s3_bucket:
                response = self.s3_client.get_object(
                    Bucket=self.s3_bucket,
                    Key=f'system-prompts/prompts/{prompt_id}.txt'
                )
                return response['Body'].read().decode('utf-8')
        except:
            pass
        
        # Check fingerprint database for hash reference
        for fp in self.fingerprint_db.values():
            if fp.prompt_id == prompt_id:
                return f"[FINGERPRINT_REFERENCE: {fp.prompt_hash}]"
        
        return None
    
    def get_stripping_statistics(self) -> Dict[str, Any]:
        """Get overall system prompt stripping statistics"""
        total_prompts = len(self.fingerprint_db)
        total_usage = sum(fp.usage_count for fp in self.fingerprint_db.values())
        
        agent_type_breakdown = {}
        for fp in self.fingerprint_db.values():
            agent_type = fp.agent_type
            if agent_type not in agent_type_breakdown:
                agent_type_breakdown[agent_type] = {"count": 0, "total_size": 0, "usage": 0}
            
            agent_type_breakdown[agent_type]["count"] += 1
            agent_type_breakdown[agent_type]["total_size"] += fp.size_bytes
            agent_type_breakdown[agent_type]["usage"] += fp.usage_count
        
        return {
            "total_unique_prompts": total_prompts,
            "total_usage_count": total_usage,
            "agent_type_breakdown": agent_type_breakdown,
            "average_prompt_size": sum(fp.size_bytes for fp in self.fingerprint_db.values()) / max(total_prompts, 1),
            "database_last_updated": datetime.utcnow().isoformat()
        }