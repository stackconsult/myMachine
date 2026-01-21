"""
Monitoring and metrics collection for CEP Machine
Tracks cache performance, system health, and usage statistics
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

from .cache import get_cache

logger = logging.getLogger(__name__)

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hit_rate: float = 0.0
    total_requests: int = 0
    hits: int = 0
    misses: int = 0
    memory_usage: str = "0B"
    connected_clients: int = 0
    ops_per_second: float = 0.0
    
@dataclass
class LayerMetrics:
    """Layer-specific metrics"""
    layer_name: str
    total_executions: int = 0
    avg_execution_time: float = 0.0
    cache_hit_rate: float = 0.0
    errors: int = 0
    last_execution: Optional[datetime] = None
    
@dataclass
class SystemMetrics:
    """Overall system metrics"""
    uptime_seconds: float = 0.0
    total_requests: int = 0
    active_sessions: int = 0
    phi_sync: float = 0.0
    error_rate: float = 0.0
    memory_usage_mb: float = 0.0

class MonitoringService:
    """Central monitoring service for CEP Machine"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self._cache = None
        self._layer_metrics: Dict[str, LayerMetrics] = {}
        self._system_metrics = SystemMetrics()
        
    async def get_cache(self):
        """Get cache instance"""
        if not self._cache:
            self._cache = await get_cache()
        return self._cache
    
    async def get_cache_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics"""
        cache = await self.get_cache()
        info = await cache.get_info()
        
        return CacheMetrics(
            hit_rate=info.get('hit_rate', 0.0),
            total_requests=info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0),
            hits=info.get('keyspace_hits', 0),
            misses=info.get('keyspace_misses', 0),
            memory_usage=info.get('used_memory_human', '0B'),
            connected_clients=info.get('connected_clients', 0),
            ops_per_second=info.get('instantaneous_ops_per_sec', 0.0)
        )
    
    async def get_layer_metrics(self, layer_name: str) -> LayerMetrics:
        """Get metrics for a specific layer"""
        if layer_name not in self._layer_metrics:
            self._layer_metrics[layer_name] = LayerMetrics(layer_name=layer_name)
        
        # Try to get from cache
        cache = await self.get_cache()
        cache_key = f"metrics:layer:{layer_name}"
        cached_metrics = await cache.get(cache_key)
        
        if cached_metrics:
            cached_metrics['last_execution'] = datetime.fromisoformat(
                cached_metrics.get('last_execution', datetime.utcnow().isoformat())
            )
            return LayerMetrics(**cached_metrics)
        
        return self._layer_metrics[layer_name]
    
    async def record_layer_execution(
        self,
        layer_name: str,
        execution_time: float,
        cache_hit: bool = False,
        error: bool = False
    ):
        """Record layer execution metrics"""
        # Update in-memory metrics
        if layer_name not in self._layer_metrics:
            self._layer_metrics[layer_name] = LayerMetrics(layer_name=layer_name)
        
        metrics = self._layer_metrics[layer_name]
        metrics.total_executions += 1
        metrics.last_execution = datetime.utcnow()
        
        if error:
            metrics.errors += 1
        
        # Update average execution time
        if metrics.total_executions == 1:
            metrics.avg_execution_time = execution_time
        else:
            metrics.avg_execution_time = (
                (metrics.avg_execution_time * (metrics.total_executions - 1) + execution_time) /
                metrics.total_executions
            )
        
        # Update cache hit rate
        if cache_hit:
            hits = getattr(metrics, '_cache_hits', 0) + 1
            setattr(metrics, '_cache_hits', hits)
        else:
            misses = getattr(metrics, '_cache_misses', 0) + 1
            setattr(metrics, '_cache_misses', misses)
        
        hits = getattr(metrics, '_cache_hits', 0)
        misses = getattr(metrics, '_cache_misses', 0)
        total = hits + misses
        metrics.cache_hit_rate = (hits / total * 100) if total > 0 else 0.0
        
        # Store in cache
        cache = await self.get_cache()
        cache_key = f"metrics:layer:{layer_name}"
        await cache.set(cache_key, asdict(metrics), ttl=3600)  # 1 hour
        
        logger.debug(f"Recorded execution for {layer_name}: {execution_time:.3f}s")
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics"""
        # Calculate uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get cache metrics
        cache_metrics = await self.get_cache_metrics()
        
        # Get active sessions (simplified)
        cache = await self.get_cache()
        active_sessions = 0  # Would need to scan session keys
        
        return SystemMetrics(
            uptime_seconds=uptime,
            total_requests=cache_metrics.total_requests,
            active_sessions=active_sessions,
            phi_sync=0.88,  # Would get from system state
            error_rate=self._calculate_error_rate(),
            memory_usage_mb=self._get_memory_usage()
        )
    
    def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        total_executions = sum(m.total_executions for m in self._layer_metrics.values())
        total_errors = sum(m.errors for m in self._layer_metrics.values())
        
        if total_executions == 0:
            return 0.0
        
        return (total_errors / total_executions) * 100
    
    def _get_memory_usage(self) -> float:
        """Get memory usage in MB (simplified)"""
        import psutil
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        cache_metrics = await self.get_cache_metrics()
        system_metrics = await self.get_system_metrics()
        
        # Get all layer metrics
        layer_data = {}
        for layer_name in self._layer_metrics:
            layer_metrics = await self.get_layer_metrics(layer_name)
            layer_data[layer_name] = asdict(layer_metrics)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache": asdict(cache_metrics),
            "system": asdict(system_metrics),
            "layers": layer_data,
            "alerts": await self._get_active_alerts()
        }
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts = []
        
        # Check cache hit rate
        cache_metrics = await self.get_cache_metrics()
        if cache_metrics.hit_rate < 50:
            alerts.append({
                "type": "warning",
                "message": f"Low cache hit rate: {cache_metrics.hit_rate:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check error rate
        error_rate = self._calculate_error_rate()
        if error_rate > 10:
            alerts.append({
                "type": "error",
                "message": f"High error rate: {error_rate:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check memory usage
        memory_mb = self._get_memory_usage()
        if memory_mb > 1000:  # > 1GB
            alerts.append({
                "type": "warning",
                "message": f"High memory usage: {memory_mb:.1f}MB",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        data = await self.get_dashboard_data()
        
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "prometheus":
            return self._to_prometheus_format(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _to_prometheus_format(self, data: Dict[str, Any]) -> str:
        """Convert metrics to Prometheus format"""
        lines = []
        
        # Cache metrics
        cache = data['cache']
        lines.append(f"cep_cache_hit_rate {cache['hit_rate']}")
        lines.append(f"cep_cache_total_requests {cache['total_requests']}")
        lines.append(f"cep_cache_hits {cache['hits']}")
        lines.append(f"cep_cache_misses {cache['misses']}")
        lines.append(f"cep_cache_connected_clients {cache['connected_clients']}")
        lines.append(f"cep_cache_ops_per_second {cache['ops_per_second']}")
        
        # System metrics
        system = data['system']
        lines.append(f"cep_system_uptime_seconds {system['uptime_seconds']}")
        lines.append(f"cep_system_total_requests {system['total_requests']}")
        lines.append(f"cep_system_active_sessions {system['active_sessions']}")
        lines.append(f"cep_system_phi_sync {system['phi_sync']}")
        lines.append(f"cep_system_error_rate {system['error_rate']}")
        lines.append(f"cep_system_memory_usage_mb {system['memory_usage_mb']}")
        
        # Layer metrics
        for layer_name, layer in data['layers'].items():
            safe_name = layer_name.replace('-', '_').replace(' ', '_')
            lines.append(f'cep_layer_executions_total{{layer="{layer_name}"}} {layer["total_executions"]}')
            lines.append(f'cep_layer_execution_time_seconds{{layer="{layer_name}"}} {layer["avg_execution_time"]}')
            lines.append(f'cep_layer_cache_hit_rate{{layer="{layer_name}"}} {layer["cache_hit_rate"]}')
            lines.append(f'cep_layer_errors_total{{layer="{layer_name}"}} {layer["errors"]}')
        
        return '\n'.join(lines)

# Global monitoring instance
monitoring = MonitoringService()

# Decorator for automatic metrics collection
def monitor_execution(layer_name: str):
    """Decorator to automatically monitor layer execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            cache_hit = False
            error = False
            
            try:
                # Check if result came from cache
                result = await func(*args, **kwargs)
                
                # Try to detect cache hit (this is a simplified check)
                if hasattr(result, '_from_cache') and result._from_cache:
                    cache_hit = True
                
                return result
                
            except Exception as e:
                error = True
                logger.error(f"Error in {layer_name}: {e}")
                raise
            
            finally:
                execution_time = time.time() - start_time
                await monitoring.record_layer_execution(
                    layer_name, execution_time, cache_hit, error
                )
        
        return wrapper
    return decorator
