"""
Structured logging utilities for the Resee application
"""
import functools
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AILogger:
    """AI-specific logging functionality"""

    def __init__(self):
        self.logger = logging.getLogger('resee.ai')

    def log_question_generation(self, user_id: int, content_id: int,
                                question_types: list, count: int, success: bool = False,
                                generated_count: int = 0, subscription_tier: str = '',
                                processing_time_ms: float = 0):
        """Log AI question generation events"""
        self.logger.info(f"AI Question Generation: user={user_id}, content={content_id}, "
                         f"types={question_types}, requested={count}, success={success}, "
                         f"generated={generated_count}, tier={subscription_tier}, "
                         f"time={processing_time_ms}ms")

    def log_answer_evaluation(self, user_id: int, question_id: int,
                              evaluation_result: str, success: bool = True):
        """Log AI answer evaluation events"""
        self.logger.info(f"AI Answer Evaluation: user={user_id}, question={question_id}, "
                         f"result={evaluation_result}, success={success}")

    def log_ai_service_error(self, service: str, error: str, user_id: Optional[int] = None):
        """Log AI service errors"""
        self.logger.error(f"AI Service Error: service={service}, error={error}, user={user_id}")


# Global AI logger instance
ai_logger = AILogger()


def log_api_call(func):
    """Decorator to log API calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # milliseconds

            logger.info(f"API Call: {func.__name__} completed successfully in {duration:.2f}ms")
            return result
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            logger.error(f"API Call: {func.__name__} failed after {duration:.2f}ms - {str(e)}")
            raise
    return wrapper


def log_performance(operation_name: str):
    """Decorator to log performance metrics"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = (end_time - start_time) * 1000

                logger.info(f"Performance: {operation_name} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                logger.error(f"Performance: {operation_name} failed after {duration:.2f}ms - {str(e)}")
                raise
        return wrapper
    return decorator


def log_user_action(action: str, user_id: Optional[int] = None,
                    metadata: Optional[Dict[str, Any]] = None):
    """Log user actions"""
    log_data = {
        'action': action,
        'user_id': user_id,
        'timestamp': time.time()
    }
    if metadata:
        log_data.update(metadata)

    logger.info(f"User Action: {log_data}")


class BusinessMetricsLogger:
    """Logger for business metrics and analytics"""

    def __init__(self):
        self.logger = logging.getLogger('resee.business_metrics')

    def log_subscription_event(self, user_id: int, event_type: str,
                               tier: str, metadata: Optional[Dict] = None):
        """Log subscription-related events"""
        self.logger.info(f"Subscription Event: user={user_id}, type={event_type}, "
                         f"tier={tier}, metadata={metadata}")

    def log_content_event(self, user_id: int, content_id: int,
                          event_type: str, metadata: Optional[Dict] = None):
        """Log content-related events"""
        self.logger.info(f"Content Event: user={user_id}, content={content_id}, "
                         f"type={event_type}, metadata={metadata}")


# Global business metrics logger
business_logger = BusinessMetricsLogger()

# Performance logger instance
performance_logger = logging.getLogger('resee.performance')


def setup_structured_logging():
    """Setup structured logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/resee.log', mode='a')
        ]
    )
