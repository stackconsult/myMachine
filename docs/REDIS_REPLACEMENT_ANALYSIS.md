# Redis Replacement Analysis

**Date:** January 21, 2026  
**Purpose:** Evaluate alternatives to Redis for CEP Machine

## Current Redis Requirements

Based on the production audit, Redis was planned for:
1. **Caching layer** - Improve database performance
2. **Session storage** - User state management
3. **Rate limiting** - API abuse prevention
4. **Message queue** - Background job processing
5. **Real-time data** - Live updates

## Supabase Free Tier Capabilities

### Database & Storage
- **Database:** 500MB PostgreSQL
- **File Storage:** 1GB
- **Egress:** 50MB/day
- **MAUs:** 10,000 monthly active users

### Real-time Features
- **Concurrent Connections:** 200 (free tier)
- **Messages:** Not explicitly limited (based on connections)
- **Channels:** Not explicitly limited
- **WebSockets:** Built-in via PostgreSQL triggers

### Edge Functions
- **Invocations:** 1,000/day
- **Concurrency:** 2 executions/second
- **Runtime:** Deno/TypeScript

## Can Supabase Replace Redis?

### 1. Caching Layer

**Supabase Approach:** PostgreSQL with connection pooling
```python
# Instead of Redis cache
supabase.table('cache').select('*').eq('key', cache_key)

# With connection pooling (pgBouncer)
# Supabase automatically handles connection pooling
```

**Limitations:**
- ❌ Not in-memory (disk-based)
- ❌ Higher latency than Redis
- ❌ No built-in TTL (Time To Live)
- ❌ No eviction policies

**Verdict:** Partial replacement - Works for simple caching but slower

### 2. Session Storage

**Supabase Approach:** Database table + Real-time subscriptions
```python
# Store sessions in database
supabase.table('sessions').insert({
    'session_id': sid,
    'user_data': data,
    'expires_at': expiry
})

# Real-time updates for session changes
supabase.channel('sessions').on_postgres_changes(
    table='sessions',
    event='*',
    callback=handle_session_change
).subscribe()
```

**Limitations:**
- ❌ Higher latency than Redis
- ❌ No automatic session expiration
- ✅ Persistent across restarts
- ✅ Real-time updates

**Verdict:** Viable replacement with trade-offs

### 3. Rate Limiting

**Supabase Approach:** Database tracking + Edge Functions
```typescript
// Edge Function for rate limiting
// supabase/functions/rate-limit/index.ts
export default async function (req: Request) {
  const client = req.headers.get('client-id')
  const now = new Date()
  
  // Check rate limit in database
  const { data, error } = await supabase
    .from('rate_limits')
    .select('*')
    .eq('client', client)
    .gte('created_at', new Date(now.getTime() - 60000))
  
  if (data && data.length >= 100) {
    return new Response('Rate limit exceeded', { status: 429 })
  }
  
  // Record this request
  await supabase.from('rate_limits').insert({
    client,
    created_at: now
  })
  
  return new Response('OK')
}
```

**Limitations:**
- ❌ Higher latency than Redis
- ❌ Database writes for every request
- ✅ Persistent tracking
- ✅ Can analyze patterns later

**Verdict:** Works but less efficient than Redis

### 4. Message Queue

**Supabase Approach:** Real-time subscriptions + Database
```python
# Producer
supabase.table('messages').insert({
    'queue': 'background_jobs',
    'payload': job_data,
    'status': 'pending'
})

# Consumer
supabase.channel('background_jobs').on_postgres_changes(
    table='messages',
    event='INSERT',
    filter='queue=eq.background_jobs',
    callback=process_job
).subscribe()
```

**Limitations:**
- ❌ No guaranteed delivery
- ❌ No dead letter queue
- ❌ Limited throughput
- ✅ Real-time processing
- ✅ Persistent storage

**Verdict:** Basic queue functionality, not production-grade

### 5. Real-time Data

**Supabase Approach:** Built-in real-time subscriptions
```python
# Real-time Φ_sync updates
supabase.channel('phi_sync').on_postgres_changes(
    table='coherence_metrics',
    event='UPDATE',
    callback=lambda payload: update_dashboard(payload.new)
).subscribe()
```

**Advantages:**
- ✅ Native real-time support
- ✅ WebSocket connections
- ✅ Tied to database changes
- ✅ 200 concurrent connections (free tier)

**Verdict:** Excellent replacement for real-time features

## Alternative Solutions

### 1. PostgreSQL Extensions

**pg_stat_statements** - Query caching
```sql
-- Enable query performance tracking
CREATE EXTENSION pg_stat_statements;

-- Cache frequently used queries
SELECT query, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

**Materialized Views** - Pre-computed results
```sql
-- Create cached view of prospects
CREATE MATERIALIZED VIEW prospect_cache AS
SELECT * FROM prospects WHERE gbp_score < 70;

-- Refresh periodically
REFRESH MATERIALIZED VIEW prospect_cache;
```

### 2. In-Memory PostgreSQL

**Configuration:**
```postgresql
# postgresql.conf
shared_buffers = 256MB          # Use more RAM
effective_cache_size = 1GB      # Assume OS cache
work_mem = 4MB                   # Sort memory
maintenance_work_mem = 64MB      # Index building
```

### 3. Application-Level Caching

**Python LRU Cache:**
```python
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def get_prospect_data(business_id: str):
    # Cache for 1000 items
    # Automatically evicts oldest
    pass

# TTL cache implementation
class TTLCache:
    def __init__(self, ttl_seconds=300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
```

## Recommendations

### For CEP Machine

1. **Use Supabase for:**
   - ✅ Real-time subscriptions (Φ_sync updates)
   - ✅ Session storage (persistent)
   - ✅ Simple caching (with limitations)

2. **Keep Redis for:**
   - High-performance caching
   - Rate limiting (if needed)
   - Message queuing (background jobs)

3. **Alternative approach:**
   - Use PostgreSQL connection pooling
   - Implement application-level caching
   - Use Supabase real-time for live updates

### Cost Comparison

| Solution | Cost | Pros | Cons |
|----------|------|------|------|
| Redis Cloud | $5-20/month | Fast, feature-rich | Additional service |
| Supabase Only | $0-25/month | All-in-one | Slower for caching |
| PostgreSQL Only | $0-25/month | Simple, fast | No real-time |
| Hybrid | $5-30/month | Best of both | More complex |

### Final Verdict

**Supabase can partially replace Redis** but with trade-offs:

- **Real-time features:** ✅ Excellent replacement
- **Session storage:** ✅ Viable with persistence
- **Simple caching:** ⚠️ Works but slower
- **Rate limiting:** ⚠️ Possible but inefficient
- **Message queuing:** ❌ Not recommended

**Recommendation:** Use Supabase for real-time and session storage, keep Redis for high-performance caching and rate limiting if needed. For a personal tool, Supabase alone may be sufficient.

---

*Analysis based on Supabase free tier and Redis Cloud pricing as of January 2026*
