"""
Debug Logger for Personal AI Assistant
Provides centralized debug logging with color-coded output and structured formatting.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class ColorCodes:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class PipelineExecution:
    """Track pipeline execution details for debugging"""
    execution_id: str
    start_time: datetime
    user_id: int
    message: str
    intent_classification: Optional[Dict[str, Any]] = None
    rag_retrieval: Optional[Dict[str, Any]] = None
    llm_processing: Optional[Dict[str, Any]] = None 
    action_processing: Optional[Dict[str, Any]] = None
    vector_operations: Optional[Dict[str, Any]] = None
    total_duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class DebugLogger:
    """Centralized debug logging system for PAA"""
    
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_to_file = os.getenv("DEBUG_LOG_TO_FILE", "false").lower() == "true"
        
        # Current pipeline execution tracking
        self.current_execution: Optional[PipelineExecution] = None
        self.recent_executions: List[PipelineExecution] = []
        
        self.setup_logging()
        
        if self.debug_mode:
            self._log_startup_info()
    
    def setup_logging(self):
        """Configure logging based on environment settings"""
        # Clear any existing handlers
        logger = logging.getLogger()
        logger.handlers.clear()
        
        # Set log level
        level = getattr(logging, self.log_level, logging.INFO)
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if enabled
        if self.log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"debug_session_{timestamp}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            if self.debug_mode:
                print(f"{ColorCodes.OKCYAN}📝 Debug logs will be saved to: {log_file}{ColorCodes.ENDC}")
    
    def _log_startup_info(self):
        """Log startup information when debug mode is enabled"""
        print(f"\n{ColorCodes.HEADER}{'='*60}{ColorCodes.ENDC}")
        print(f"{ColorCodes.HEADER}🐛 DEBUG MODE ACTIVATED{ColorCodes.ENDC}")
        print(f"{ColorCodes.HEADER}{'='*60}{ColorCodes.ENDC}")
        print(f"{ColorCodes.OKCYAN}📊 Debug Features Enabled:{ColorCodes.ENDC}")
        
        features = {
            "HTTP Requests": os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true",
            "Intent Classification": os.getenv("DEBUG_INTENT_CLASSIFICATION", "false").lower() == "true",
            "RAG System": os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true",
            "LLM Calls": os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true",
            "Action Processor": os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true",
            "Vector Store": os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true",
        }
        
        for feature, enabled in features.items():
            status = f"{ColorCodes.OKGREEN}✅ ON{ColorCodes.ENDC}" if enabled else f"{ColorCodes.FAIL}❌ OFF{ColorCodes.ENDC}"
            print(f"  • {feature}: {status}")
        
        print(f"{ColorCodes.HEADER}{'='*60}{ColorCodes.ENDC}\n")
    
    def start_pipeline_execution(self, user_id: int, message: str) -> str:
        """Start tracking a new pipeline execution"""
        execution_id = f"exec_{datetime.now().strftime('%H%M%S_%f')}"
        
        self.current_execution = PipelineExecution(
            execution_id=execution_id,
            start_time=datetime.now(),
            user_id=user_id,
            message=message
        )
        
        if self.debug_mode:
            print(f"\n{ColorCodes.BOLD}{ColorCodes.OKBLUE}🚀 Pipeline Execution Started: {execution_id}{ColorCodes.ENDC}")
            print(f"{ColorCodes.OKCYAN}   User: {user_id} | Message: \"{message[:50]}{'...' if len(message) > 50 else ''}\"{ColorCodes.ENDC}")
        
        return execution_id
    
    def end_pipeline_execution(self, success: bool = True, error: Optional[str] = None):
        """End the current pipeline execution"""
        if self.current_execution:
            self.current_execution.total_duration = (
                datetime.now() - self.current_execution.start_time
            ).total_seconds() * 1000  # Convert to milliseconds
            
            self.current_execution.success = success
            self.current_execution.error = error
            
            # Add to recent executions (keep last 10)
            self.recent_executions.append(self.current_execution)
            if len(self.recent_executions) > 10:
                self.recent_executions = self.recent_executions[-10:]
            
            if self.debug_mode:
                status = f"{ColorCodes.OKGREEN}✅ SUCCESS{ColorCodes.ENDC}" if success else f"{ColorCodes.FAIL}❌ FAILED{ColorCodes.ENDC}"
                duration = f"{self.current_execution.total_duration:.0f}ms"
                print(f"{ColorCodes.BOLD}🏁 Pipeline Execution Completed: {status} ({duration}){ColorCodes.ENDC}")
                
                if error:
                    print(f"{ColorCodes.FAIL}   Error: {error}{ColorCodes.ENDC}")
                print()  # Empty line for separation
            
            self.current_execution = None
    
    def log_http_request(self, method: str, path: str, headers: Dict[str, str], body: Optional[str] = None):
        """Log HTTP request details"""
        if not (self.debug_mode and os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true"):
            return
        
        print(f"{ColorCodes.OKBLUE}📥 HTTP Request: {method} {path}{ColorCodes.ENDC}")
        
        # Log relevant headers only
        relevant_headers = {k: v for k, v in headers.items() 
                          if k.lower() in ['content-type', 'authorization', 'user-agent']}
        if relevant_headers:
            print(f"   Headers: {json.dumps(relevant_headers, indent=2)}")
        
        if body and len(body) < 500:  # Only log short bodies
            try:
                body_json = json.loads(body)
                print(f"   Body: {json.dumps(body_json, indent=2)}")
            except:
                print(f"   Body: {body}")
    
    def log_http_response(self, status_code: int, process_time: float, headers: Dict[str, str]):
        """Log HTTP response details"""
        if not (self.debug_mode and os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true"):
            return
        
        status_color = ColorCodes.OKGREEN if status_code < 400 else ColorCodes.FAIL
        print(f"{ColorCodes.OKGREEN}📤 HTTP Response: {status_color}{status_code}{ColorCodes.ENDC} ({process_time*1000:.0f}ms)")
    
    def log_intent_classification(self, message: str, intent_result: Dict[str, Any]):
        """Log intent classification results"""
        if not (self.debug_mode and os.getenv("DEBUG_INTENT_CLASSIFICATION", "false").lower() == "true"):
            return
        
        if self.current_execution:
            self.current_execution.intent_classification = intent_result
        
        print(f"{ColorCodes.WARNING}🎯 Intent Classification:{ColorCodes.ENDC}")
        print(f"   Intent: {ColorCodes.BOLD}{intent_result.get('primary_intent', 'unknown')}{ColorCodes.ENDC}")
        print(f"   Confidence: {intent_result.get('confidence', 0):.2f}")
        
        entities = intent_result.get('entities', {})
        if entities:
            print(f"   Entities: {json.dumps(entities, indent=2)}")
    
    def log_rag_retrieval_start(self, intent: Any, user_id: int):
        """Log RAG retrieval start"""
        if not (self.debug_mode and os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true"):
            return
        
        print(f"{ColorCodes.OKCYAN}🔍 RAG Retrieval Started:{ColorCodes.ENDC}")
        print(f"   User: {user_id} | Intent: {getattr(intent, 'primary_intent', 'unknown')}")
    
    def log_rag_retrieval_result(self, context_sources: List[str], similarity_scores: List[float], 
                                retrieved_items: int, processing_time: float):
        """Log RAG retrieval results"""
        if not (self.debug_mode and os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true"):
            return
        
        if self.current_execution:
            self.current_execution.rag_retrieval = {
                'sources': context_sources,
                'retrieved_items': retrieved_items,
                'processing_time': processing_time,
                'avg_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
            }
        
        print(f"{ColorCodes.OKCYAN}✅ RAG Retrieved: {retrieved_items} items ({processing_time:.0f}ms){ColorCodes.ENDC}")
        print(f"   Sources: {', '.join(context_sources)}")
        if similarity_scores:
            print(f"   Avg Similarity: {sum(similarity_scores) / len(similarity_scores):.3f}")
    
    def log_llm_call_start(self, message: str, context_summary: Dict[str, int], intent: str):
        """Log LLM call start"""
        if not (self.debug_mode and os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true"):
            return
        
        print(f"{ColorCodes.HEADER}🤖 LLM Processing Started:{ColorCodes.ENDC}")
        print(f"   Intent: {intent}")
        print(f"   Context: {json.dumps(context_summary)}")
    
    def log_llm_call_result(self, prompt_length: int, response_length: int, api_call_time: float, 
                           tokens_used: int, structured_output: Dict[str, Any]):
        """Log LLM call results"""
        if not (self.debug_mode and os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true"):
            return
        
        if self.current_execution:
            self.current_execution.llm_processing = {
                'prompt_length': prompt_length,
                'response_length': response_length,
                'api_call_time': api_call_time,
                'tokens_used': tokens_used,
                'has_commitments': len(structured_output.get('commitments', [])) > 0,
                'has_habit_actions': len(structured_output.get('habit_actions', [])) > 0,
                'has_people_updates': len(structured_output.get('people_updates', [])) > 0
            }
        
        print(f"{ColorCodes.HEADER}✅ LLM Response: {response_length} chars, ~{tokens_used} tokens ({api_call_time:.0f}ms){ColorCodes.ENDC}")
        
        # Log structured output summary
        commitments = len(structured_output.get('commitments', []))
        habit_actions = len(structured_output.get('habit_actions', []))
        people_updates = len(structured_output.get('people_updates', []))
        
        if any([commitments, habit_actions, people_updates]):
            print(f"   Actions: {commitments} commitments, {habit_actions} habits, {people_updates} people")
    
    def log_action_processing_start(self, commitments_count: int, habit_actions_count: int, 
                                   people_updates_count: int, user_profile_updates_count: int, scheduled_actions_count: int):
        """Log action processing start"""
        if not (self.debug_mode and os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true"):
            return
        
        print(f"{ColorCodes.WARNING}⚡ Action Processing Started:{ColorCodes.ENDC}")
        print(f"   {commitments_count} commitments, {habit_actions_count} habit actions")
        print(f"   {people_updates_count} people updates, {user_profile_updates_count} profile updates")
        print(f"   {scheduled_actions_count} scheduled actions")
    
    def log_action_processing_result(self, executed_actions: Dict[str, int], 
                                   failed_actions: Dict[str, int], database_changes: Dict[str, int]):
        """Log action processing results"""
        if not (self.debug_mode and os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true"):
            return
        
        if self.current_execution:
            self.current_execution.action_processing = {
                'executed_actions': executed_actions,
                'failed_actions': failed_actions,
                'database_changes': database_changes
            }
        
        total_executed = sum(executed_actions.values())
        total_failed = sum(failed_actions.values())
        
        print(f"{ColorCodes.WARNING}✅ Actions Processed: {total_executed} executed, {total_failed} failed{ColorCodes.ENDC}")
        
        if database_changes:
            changes_str = ", ".join([f"{count} {action}" for action, count in database_changes.items()])
            print(f"   DB Changes: {changes_str}")
    
    def log_vector_search_start(self, collection: str, query: str, user_id: int, limit: int):
        """Log vector search start"""
        if not (self.debug_mode and os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true"):
            return
        
        print(f"{ColorCodes.OKCYAN}🔎 Vector Search: {collection}{ColorCodes.ENDC}")
        print(f"   Query: \"{query[:50]}{'...' if len(query) > 50 else ''}\"")
        print(f"   User: {user_id} | Limit: {limit}")
    
    def log_vector_search_result(self, results_count: int, similarity_scores: List[float], search_time: float):
        """Log vector search results"""
        if not (self.debug_mode and os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true"):
            return
        
        if self.current_execution:
            if not self.current_execution.vector_operations:
                self.current_execution.vector_operations = {'searches': []}
            
            self.current_execution.vector_operations['searches'].append({
                'results_count': results_count,
                'avg_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
                'search_time': search_time
            })
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        print(f"{ColorCodes.OKCYAN}✅ Found {results_count} results (avg similarity: {avg_similarity:.3f}) ({search_time:.0f}ms){ColorCodes.ENDC}")
    
    def log_vector_embedding(self, collection: str, document_id: str, embedding_time: float, success: bool = True):
        """Log vector embedding operations"""
        if not (self.debug_mode and os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true"):
            return
        
        status = f"{ColorCodes.OKGREEN}✅{ColorCodes.ENDC}" if success else f"{ColorCodes.FAIL}❌{ColorCodes.ENDC}"
        print(f"{ColorCodes.OKCYAN}📝 Vector Embedding: {collection}/{document_id} {status} ({embedding_time:.0f}ms){ColorCodes.ENDC}")
    
    def get_recent_executions(self) -> List[Dict[str, Any]]:
        """Get recent pipeline executions for debugging"""
        return [
            {
                'execution_id': exec.execution_id,
                'start_time': exec.start_time.isoformat(),
                'user_id': exec.user_id,
                'message': exec.message[:100],
                'duration': exec.total_duration,
                'success': exec.success,
                'error': exec.error,
                'stages': {
                    'intent_classification': exec.intent_classification is not None,
                    'rag_retrieval': exec.rag_retrieval is not None,
                    'llm_processing': exec.llm_processing is not None,
                    'action_processing': exec.action_processing is not None,
                    'vector_operations': exec.vector_operations is not None
                }
            }
            for exec in self.recent_executions
        ]
    
    def get_debug_status(self) -> Dict[str, Any]:
        """Get current debug configuration status"""
        return {
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "debug_features": {
                "http_requests": os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true",
                "intent_classification": os.getenv("DEBUG_INTENT_CLASSIFICATION", "false").lower() == "true",
                "rag_system": os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true",
                "llm_calls": os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true",
                "action_processor": os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true",
                "vector_store": os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true"
            },
            "recent_executions_count": len(self.recent_executions)
        }
    
    # Standard logging methods for compatibility
    def info(self, message: str):
        """Log info message"""
        if self.debug_mode:
            print(f"{ColorCodes.OKBLUE}ℹ️  {message}{ColorCodes.ENDC}")
        logging.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        if self.debug_mode:
            print(f"{ColorCodes.WARNING}⚠️  {message}{ColorCodes.ENDC}")
        logging.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        if self.debug_mode:
            print(f"{ColorCodes.FAIL}❌ {message}{ColorCodes.ENDC}")
        logging.error(message)
        
        # Update current execution if active
        if self.current_execution:
            self.current_execution.success = False
            if not self.current_execution.error:
                self.current_execution.error = message
    
    def debug(self, message: str):
        """Log debug message"""
        if self.debug_mode:
            print(f"{ColorCodes.OKCYAN}🐛 {message}{ColorCodes.ENDC}")
        logging.debug(message)


# Global debug logger instance
debug_logger = DebugLogger()