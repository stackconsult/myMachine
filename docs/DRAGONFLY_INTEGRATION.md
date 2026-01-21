# DragonflyDB Integration Guide

**Date:** January 21, 2026  
**Purpose:** Replace Redis with DragonflyDB for CEP Machine

## Overview

DragonflyDB is a modern in-memory datastore compatible with Redis protocol, delivering 25x more throughput while using 80% less memory.

## Why DragonflyDB?

### Performance Benefits
- **25x more throughput** than Redis
- **80% less memory** usage
- **100% Redis API compatible** - drop-in replacement
- **Multithreaded architecture** - utilizes all CPU cores
- **Flash storage integration** - larger than RAM datasets

### Technical Advantages
- **No code changes required** - Redis client libraries work
- **Open source** - BSL 1.1 → Apache 2.0 license
- **Single binary deployment** - easy setup
- **Active development** - modern codebase

## Integration Requirements

### 1. Installation & Setup

#### Docker Deployment (Recommended)
```bash
# Pull DragonflyDB image
docker pull dragonflydb/dragonfly

# Run container
docker run -d \
  --name dragonfly \
  -p 6379:6379 \
  -v dragonfly-data:/data \
  dragonflydb/dragonfly
```

#### Binary Installation
```bash
# Download binary
curl -L https://github.com/dragonflydb/dragonfly/releases/latest/download/dragonfly-linux-amd64 -o dragonfly
chmod +x dragonfly

# Run
./dragonfly --port 6379
```

### 2. Configuration Changes

#### Current Redis Configuration
```python
# cep_machine/core/cache.py (not yet implemented)
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

#### DragonflyDB Configuration (Same)
```python
# No changes needed - DragonflyDB is Redis compatible
import redis
dragonfly_client = redis.Redis(host='localhost', port=6379, db=0)
```

### 3. Environment Variables

```bash
# .env file
CACHE_HOST=localhost
CACHE_PORT=6379
CACHE_TYPE=dragonfly
# Optional: Dragonfly specific settings
DRAGONFLY_MAX_MEMORY=2gb
DRAGONFLY_THREADS=auto
```

## Implementation Plan

### Step 1: Cache Layer Implementation
Create cache abstraction layer:
```python
# cep_machine/core/cache.py
from abc import ABC, abstractmethod
import redis
import os

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None):
        pass

class DragonflyCache(CacheInterface):
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('CACHE_HOST', 'localhost'),
            port=int(os.getenv('CACHE_PORT', 6379)),
            decode_responses=True
        )
    
    async def get(self, key: str):
        return self.client.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None):
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)
```

### Step 2: Use Cases in CEP Machine

#### 1. Prospect Research Caching
```python
# Cache prospect search results
cache_key = f"prospects:{location}:{category}"
cached = await cache.get(cache_key)
if not cached:
    prospects = await search_businesses(location, category)
    await cache.set(cache_key, prospects, ttl=3600)  # 1 hour
```

#### 2. Pitch Generation Cache
```python
# Cache generated pitches
cache_key = f"pitch:{prospect_id}:{template}"
cached = await cache.get(cache_key)
if not cached:
    pitch = await generate_pitch(prospect, template)
    await cache.set(cache_key, pitch, ttl=86400)  # 24 hours
```

#### 3. GBP Score Cache
```python
# Cache GBP analysis results
cache_key = f"gbp:{business_id}"
cached = await cache.get(cache_key)
if not cached:
    analysis = await analyze_gbp(business_id)
    await cache.set(cache_key, analysis, ttl=1800)  # 30 minutes
```

#### 4. Session Storage
```python
# Store user sessions
session_id = "session_123"
session_data = {"user": "kirtis", "role": "admin"}
await cache.set(f"session:{session_id}", session_data, ttl=7200)
```

#### 5. Rate Limiting
```python
# Implement rate limiting
client_ip = "192.168.1.1"
key = f"rate_limit:{client_ip}"
requests = await cache.get(key) or 0
if requests > 100:
    raise RateLimitError()
await cache.set(key, requests + 1, ttl=60)
```

### Step 3: Performance Optimizations

#### Connection Pooling
```python
# Configure connection pool
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=20,
    retry_on_timeout=True
)
client = redis.Redis(connection_pool=pool)
```

#### Batch Operations
```python
# Use pipelines for bulk operations
pipe = client.pipeline()
for key, value in data.items():
    pipe.set(key, value)
pipe.execute()
```

## Migration Strategy

### Phase 1: Setup DragonflyDB
1. Deploy DragonflyDB instance
2. Verify Redis compatibility
3. Test basic operations

### Phase 2: Implement Cache Layer
1. Create cache abstraction
2. Implement DragonflyCache
3. Add to existing layers

### Phase 3: Deploy Caching
1. Add caching to Layer 1 (Prospects)
2. Add caching to Layer 2 (Pitches)
3. Add caching to Layer 6 (GBP)
4. Add session storage
5. Add rate limiting

### Phase 4: Monitor & Optimize
1. Monitor hit ratios
2. Optimize TTL values
3. Tune memory usage

## Performance Expectations

### Baseline (No Cache)
- Prospect search: 2-3 seconds
- Pitch generation: 1-2 seconds
- GBP analysis: 5-10 seconds

### With DragonflyDB Cache
- Prospect search: 50-100ms (cached)
- Pitch generation: 10-50ms (cached)
- GBP analysis: 100-200ms (cached)

### Memory Requirements
- Base application: ~500MB
- DragonflyDB: 1-2GB (depending on cache size)
- Total: <3GB (vs 5GB+ with Redis)

## Monitoring

### Key Metrics
- **Hit Ratio**: % of requests served from cache
- **Memory Usage**: Current memory consumption
- **Ops/sec**: Operations per second
- **Latency**: Response times

### Monitoring Commands
```bash
# DragonflyDB info
redis-cli INFO memory
redis-cli INFO stats
redis-cli INFO server

# Monitor real-time
redis-cli MONITOR
```

## Troubleshooting

### Common Issues
1. **Connection Refused**: Check DragonflyDB is running
2. **Memory Full**: Configure maxmemory policy
3. **Slow Queries**: Check for large values

### Debug Commands
```bash
# Check connection
redis-cli PING

# Check memory
redis-cli INFO memory | grep used_memory

# Check slow log
redis-cli SLOWLOG GET 10
```

## Configuration File

```yaml
# config/dragonfly.yaml
dragonfly:
  port: 6379
  maxmemory: 2gb
  maxmemory_policy: allkeys-lru
  save_interval: 300
  appendonly: yes
  appendfsync: everysec
  threads: auto
```

## Security Considerations

### Production Setup
```bash
# Run with authentication
./dragonfly --requirepass your_password

# Network security
./dragonfly --bind 127.0.0.1

# TLS (if needed)
./dragonfly --tls-cert-file cert.pem --tls-key-file key.pem
```

## Cost Analysis

### Self-Hosted
- **Hardware**: $20-50/month (VPS with 4GB RAM)
- **Maintenance**: Minimal
- **Total**: $20-50/month

### Cloud Options
- **AWS EC2**: $30-100/month
- **Google Cloud**: $25-80/month
- **DigitalOcean**: $20-60/month

## Conclusion

DragonflyDB provides superior performance with minimal implementation effort. As a Redis-compatible drop-in replacement, it requires no code changes while delivering significant performance improvements.

**Next Steps:**
1. Deploy DragonflyDB
2. Implement cache abstraction layer
3. Add caching to critical paths
4. Monitor and optimize

---

*DragonflyDB: 25x performance, 80% less memory, zero code changes*
