"""
CEP Database - SQLite Storage Layer

Tables:
- layers: Tracks the 9 business layers
- research_logs: Stores research citations
- coherence_metrics: Tracks Φ_sync over time
- events: Container events
- architectures: Layer architecture documents
- test_results: Testing engine results
"""

import os
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class Database:
    """SQLite database for CEP Machine."""
    
    def __init__(self, db_path: str = "./data/cep_machine.db"):
        self.db_path = db_path
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Layers table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS layers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    output_file TEXT,
                    phi_contribution REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Research logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    source_url TEXT,
                    source_title TEXT,
                    summary TEXT,
                    citations TEXT,
                    layer_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (layer_id) REFERENCES layers(id)
                )
            """)
            
            # Coherence metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS coherence_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phi_sync REAL NOT NULL,
                    sales_health REAL,
                    ops_health REAL,
                    finance_health REAL,
                    coupling_factor REAL,
                    recommendation TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Events table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    container TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Architectures table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS architectures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer_id INTEGER,
                    architecture_json TEXT NOT NULL,
                    validated INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (layer_id) REFERENCES layers(id)
                )
            """)
            
            # Test results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer_id INTEGER,
                    test_name TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    duration_ms INTEGER,
                    error_message TEXT,
                    screenshot_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (layer_id) REFERENCES layers(id)
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_research_layer ON research_logs(layer_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_events_container ON events(container)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_coherence_time ON coherence_metrics(recorded_at)")
            
            await db.commit()
            
            # Seed the 9 layers if not exists
            await self._seed_layers(db)
    
    async def _seed_layers(self, db: aiosqlite.Connection) -> None:
        """Seed the 9 business layers."""
        layers = [
            (1, "Prospect Research", "Find dental practices with no GBP", "prospector.py"),
            (2, "Pitch Generator", "Write personalized emails referencing missing GBP features", "pitch_gen.py"),
            (3, "Outreach Engine", "Send pitches via Gmail API", "outreach.py"),
            (4, "Booking Handler", "Webhook listener for Calendly that updates CRM", "booking_handler.py"),
            (5, "Onboarding Flow", "Create Google Drive folder and Trello board for new clients", "onboarding.py"),
            (6, "GBP Optimizer", "Core service agent that posts updates to GBP", "gbp_optimizer.py"),
            (7, "Reporting Engine", "Compile GBP insights into PDF report", "reporter.py"),
            (8, "Finance Tracker", "Stripe webhook listener for MRR and Finance Container", "finance_tracker.py"),
            (9, "Self-Learning", "Loop that reads outcomes and updates prompts for Layers 1 & 2", "feedback_loop.py"),
        ]
        
        for layer_id, name, description, output_file in layers:
            await db.execute("""
                INSERT OR IGNORE INTO layers (id, name, description, output_file)
                VALUES (?, ?, ?, ?)
            """, (layer_id, name, description, output_file))
        
        await db.commit()
    
    # Layer operations
    async def get_layer(self, layer_id: int) -> Optional[Dict[str, Any]]:
        """Get a layer by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM layers WHERE id = ?", (layer_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_all_layers(self) -> List[Dict[str, Any]]:
        """Get all layers."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM layers ORDER BY id") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def update_layer_status(
        self,
        layer_id: int,
        status: str,
        phi_contribution: Optional[float] = None,
    ) -> None:
        """Update a layer's status."""
        async with aiosqlite.connect(self.db_path) as db:
            if status == "completed":
                await db.execute("""
                    UPDATE layers 
                    SET status = ?, completed_at = ?, phi_contribution = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), phi_contribution or 0.0, layer_id))
            else:
                await db.execute(
                    "UPDATE layers SET status = ? WHERE id = ?",
                    (status, layer_id)
                )
            await db.commit()
    
    # Research operations
    async def add_research_log(
        self,
        query: str,
        source_url: str,
        source_title: str,
        summary: str,
        citations: str,
        layer_id: Optional[int] = None,
    ) -> int:
        """Add a research log entry."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO research_logs (query, source_url, source_title, summary, citations, layer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (query, source_url, source_title, summary, citations, layer_id))
            await db.commit()
            return cursor.lastrowid
    
    async def get_research_for_layer(self, layer_id: int) -> List[Dict[str, Any]]:
        """Get all research logs for a layer."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM research_logs WHERE layer_id = ? ORDER BY created_at DESC",
                (layer_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # Coherence operations
    async def record_coherence(
        self,
        phi_sync: float,
        sales_health: float,
        ops_health: float,
        finance_health: float,
        coupling_factor: float,
        recommendation: str,
    ) -> None:
        """Record a coherence metric snapshot."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO coherence_metrics 
                (phi_sync, sales_health, ops_health, finance_health, coupling_factor, recommendation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (phi_sync, sales_health, ops_health, finance_health, coupling_factor, recommendation))
            await db.commit()
    
    async def get_coherence_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get coherence history."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM coherence_metrics ORDER BY recorded_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_latest_coherence(self) -> Optional[Dict[str, Any]]:
        """Get the latest coherence reading."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM coherence_metrics ORDER BY recorded_at DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # Event operations
    async def record_event(
        self,
        container: str,
        event_type: str,
        data: str,
    ) -> None:
        """Record a container event."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO events (container, event_type, data)
                VALUES (?, ?, ?)
            """, (container, event_type, data))
            await db.commit()
    
    # Architecture operations
    async def save_architecture(
        self,
        layer_id: int,
        architecture_json: str,
        validated: bool = False,
    ) -> int:
        """Save a layer architecture."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO architectures (layer_id, architecture_json, validated)
                VALUES (?, ?, ?)
            """, (layer_id, architecture_json, 1 if validated else 0))
            await db.commit()
            return cursor.lastrowid
    
    # Test result operations
    async def save_test_result(
        self,
        layer_id: int,
        test_name: str,
        passed: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> None:
        """Save a test result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO test_results 
                (layer_id, test_name, passed, duration_ms, error_message, screenshot_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (layer_id, test_name, 1 if passed else 0, duration_ms, error_message, screenshot_path))
            await db.commit()
    
    async def get_test_results_for_layer(self, layer_id: int) -> List[Dict[str, Any]]:
        """Get test results for a layer."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM test_results WHERE layer_id = ? ORDER BY created_at DESC",
                (layer_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
