"""
Optimized Database Queries for CEP Machine
Production-ready query optimization with indexes and efficient loading
"""

from sqlalchemy import select, text, Index, Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from backend.config.database import engine, Base

logger = logging.getLogger(__name__)

# Define Models for queries
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    content = Column(String, nullable=False)
    role = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolExecution(Base):
    __tablename__ = "tool_executions"
    
    id = Column(String, primary_key=True)
    tool_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    parameters = Column(String, nullable=True)
    result = Column(String, nullable=True)
    error = Column(String, nullable=True)
    execution_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Prospect(Base):
    __tablename__ = "prospects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    location = Column(String, nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, default="new")
    source = Column(String, nullable=True)
    converted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database Indexes
async def create_indexes():
    """Create database indexes for performance optimization"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON messages(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_tools_status ON tool_executions(status)",
        "CREATE INDEX IF NOT EXISTS idx_tools_tool_name ON tool_executions(tool_name)",
        "CREATE INDEX IF NOT EXISTS idx_tools_created_at ON tool_executions(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)",
        "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_created ON user_sessions(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_prospects_location ON prospects(location)",
        "CREATE INDEX IF NOT EXISTS idx_prospects_category ON prospects(category)",
        "CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status)",
        "CREATE INDEX IF NOT EXISTS idx_prospects_converted ON prospects(converted)",
        "CREATE INDEX IF NOT EXISTS idx_prospects_created_at ON prospects(created_at)"
    ]
    
    async with engine.begin() as conn:
        for idx in indexes:
            try:
                await conn.execute(text(idx))
                logger.info(f"Index created: {idx.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"Index creation skipped: {str(e)}")
    
    logger.info("Database indexes created successfully")

# Optimized Query Functions
async def get_messages_with_tools(session: AsyncSession, limit: int = 50) -> List[Message]:
    """Get messages with their tool executions using optimized loading"""
    stmt = select(Message).options(
        selectinload(Message.tool_executions)
    ).order_by(Message.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_messages_by_session(session: AsyncSession, session_id: str, limit: int = 100) -> List[Message]:
    """Get messages for a specific session"""
    stmt = select(Message).where(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_recent_tool_executions(session: AsyncSession, hours: int = 24, limit: int = 100) -> List[ToolExecution]:
    """Get recent tool executions within specified hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    stmt = select(ToolExecution).where(
        ToolExecution.created_at >= cutoff
    ).order_by(ToolExecution.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_tool_execution_stats(session: AsyncSession, hours: int = 24) -> Dict[str, Any]:
    """Get tool execution statistics"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Total executions
    total_stmt = select(ToolExecution).where(ToolExecution.created_at >= cutoff)
    total_result = await session.execute(total_stmt)
    total = len(total_result.scalars().all())
    
    # Successful executions
    success_stmt = select(ToolExecution).where(
        ToolExecution.created_at >= cutoff,
        ToolExecution.status == "success"
    )
    success_result = await session.execute(success_stmt)
    successful = len(success_result.scalars().all())
    
    # Failed executions
    failed_stmt = select(ToolExecution).where(
        ToolExecution.created_at >= cutoff,
        ToolExecution.status == "failed"
    )
    failed_result = await session.execute(failed_stmt)
    failed = len(failed_result.scalars().all())
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "period_hours": hours
    }

async def get_active_agents(session: AsyncSession) -> List[Agent]:
    """Get all active agents"""
    stmt = select(Agent).where(Agent.status == "active").order_by(Agent.name)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_prospects_by_location(session: AsyncSession, location: str, limit: int = 50) -> List[Prospect]:
    """Get prospects by location"""
    stmt = select(Prospect).where(
        Prospect.location.ilike(f"%{location}%")
    ).order_by(Prospect.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_prospects_by_category(session: AsyncSession, category: str, limit: int = 50) -> List[Prospect]:
    """Get prospects by category"""
    stmt = select(Prospect).where(
        Prospect.category.ilike(f"%{category}%")
    ).order_by(Prospect.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_unconverted_prospects(session: AsyncSession, limit: int = 100) -> List[Prospect]:
    """Get prospects that haven't been converted yet"""
    stmt = select(Prospect).where(
        Prospect.converted == False
    ).order_by(Prospect.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_conversion_stats(session: AsyncSession) -> Dict[str, Any]:
    """Get prospect conversion statistics"""
    # Total prospects
    total_stmt = select(Prospect)
    total_result = await session.execute(total_stmt)
    total = len(total_result.scalars().all())
    
    # Converted prospects
    converted_stmt = select(Prospect).where(Prospect.converted == True)
    converted_result = await session.execute(converted_stmt)
    converted = len(converted_result.scalars().all())
    
    return {
        "total_prospects": total,
        "converted": converted,
        "unconverted": total - converted,
        "conversion_rate": (converted / total * 100) if total > 0 else 0
    }

async def search_prospects(
    session: AsyncSession,
    location: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    converted: Optional[bool] = None,
    limit: int = 50
) -> List[Prospect]:
    """Search prospects with multiple filters"""
    stmt = select(Prospect)
    
    if location:
        stmt = stmt.where(Prospect.location.ilike(f"%{location}%"))
    if category:
        stmt = stmt.where(Prospect.category.ilike(f"%{category}%"))
    if status:
        stmt = stmt.where(Prospect.status == status)
    if converted is not None:
        stmt = stmt.where(Prospect.converted == converted)
    
    stmt = stmt.order_by(Prospect.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_active_sessions(session: AsyncSession, user_id: Optional[str] = None) -> List[UserSession]:
    """Get active user sessions"""
    stmt = select(UserSession).where(
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    )
    
    if user_id:
        stmt = stmt.where(UserSession.user_id == user_id)
    
    stmt = stmt.order_by(UserSession.created_at.desc())
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def cleanup_expired_sessions(session: AsyncSession) -> int:
    """Clean up expired sessions and return count of deleted sessions"""
    from sqlalchemy import delete
    
    stmt = delete(UserSession).where(
        UserSession.expires_at < datetime.utcnow()
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    deleted_count = result.rowcount
    logger.info(f"Cleaned up {deleted_count} expired sessions")
    return deleted_count
