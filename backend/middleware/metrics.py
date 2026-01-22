"""
Prometheus metrics middleware for CEP Machine Backend
Production-ready monitoring and observability
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.middleware import PrometheusMiddleware
from prometheus_client.exposition import MetricsHandler
import time
import logging
from typing import Callable
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

TOOL_EXECUTION_COUNT = Counter(
    'tool_executions_total',
    'Total tool executions',
    ['tool_name', 'status']
)

TOOL_EXECUTION_DURATION = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration in seconds',
    ['tool_name']
)

AGENT_INVOCATION_COUNT = Counter(
    'agent_invocations_total',
    'Total agent invocations',
    ['agent_name', 'status']
)

AGENT_INVOCATION_DURATION = Histogram(
    'agent_invocation_duration_seconds',
    'Agent invocation duration in seconds',
    ['agent_name']
)

COPLOTKIT_REQUEST_COUNT = Counter(
    'copilotkit_requests_total',
    'Total CopilotKit requests',
    ['agent', 'action']
)

COPLOTKIT_REQUEST_DURATION = Histogram(
    'copilotkit_request_duration_seconds',
    'CopilotKit request duration in seconds',
    ['agent', 'action']
)

# System metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

class MetricsMiddleware:
    """Custom metrics middleware for FastAPI"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        try:
            # Process request
            response = await self.app(scope, receive, send)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            method = request.method
            endpoint = request.url.path
            status_code = getattr(response, 'status_code', 200)
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.info(f"Request metrics recorded: {method} {endpoint} - {status_code} - {duration:.3f}s")
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            method = request.method
            endpoint = request.url.path
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code="500"
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.error(f"Request error metrics recorded: {method} {endpoint} - 500 - {duration:.3f}s - {str(e)}")
            raise
        
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()

def track_tool_execution(tool_name: str):
    """Decorator to track tool execution metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Tool {tool_name} execution failed: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                
                TOOL_EXECUTION_COUNT.labels(
                    tool_name=tool_name,
                    status=status
                ).inc()
                
                TOOL_EXECUTION_DURATION.labels(
                    tool_name=tool_name
                ).observe(duration)
                
                logger.info(f"Tool execution metrics recorded: {tool_name} - {status} - {duration:.3f}s")
        
        return wrapper
    return decorator

def track_agent_invocation(agent_name: str):
    """Decorator to track agent invocation metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Agent {agent_name} invocation failed: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                
                AGENT_INVOCATION_COUNT.labels(
                    agent_name=agent_name,
                    status=status
                ).inc()
                
                AGENT_INVOCATION_DURATION.labels(
                    agent_name=agent_name
                ).observe(duration)
                
                logger.info(f"Agent invocation metrics recorded: {agent_name} - {status} - {duration:.3f}s")
        
        return wrapper
    return decorator

def track_copilotkit_request(agent: str = "unknown", action: str = "unknown"):
    """Decorator to track CopilotKit request metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"CopilotKit request failed: {agent} - {action} - {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                
                COPLOTKIT_REQUEST_COUNT.labels(
                    agent=agent,
                    action=action
                ).inc()
                
                COPLOTKIT_REQUEST_DURATION.labels(
                    agent=agent,
                    action=action
                ).observe(duration)
                
                logger.info(f"CopilotKit request metrics recorded: {agent} - {action} - {status} - {duration:.3f}s")
        
        return wrapper
    return decorator

async def update_system_metrics():
    """Update system metrics (memory, CPU)"""
    try:
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        MEMORY_USAGE.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        CPU_USAGE.set(cpu_percent)
        
    except ImportError:
        logger.warning("psutil not available for system metrics")
    except Exception as e:
        logger.error(f"Failed to update system metrics: {str(e)}")

def setup_metrics_endpoint(app):
    """Setup metrics endpoint for Prometheus scraping"""
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        # Update system metrics before serving
        await update_system_metrics()
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/metrics/health")
    async def metrics_health():
        """Metrics health check endpoint"""
        return {
            "status": "healthy",
            "service": "cep-machine-metrics",
            "metrics_available": True
        }

# Metrics collection task
async def metrics_collection_task():
    """Background task to collect metrics"""
    while True:
        try:
            await update_system_metrics()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Metrics collection error: {str(e)}")
            await asyncio.sleep(60)  # Wait longer on error
