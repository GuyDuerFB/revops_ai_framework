"""
Conversation Quality Analyzer
Comprehensive analysis of conversation effectiveness and quality metrics
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import re

logger = logging.getLogger(__name__)

class ConversationOutcome(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"  
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    INCOMPLETE = "incomplete"

class UserSatisfactionLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

@dataclass
class QualityMetrics:
    """Comprehensive conversation quality metrics"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    timeliness_score: float
    relevance_score: float
    user_satisfaction_score: float
    technical_quality_score: float
    business_impact_score: float

@dataclass
class ConversationOutcomeAnalysis:
    """Analysis of conversation outcome and effectiveness"""
    outcome: ConversationOutcome
    confidence: float
    success_indicators: List[str]
    failure_indicators: List[str]
    user_satisfaction: UserSatisfactionLevel
    business_value_delivered: bool
    follow_up_needed: bool
    improvement_suggestions: List[str]

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents"""
    agent_name: str
    effectiveness_score: float
    response_time_ms: int
    tool_success_rate: float
    handoff_quality: float
    collaboration_score: float
    error_rate: float
    business_contribution: float

@dataclass
class ConversationAnalysisResult:
    """Complete conversation analysis result"""
    conversation_id: str
    analysis_timestamp: str
    quality_metrics: QualityMetrics
    outcome_analysis: ConversationOutcomeAnalysis
    agent_performance: List[AgentPerformanceMetrics]
    system_performance: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any]

class ConversationQualityAnalyzer:
    """Analyzes conversation quality and effectiveness"""
    
    def __init__(self):
        # Success indicators
        self.success_indicators = [
            r'analysis complete',
            r'here.*results?',
            r'based on.*data',
            r'according to.*analysis',
            r'findings? show',
            r'recommendations?',
            r'summary:',
            r'key insights?',
            r'successfully',
            r'completed',
            r'delivered',
            r'\d+%',  # Specific percentages
            r'\$[\d,]+',  # Dollar amounts
            r'compared to',
            r'improvement',
            r'growth',
            r'performance'
        ]
        
        # Failure indicators
        self.failure_indicators = [
            r'error',
            r'failed',
            r'unable to',
            r'couldn\'t',
            r'not available',
            r'not found',
            r'timeout',
            r'something went wrong',
            r'try again',
            r'incomplete',
            r'partial.*results?',
            r'limited.*data',
            r'insufficient',
            r'unclear',
            r'i don\'t know',
            r'no data'
        ]
        
        # User satisfaction indicators
        self.satisfaction_indicators = {
            'high': [
                r'thank you',
                r'thanks',
                r'perfect',
                r'excellent',
                r'great',
                r'helpful',
                r'exactly what i needed',
                r'this is useful',
                r'very good'
            ],
            'medium': [
                r'ok',
                r'okay',
                r'good',
                r'fine',
                r'alright',
                r'that works'
            ],
            'low': [
                r'not what i wanted',
                r'this doesn\'t help',
                r'wrong',
                r'incorrect',
                r'not useful',
                r'disappointing',
                r'confused',
                r'still need help'
            ]
        }
        
        # Business value indicators
        self.business_value_patterns = [
            r'revenue',
            r'cost.*sav',
            r'efficiency',
            r'conversion.*rate',
            r'customer.*satisfaction',
            r'retention',
            r'churn',
            r'pipeline',
            r'forecast',
            r'roi',
            r'growth',
            r'market.*share',
            r'competitive.*advantage',
            r'optimization',
            r'performance.*improvement'
        ]
        
        # Quality thresholds
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        }
    
    def analyze_conversation_quality(self, conversation_data: Dict[str, Any]) -> ConversationAnalysisResult:
        """Perform comprehensive conversation quality analysis"""
        
        conversation = conversation_data.get('conversation', {})
        conversation_id = conversation.get('conversation_id', 'unknown')
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(conversation_data)
        
        # Analyze conversation outcome
        outcome_analysis = self._analyze_conversation_outcome(conversation_data)
        
        # Analyze agent performance
        agent_performance = self._analyze_agent_performance(conversation_data)
        
        # Calculate system performance metrics
        system_performance = self._calculate_system_performance(conversation_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(quality_metrics, outcome_analysis, agent_performance)
        
        # Create metadata
        metadata = self._create_analysis_metadata(conversation_data, quality_metrics)
        
        return ConversationAnalysisResult(
            conversation_id=conversation_id,
            analysis_timestamp=datetime.utcnow().isoformat(),
            quality_metrics=quality_metrics,
            outcome_analysis=outcome_analysis,
            agent_performance=agent_performance,
            system_performance=system_performance,
            recommendations=recommendations,
            metadata=metadata
        )
    
    def _calculate_quality_metrics(self, conversation_data: Dict[str, Any]) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Completeness score
        completeness_score = self._calculate_completeness_score(conversation)
        
        # Accuracy score
        accuracy_score = self._calculate_accuracy_score(conversation)
        
        # Timeliness score
        timeliness_score = self._calculate_timeliness_score(conversation)
        
        # Relevance score
        relevance_score = self._calculate_relevance_score(conversation)
        
        # User satisfaction score
        user_satisfaction_score = self._calculate_user_satisfaction_score(conversation)
        
        # Technical quality score
        technical_quality_score = self._calculate_technical_quality_score(conversation)
        
        # Business impact score
        business_impact_score = self._calculate_business_impact_score(conversation)
        
        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.2 +
            accuracy_score * 0.2 +
            timeliness_score * 0.15 +
            relevance_score * 0.15 +
            user_satisfaction_score * 0.1 +
            technical_quality_score * 0.1 +
            business_impact_score * 0.1
        )
        
        return QualityMetrics(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            timeliness_score=timeliness_score,
            relevance_score=relevance_score,
            user_satisfaction_score=user_satisfaction_score,
            technical_quality_score=technical_quality_score,
            business_impact_score=business_impact_score
        )
    
    def _calculate_completeness_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate how complete the conversation response is"""
        
        score = 0.5  # Base score
        
        # Check if user query was addressed
        user_query = conversation.get('user_query', '')
        final_response = conversation.get('final_response', '')
        
        if user_query and final_response:
            # Basic query addressing check
            query_words = set(re.findall(r'\w+', user_query.lower()))
            response_words = set(re.findall(r'\w+', final_response.lower()))
            
            if query_words:
                word_overlap = len(query_words.intersection(response_words)) / len(query_words)
                score += word_overlap * 0.3
        
        # Check response length (comprehensive responses score higher)
        if final_response:
            if len(final_response) > 500:
                score += 0.2
            elif len(final_response) > 200:
                score += 0.1
            elif len(final_response) < 50:
                score -= 0.2
        
        # Check if conversation reached natural conclusion
        if conversation.get('success', False):
            score += 0.2
        
        # Check for success indicators in response
        success_matches = sum(1 for pattern in self.success_indicators 
                             if re.search(pattern, final_response.lower()))
        if success_matches > 0:
            score += min(success_matches * 0.05, 0.2)
        
        # Penalize for failure indicators
        failure_matches = sum(1 for pattern in self.failure_indicators 
                             if re.search(pattern, final_response.lower()))
        if failure_matches > 0:
            score -= min(failure_matches * 0.1, 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_accuracy_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate accuracy of the conversation response"""
        
        score = 0.7  # Assume good accuracy unless indicators suggest otherwise
        
        # Check tool execution success rates
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            successful_tools = 0
            total_tools = 0
            
            for step in agent_flow:
                tools_used = step.get('tools_used', [])
                for tool in tools_used:
                    total_tools += 1
                    if isinstance(tool, dict) and tool.get('success', True):
                        successful_tools += 1
                    elif hasattr(tool, 'success') and getattr(tool, 'success', True):
                        successful_tools += 1
            
            if total_tools > 0:
                tool_success_rate = successful_tools / total_tools
                score = score * 0.7 + tool_success_rate * 0.3
        
        # Check for data quality indicators
        final_response = conversation.get('final_response', '')
        if final_response:
            # Presence of specific data points suggests accuracy
            data_indicators = [
                r'\d+\.\d+%',  # Precise percentages
                r'\$[\d,]+\.\d{2}',  # Precise dollar amounts
                r'\d{4}-\d{2}-\d{2}',  # Specific dates
                r'according to',
                r'based on.*data',
                r'analysis shows'
            ]
            
            data_matches = sum(1 for pattern in data_indicators 
                              if re.search(pattern, final_response))
            if data_matches > 0:
                score += min(data_matches * 0.05, 0.15)
        
        # Check for error indicators that might suggest inaccuracy
        error_indicators = ['error', 'failed', 'timeout', 'unable to', 'not found']
        error_matches = sum(1 for indicator in error_indicators 
                           if indicator in final_response.lower())
        if error_matches > 0:
            score -= min(error_matches * 0.1, 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_timeliness_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate timeliness score based on processing time"""
        
        processing_time_ms = conversation.get('processing_time_ms', 0)
        
        if processing_time_ms <= 0:
            return 0.5  # Unknown timing
        
        # Define optimal time ranges (in seconds)
        processing_time_s = processing_time_ms / 1000
        
        if processing_time_s <= 30:  # Very fast
            return 1.0
        elif processing_time_s <= 60:  # Fast
            return 0.9
        elif processing_time_s <= 120:  # Acceptable
            return 0.8
        elif processing_time_s <= 300:  # Slow
            return 0.6
        elif processing_time_s <= 600:  # Very slow
            return 0.4
        else:  # Extremely slow
            return 0.2
    
    def _calculate_relevance_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate how relevant the response is to the user query"""
        
        user_query = conversation.get('user_query', '')
        final_response = conversation.get('final_response', '')
        
        if not user_query or not final_response:
            return 0.5
        
        # Basic keyword relevance
        query_words = set(re.findall(r'\w+', user_query.lower()))
        response_words = set(re.findall(r'\w+', final_response.lower()))
        
        if not query_words:
            return 0.5
        
        # Calculate word overlap
        overlap_score = len(query_words.intersection(response_words)) / len(query_words)
        
        # Boost for domain-specific relevance
        domain_boost = 0.0
        
        # Check if query type matches response content
        query_lower = user_query.lower()
        response_lower = final_response.lower()
        
        relevance_pairs = [
            (['data', 'analysis', 'query', 'sql'], ['data', 'analysis', 'results', 'metrics']),
            (['deal', 'opportunity', 'pipeline'], ['deal', 'opportunity', 'meddpicc', 'qualification']),
            (['lead', 'prospect', 'contact'], ['lead', 'scoring', 'qualification', 'disqualification']),
            (['revenue', 'sales', 'money'], ['revenue', 'sales', '$', 'growth']),
            (['help', 'explain', 'how'], ['here', 'explanation', 'steps', 'process'])
        ]
        
        for query_terms, response_terms in relevance_pairs:
            if any(term in query_lower for term in query_terms):
                if any(term in response_lower for term in response_terms):
                    domain_boost += 0.2
                    break
        
        final_score = min(1.0, overlap_score * 0.7 + domain_boost)
        return max(0.1, final_score)  # Minimum score for any response
    
    def _calculate_user_satisfaction_score(self, conversation: Dict[str, Any]) -> float:
        """Estimate user satisfaction based on conversation indicators"""
        
        # This is estimated since we don't have explicit user feedback
        score = 0.5  # Neutral starting point
        
        final_response = conversation.get('final_response', '')
        
        # Check for satisfaction indicators in the response quality
        success = conversation.get('success', False)
        if success:
            score += 0.3
        
        # Check response completeness and usefulness
        if final_response:
            # Comprehensive responses likely increase satisfaction
            if len(final_response) > 200:
                score += 0.1
            
            # Specific data points likely increase satisfaction
            data_elements = [
                r'\d+%', r'\$[\d,]+', r'\d{4}-\d{2}-\d{2}',
                r'recommendations?', r'insights?', r'analysis'
            ]
            data_matches = sum(1 for pattern in data_elements 
                              if re.search(pattern, final_response.lower()))
            if data_matches > 0:
                score += min(data_matches * 0.05, 0.2)
        
        # Check for negative satisfaction indicators
        negative_indicators = ['error', 'failed', 'unable to', 'not available', 'try again']
        negative_matches = sum(1 for indicator in negative_indicators 
                              if indicator in final_response.lower())
        if negative_matches > 0:
            score -= min(negative_matches * 0.15, 0.4)
        
        # Processing time impact on satisfaction
        processing_time_ms = conversation.get('processing_time_ms', 0)
        if processing_time_ms > 300000:  # > 5 minutes
            score -= 0.2
        elif processing_time_ms > 120000:  # > 2 minutes
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_technical_quality_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate technical quality of the conversation execution"""
        
        score = 0.5  # Base score
        
        # Check agent attribution quality
        export_metadata = conversation.get('export_metadata', {})
        if 'validation' in export_metadata:
            validation = export_metadata['validation']
            quality_assessment = validation.get('quality_assessment', {})
            if quality_assessment:
                score += quality_assessment.get('overall_score', 0) * 0.3
        
        # Check system prompt filtering
        system_prompts_excluded = export_metadata.get('system_prompts_excluded', False)
        if system_prompts_excluded:
            score += 0.1
        
        # Check tool execution quality
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            total_quality = 0
            quality_count = 0
            
            for step in agent_flow:
                if 'tool_normalization' in step:
                    tool_norm = step['tool_normalization']
                    high_quality = tool_norm.get('high_quality_tools', 0)
                    total_tools = tool_norm.get('normalized_tool_count', 0)
                    
                    if total_tools > 0:
                        quality_ratio = high_quality / total_tools
                        total_quality += quality_ratio
                        quality_count += 1
            
            if quality_count > 0:
                avg_tool_quality = total_quality / quality_count
                score += avg_tool_quality * 0.3
        
        # Check for processing errors
        success = conversation.get('success', True)
        if not success:
            score -= 0.3
        
        error_details = conversation.get('error_details')
        if error_details:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_business_impact_score(self, conversation: Dict[str, Any]) -> float:
        """Calculate potential business impact of the conversation"""
        
        score = 0.3  # Base score (most conversations have some business value)
        
        final_response = conversation.get('final_response', '')
        user_query = conversation.get('user_query', '')
        
        # Check for business value indicators in response
        business_matches = sum(1 for pattern in self.business_value_patterns 
                              if re.search(pattern, final_response.lower()))
        if business_matches > 0:
            score += min(business_matches * 0.1, 0.4)
        
        # Check for specific business outcomes
        business_outcomes = [
            r'cost.*sav.*\$[\d,]+',
            r'revenue.*increase.*\$[\d,]+',
            r'efficiency.*improve.*\d+%',
            r'conversion.*up.*\d+%',
            r'performance.*gain.*\d+%'
        ]
        
        outcome_matches = sum(1 for pattern in business_outcomes 
                             if re.search(pattern, final_response.lower()))
        if outcome_matches > 0:
            score += min(outcome_matches * 0.2, 0.5)
        
        # Check query type for inherent business value
        query_lower = user_query.lower()
        high_value_queries = [
            'revenue', 'sales', 'pipeline', 'conversion', 'customer',
            'deal', 'opportunity', 'forecast', 'performance', 'growth'
        ]
        
        if any(term in query_lower for term in high_value_queries):
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _analyze_conversation_outcome(self, conversation_data: Dict[str, Any]) -> ConversationOutcomeAnalysis:
        """Analyze the overall outcome of the conversation"""
        
        conversation = conversation_data.get('conversation', {})
        final_response = conversation.get('final_response', '')
        success = conversation.get('success', False)
        error_details = conversation.get('error_details')
        
        # Determine outcome
        outcome = ConversationOutcome.SUCCESS
        confidence = 0.8
        success_indicators = []
        failure_indicators = []
        
        # Check for explicit success/failure
        if not success:
            outcome = ConversationOutcome.FAILURE
            confidence = 0.9
            failure_indicators.append("Conversation marked as unsuccessful")
        
        if error_details:
            outcome = ConversationOutcome.ERROR
            confidence = 0.9
            failure_indicators.append(f"Error occurred: {error_details}")
        
        # Check processing time for timeout
        processing_time_ms = conversation.get('processing_time_ms', 0)
        if processing_time_ms > 600000:  # 10 minutes
            outcome = ConversationOutcome.TIMEOUT
            failure_indicators.append("Excessive processing time suggests timeout")
        
        # Analyze response content
        if final_response:
            # Success indicators
            for pattern in self.success_indicators:
                if re.search(pattern, final_response.lower()):
                    success_indicators.append(f"Response contains: {pattern}")
            
            # Failure indicators
            for pattern in self.failure_indicators:
                if re.search(pattern, final_response.lower()):
                    failure_indicators.append(f"Response contains: {pattern}")
            
            # Adjust outcome based on indicators
            if len(failure_indicators) > len(success_indicators) and outcome == ConversationOutcome.SUCCESS:
                outcome = ConversationOutcome.PARTIAL_SUCCESS
                confidence = 0.6
        
        # Determine user satisfaction
        user_satisfaction = self._determine_user_satisfaction(final_response)
        
        # Determine business value
        business_value_delivered = self._assess_business_value_delivered(conversation)
        
        # Determine if follow-up needed
        follow_up_needed = self._assess_follow_up_needed(conversation, outcome)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            conversation, outcome, success_indicators, failure_indicators
        )
        
        return ConversationOutcomeAnalysis(
            outcome=outcome,
            confidence=confidence,
            success_indicators=success_indicators,
            failure_indicators=failure_indicators,
            user_satisfaction=user_satisfaction,
            business_value_delivered=business_value_delivered,
            follow_up_needed=follow_up_needed,
            improvement_suggestions=improvement_suggestions
        )
    
    def _determine_user_satisfaction(self, final_response: str) -> UserSatisfactionLevel:
        """Determine user satisfaction level from response indicators"""
        
        response_lower = final_response.lower()
        
        # Check satisfaction indicators
        for level, indicators in self.satisfaction_indicators.items():
            for indicator in indicators:
                if re.search(indicator, response_lower):
                    return UserSatisfactionLevel(level.upper())
        
        # Default assessment based on response quality
        if len(final_response) > 200 and any(word in response_lower for word in ['analysis', 'data', 'results']):
            return UserSatisfactionLevel.MEDIUM
        elif any(word in response_lower for word in ['error', 'failed', 'unable']):
            return UserSatisfactionLevel.LOW
        
        return UserSatisfactionLevel.UNKNOWN
    
    def _assess_business_value_delivered(self, conversation: Dict[str, Any]) -> bool:
        """Assess whether business value was delivered"""
        
        final_response = conversation.get('final_response', '')
        user_query = conversation.get('user_query', '')
        
        # High business value queries
        high_value_terms = [
            'revenue', 'sales', 'pipeline', 'conversion', 'customer',
            'deal', 'opportunity', 'forecast', 'performance', 'growth',
            'cost', 'efficiency', 'optimization', 'roi'
        ]
        
        query_has_business_intent = any(term in user_query.lower() for term in high_value_terms)
        
        # Response has business content
        response_has_business_content = any(
            re.search(pattern, final_response.lower()) 
            for pattern in self.business_value_patterns
        )
        
        # Successful completion
        success = conversation.get('success', False)
        
        return query_has_business_intent and response_has_business_content and success
    
    def _assess_follow_up_needed(self, conversation: Dict[str, Any], outcome: ConversationOutcome) -> bool:
        """Assess whether follow-up is needed"""
        
        # Follow-up needed for failures
        if outcome in [ConversationOutcome.FAILURE, ConversationOutcome.ERROR, ConversationOutcome.TIMEOUT]:
            return True
        
        # Follow-up for partial success
        if outcome == ConversationOutcome.PARTIAL_SUCCESS:
            return True
        
        # Follow-up if response suggests more work needed
        final_response = conversation.get('final_response', '')
        follow_up_indicators = [
            'need more information',
            'additional analysis',
            'follow up',
            'next steps',
            'continue',
            'part 1',
            'preliminary'
        ]
        
        return any(indicator in final_response.lower() for indicator in follow_up_indicators)
    
    def _analyze_agent_performance(self, conversation_data: Dict[str, Any]) -> List[AgentPerformanceMetrics]:
        """Analyze performance of individual agents"""
        
        conversation = conversation_data.get('conversation', {})
        agent_flow = conversation.get('agent_flow', [])
        
        if not agent_flow:
            return []
        
        # Aggregate agent performance data
        agent_stats = {}
        
        for step in agent_flow:
            agent_name = step.get('agent_name', 'unknown')
            
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    'steps': 0,
                    'total_time_ms': 0,
                    'tools_executed': 0,
                    'successful_tools': 0,
                    'errors': 0,
                    'handoffs_initiated': 0,
                    'collaborations': 0
                }
            
            stats = agent_stats[agent_name]
            stats['steps'] += 1
            
            # Timing
            timing = step.get('timing', {})
            duration = timing.get('duration_ms', 0)
            stats['total_time_ms'] += duration
            
            # Tools
            tools_used = step.get('tools_used', [])
            stats['tools_executed'] += len(tools_used)
            
            for tool in tools_used:
                if isinstance(tool, dict) and tool.get('success', True):
                    stats['successful_tools'] += 1
                elif hasattr(tool, 'success') and getattr(tool, 'success', True):
                    stats['successful_tools'] += 1
            
            # Errors
            if step.get('error_details'):
                stats['errors'] += 1
            
            # Handoffs and collaborations
            if step.get('agent_attribution', {}).get('handoff_detected'):
                stats['handoffs_initiated'] += 1
            
            collaboration_indicators = step.get('collaboration_indicators', [])
            stats['collaborations'] += len(collaboration_indicators)
        
        # Convert to performance metrics
        performance_metrics = []
        
        for agent_name, stats in agent_stats.items():
            # Calculate metrics
            tool_success_rate = (stats['successful_tools'] / max(stats['tools_executed'], 1))
            error_rate = stats['errors'] / max(stats['steps'], 1)
            avg_response_time = stats['total_time_ms'] / max(stats['steps'], 1)
            
            # Effectiveness score
            effectiveness_score = self._calculate_agent_effectiveness(stats, tool_success_rate, error_rate)
            
            # Handoff quality (placeholder - would need more sophisticated analysis)
            handoff_quality = min(1.0, stats['handoffs_initiated'] * 0.5) if stats['handoffs_initiated'] > 0 else 0.5
            
            # Collaboration score
            collaboration_score = min(1.0, stats['collaborations'] * 0.2)
            
            # Business contribution (based on tool types and success)
            business_contribution = self._calculate_business_contribution(agent_name, stats)
            
            performance_metrics.append(AgentPerformanceMetrics(
                agent_name=agent_name,
                effectiveness_score=effectiveness_score,
                response_time_ms=int(avg_response_time),
                tool_success_rate=tool_success_rate,
                handoff_quality=handoff_quality,
                collaboration_score=collaboration_score,
                error_rate=error_rate,
                business_contribution=business_contribution
            ))
        
        return performance_metrics
    
    def _calculate_agent_effectiveness(self, stats: Dict[str, int], tool_success_rate: float, error_rate: float) -> float:
        """Calculate overall agent effectiveness score"""
        
        score = 0.5  # Base score
        
        # Tool success contribution
        score += tool_success_rate * 0.3
        
        # Error penalty
        score -= error_rate * 0.3
        
        # Activity bonus (agents that do more work)
        if stats['tools_executed'] > 5:
            score += 0.1
        elif stats['tools_executed'] > 10:
            score += 0.2
        
        # Collaboration bonus
        if stats['collaborations'] > 0:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_business_contribution(self, agent_name: str, stats: Dict[str, int]) -> float:
        """Calculate agent's business contribution score"""
        
        # Base scores by agent type
        business_scores = {
            'data': 0.8,      # Data agents directly contribute to business insights
            'deal': 0.9,      # Deal analysis is high business value
            'lead': 0.7,      # Lead analysis is valuable but earlier stage
            'manager': 0.6,   # Coordination is important but indirect
            'execution': 0.8, # Execution drives actions
            'web': 0.4        # Web search is supportive
        }
        
        agent_lower = agent_name.lower()
        base_score = 0.5  # Default for unknown agents
        
        for agent_type, score in business_scores.items():
            if agent_type in agent_lower:
                base_score = score
                break
        
        # Adjust based on activity and success
        activity_factor = min(1.2, 1 + (stats['tools_executed'] / 20))  # More tools = more contribution
        success_factor = (stats['successful_tools'] / max(stats['tools_executed'], 1))  # Success rate matters
        
        final_score = base_score * activity_factor * success_factor
        
        return max(0.0, min(1.0, final_score))
    
    def _calculate_system_performance(self, conversation_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall system performance metrics"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Processing efficiency
        processing_time_ms = conversation.get('processing_time_ms', 0)
        efficiency_score = 1.0 if processing_time_ms <= 30000 else max(0.2, 1.0 - (processing_time_ms - 30000) / 300000)
        
        # System reliability
        success = conversation.get('success', False)
        error_details = conversation.get('error_details')
        reliability_score = 1.0 if success and not error_details else 0.3
        
        # Resource utilization
        agent_flow = conversation.get('agent_flow', [])
        total_agents = len(set(step.get('agent_name', 'unknown') for step in agent_flow))
        utilization_score = min(1.0, total_agents / 3)  # Optimal use of 2-3 agents
        
        # Data quality
        export_metadata = conversation_data.get('export_metadata', {})
        validation = export_metadata.get('validation', {})
        data_quality_score = validation.get('quality_assessment', {}).get('overall_score', 0.5)
        
        return {
            'processing_efficiency': efficiency_score,
            'system_reliability': reliability_score,
            'resource_utilization': utilization_score,
            'data_quality': data_quality_score,
            'overall_system_performance': (efficiency_score + reliability_score + utilization_score + data_quality_score) / 4
        }
    
    def _generate_recommendations(
        self, 
        quality_metrics: QualityMetrics, 
        outcome_analysis: ConversationOutcomeAnalysis,
        agent_performance: List[AgentPerformanceMetrics]
    ) -> List[str]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        # Overall quality recommendations
        if quality_metrics.overall_score < 0.7:
            recommendations.append("Overall conversation quality is below target - review all metrics for improvement opportunities")
        
        # Specific metric recommendations
        if quality_metrics.completeness_score < 0.6:
            recommendations.append("Improve response completeness - ensure all aspects of user queries are addressed")
        
        if quality_metrics.accuracy_score < 0.7:
            recommendations.append("Enhance response accuracy - review tool execution success rates and data validation")
        
        if quality_metrics.timeliness_score < 0.6:
            recommendations.append("Optimize processing time - consider parallel execution or timeout management")
        
        if quality_metrics.relevance_score < 0.6:
            recommendations.append("Improve response relevance - better align responses with user query intent")
        
        # Outcome-based recommendations
        if outcome_analysis.outcome != ConversationOutcome.SUCCESS:
            recommendations.append(f"Address conversation outcome: {outcome_analysis.outcome.value}")
        
        if len(outcome_analysis.failure_indicators) > len(outcome_analysis.success_indicators):
            recommendations.append("Reduce failure indicators in responses - improve error handling and messaging")
        
        # Agent performance recommendations
        for agent_perf in agent_performance:
            if agent_perf.effectiveness_score < 0.6:
                recommendations.append(f"Improve {agent_perf.agent_name} effectiveness - current score: {agent_perf.effectiveness_score:.2f}")
            
            if agent_perf.tool_success_rate < 0.8:
                recommendations.append(f"Improve {agent_perf.agent_name} tool reliability - success rate: {agent_perf.tool_success_rate:.2f}")
            
            if agent_perf.error_rate > 0.2:
                recommendations.append(f"Reduce {agent_perf.agent_name} error rate - current: {agent_perf.error_rate:.2f}")
        
        # User satisfaction recommendations
        if outcome_analysis.user_satisfaction == UserSatisfactionLevel.LOW:
            recommendations.append("Improve user satisfaction - focus on response quality and completeness")
        
        # Business impact recommendations
        if not outcome_analysis.business_value_delivered:
            recommendations.append("Enhance business value delivery - ensure responses provide actionable insights")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_improvement_suggestions(
        self, 
        conversation: Dict[str, Any], 
        outcome: ConversationOutcome,
        success_indicators: List[str],
        failure_indicators: List[str]
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        
        # Based on outcome
        if outcome == ConversationOutcome.FAILURE:
            suggestions.append("Review error handling and provide better fallback responses")
            suggestions.append("Implement retry mechanisms for failed operations")
        
        elif outcome == ConversationOutcome.PARTIAL_SUCCESS:
            suggestions.append("Enhance response completeness checking")
            suggestions.append("Implement follow-up question capabilities")
        
        elif outcome == ConversationOutcome.TIMEOUT:
            suggestions.append("Implement parallel processing for better performance")
            suggestions.append("Add progress updates for long-running operations")
        
        # Based on failure indicators
        if failure_indicators:
            suggestions.append("Improve error messaging to be more user-friendly")
            suggestions.append("Add proactive error prevention mechanisms")
        
        # Based on processing time
        processing_time_ms = conversation.get('processing_time_ms', 0)
        if processing_time_ms > 120000:  # > 2 minutes
            suggestions.append("Optimize processing pipeline for better performance")
            suggestions.append("Consider caching frequently requested data")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _create_analysis_metadata(
        self, 
        conversation_data: Dict[str, Any], 
        quality_metrics: QualityMetrics
    ) -> Dict[str, Any]:
        """Create metadata for the analysis"""
        
        conversation = conversation_data.get('conversation', {})
        
        return {
            'analyzer_version': '1.0',
            'analysis_type': 'comprehensive_quality_analysis',
            'conversation_source': conversation_data.get('export_metadata', {}).get('source', 'unknown'),
            'conversation_length_ms': conversation.get('processing_time_ms', 0),
            'agent_count': len(conversation.get('agents_involved', [])),
            'tool_executions': sum(len(step.get('tools_used', [])) for step in conversation.get('agent_flow', [])),
            'quality_category': self._categorize_quality(quality_metrics.overall_score),
            'analysis_confidence': 0.8,  # Confidence in the analysis results
            'improvement_potential': max(0.0, 1.0 - quality_metrics.overall_score),
            'business_relevance': quality_metrics.business_impact_score
        }
    
    def _categorize_quality(self, overall_score: float) -> str:
        """Categorize quality based on score"""
        
        if overall_score >= self.quality_thresholds['excellent']:
            return 'excellent'
        elif overall_score >= self.quality_thresholds['good']:
            return 'good'
        elif overall_score >= self.quality_thresholds['fair']:
            return 'fair'
        else:
            return 'poor'