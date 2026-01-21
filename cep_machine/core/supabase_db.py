"""
Supabase database adapter for CEP Machine
Replaces SQLite with PostgreSQL for production
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    """Supabase database implementation"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not all([self.url, self.anon_key, self.service_key]):
            raise ValueError("Missing required Supabase environment variables")
        
        # Use service key for admin operations
        self.client: Client = create_client(self.url, self.service_key)
        self._initialized = False
    
    async def initialize(self):
        """Initialize database with required tables"""
        if self._initialized:
            return
        
        logger.info("Initializing Supabase database...")
        
        # Create tables if they don't exist
        await self._create_tables()
        
        # Enable real-time subscriptions
        await self._enable_realtime()
        
        self._initialized = True
        logger.info("✅ Supabase database initialized")
    
    async def _create_tables(self):
        """Create required tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS layers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                container TEXT NOT NULL,
                description TEXT,
                output_file TEXT,
                phi_contribution FLOAT DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS layer_results (
                id SERIAL PRIMARY KEY,
                layer_id INTEGER REFERENCES layers(id) ON DELETE CASCADE,
                execution_id UUID DEFAULT gen_random_uuid(),
                status TEXT NOT NULL,
                result_data JSONB,
                error_message TEXT,
                phi_contribution FLOAT DEFAULT 0.0,
                execution_time_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS prospects (
                id SERIAL PRIMARY KEY,
                business_name TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT,
                phone TEXT,
                website TEXT,
                email TEXT,
                address TEXT,
                gbp_score FLOAT DEFAULT 0.0,
                prospect_score FLOAT DEFAULT 0.0,
                status TEXT DEFAULT 'new',
                source TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS pitches (
                id SERIAL PRIMARY KEY,
                prospect_id INTEGER REFERENCES prospects(id) ON DELETE CASCADE,
                channel TEXT NOT NULL,
                subject TEXT,
                body TEXT NOT NULL,
                confidence_score FLOAT DEFAULT 0.0,
                template TEXT,
                status TEXT DEFAULT 'draft',
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS outreach_sequences (
                id SERIAL PRIMARY KEY,
                prospect_id INTEGER REFERENCES prospects(id) ON DELETE CASCADE,
                sequence_data JSONB NOT NULL,
                status TEXT DEFAULT 'active',
                next_step TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS coherence_metrics (
                id SERIAL PRIMARY KEY,
                phi_sync FLOAT NOT NULL,
                milestone TEXT NOT NULL,
                status TEXT NOT NULL,
                details JSONB,
                measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT,
                user_type TEXT DEFAULT 'anonymous',
                session_data JSONB,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                layer_id INTEGER REFERENCES layers(id) ON DELETE CASCADE,
                report_type TEXT NOT NULL,
                report_data JSONB NOT NULL,
                file_path TEXT,
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS financial_transactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                type TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'pending',
                description TEXT,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ]
        
        for table_sql in tables:
            try:
                await self.client.rpc('exec_sql', {'sql': table_sql})
                logger.info(f"Created table: {table_sql.split()[2] if 'CREATE TABLE' in table_sql else 'Unknown'}")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.error(f"Error creating table: {e}")
    
    async def _enable_realtime(self):
        """Enable real-time subscriptions"""
        try:
            # Enable RLS (Row Level Security)
            await self.client.rpc('exec_sql', {'sql': 'ALTER TABLE layers ENABLE ROW LEVEL SECURITY;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER TABLE layer_results ENABLE ROW LEVEL SECURITY;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER TABLE prospects ENABLE ROW LEVEL SECURITY;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER TABLE coherence_metrics ENABLE ROW LEVEL SECURITY;'})
            
            # Add to publication
            await self.client.rpc('exec_sql', {'sql': 'ALTER PUBLICATION supabase_realtime ADD TABLE layers;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER PUBLICATION supabase_realtime ADD TABLE layer_results;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER PUBLICATION supabase_realtime ADD TABLE prospects;'})
            await self.client.rpc('exec_sql', {'sql': 'ALTER PUBLICATION supabase_realtime ADD TABLE coherence_metrics;'})
            
            logger.info("✅ Real-time subscriptions enabled")
        except Exception as e:
            logger.warning(f"Real-time setup warning: {e}")
    
    async def get_layer(self, layer_id: int) -> Optional[Dict[str, Any]]:
        """Get layer by ID"""
        try:
            response = self.client.table('layers').select('*').eq('id', layer_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting layer {layer_id}: {e}")
            return None
    
    async def get_all_layers(self) -> List[Dict[str, Any]]:
        """Get all layers"""
        try:
            response = self.client.table('layers').select('*').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting layers: {e}")
            return []
    
    async def save_layer_result(self, layer_id: int, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save layer execution result"""
        try:
            response = self.client.table('layer_results').insert({
                'layer_id': layer_id,
                'status': result_data.get('status', 'completed'),
                'result_data': result_data.get('data'),
                'error_message': result_data.get('error'),
                'phi_contribution': result_data.get('phi_contribution', 0.0),
                'execution_time_ms': result_data.get('execution_time_ms'),
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving layer result: {e}")
            return {}
    
    async def get_prospects(self, location: str = None, category: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get prospects with optional filters"""
        try:
            query = self.client.table('prospects').select('*')
            
            if location:
                query = query.ilike('location', location)
            if category:
                query = query.ilike('category', category)
            
            query = query.limit(limit)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting prospects: {e}")
            return []
    
    async def save_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update prospect"""
        try:
            if 'id' in prospect_data:
                # Update existing
                response = self.client.table('prospects').update(prospect_data).eq('id', prospect_data['id']).execute()
            else:
                # Create new
                response = self.client.table('prospects').insert(prospect_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving prospect: {e}")
            return {}
    
    async def save_pitch(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update pitch"""
        try:
            if 'id' in pitch_data:
                response = self.client.table('pitches').update(pitch_data).eq('id', pitch_data['id']).execute()
            else:
                response = self.client.table('pitches').insert(pitch_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving pitch: {e}")
            return {}
    
    async def update_coherence_metrics(self, phi_sync: float, milestone: str, status: str, details: Dict[str, Any] = None):
        """Update coherence metrics"""
        try:
            await self.client.table('coherence_metrics').insert({
                'phi_sync': phi_sync,
                'milestone': milestone,
                'status': status,
                'details': details or {}
            }).execute()
            logger.info(f"Updated coherence metrics: Φ_sync={phi_sync}, milestone={milestone}")
        except Exception as e:
            logger.error(f"Error updating coherence metrics: {e}")
    
    async def get_latest_coherence(self) -> Optional[Dict[str, Any]]:
        """Get latest coherence metrics"""
        try:
            response = self.client.table('coherence_metrics').select('*').order('measured_at', desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting coherence metrics: {e}")
            return None
    
    async def subscribe_to_coherence(self, callback):
        """Subscribe to real-time coherence updates"""
        try:
            return self.client.channel('coherence_metrics').on_postgres_changes(
                event='*',
                callback=callback
            ).subscribe()
        except Exception as e:
            logger.error(f"Error subscribing to coherence: {e}")
            return None
    
    async def close(self):
        """Close database connection"""
        # Supabase client doesn't need explicit closing
        pass

# Global instance
_db_instance: Optional[SupabaseDatabase] = None

async def get_database() -> SupabaseDatabase:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDatabase()
        await _db_instance.initialize()
    return _db_instance
