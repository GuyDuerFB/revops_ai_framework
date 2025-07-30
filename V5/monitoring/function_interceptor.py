import functools
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict

# Import schema classes with fallback
try:
    from conversation_schema import FunctionCall
except ImportError:
    # Fallback if schema not available
    class FunctionCall:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

class FunctionInterceptor:
    def __init__(self, conversation_tracker):
        self.conversation_tracker = conversation_tracker
    
    def track_function_call(self, function_name: str, agent_name: str):
        """Decorator to track function calls"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_timestamp = datetime.now(timezone.utc).isoformat()
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Calculate execution time
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Create function call record
                    function_call = FunctionCall(
                        function=function_name,
                        agent=agent_name,
                        full_parameters={
                            'args': args,
                            'kwargs': kwargs
                        },
                        full_response=result if isinstance(result, dict) else {'result': str(result)},
                        execution_time_ms=execution_time_ms,
                        success=True,
                        timestamp=start_timestamp
                    )
                    
                    # Add to conversation tracker
                    self.conversation_tracker.add_function_call(function_call)
                    
                    return result
                    
                except Exception as e:
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    function_call = FunctionCall(
                        function=function_name,
                        agent=agent_name,
                        full_parameters={
                            'args': args,
                            'kwargs': kwargs
                        },
                        full_response={'error': str(e)},
                        execution_time_ms=execution_time_ms,
                        success=False,
                        timestamp=start_timestamp
                    )
                    
                    self.conversation_tracker.add_function_call(function_call)
                    raise
            
            return wrapper
        return decorator