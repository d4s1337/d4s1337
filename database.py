"""Database operations for Discord Mesai Bot."""

import aiosqlite
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from config import Config

class Database:
    """Database manager for the mesai bot."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_db_directory()
    
    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(Config.BACKUP_DIRECTORY, exist_ok=True)
    
    async def init_db(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript('''
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    daily_goal_minutes INTEGER DEFAULT 480,  -- 8 hours default
                    weekly_goal_minutes INTEGER DEFAULT 2400, -- 40 hours default
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Work sessions table
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    auto_ended BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
                
                -- Weekly stats table
                CREATE TABLE IF NOT EXISTS weekly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    week_start DATE NOT NULL,
                    total_minutes INTEGER DEFAULT 0,
                    sessions_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, week_start)
                );
                
                -- Monthly stats table
                CREATE TABLE IF NOT EXISTS monthly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    month_start DATE NOT NULL,
                    total_minutes INTEGER DEFAULT 0,
                    sessions_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, month_start)
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_work_sessions_user_id ON work_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_work_sessions_start_time ON work_sessions(start_time);
                CREATE INDEX IF NOT EXISTS idx_work_sessions_active ON work_sessions(is_active);
                CREATE INDEX IF NOT EXISTS idx_weekly_stats_user_week ON weekly_stats(user_id, week_start);
                CREATE INDEX IF NOT EXISTS idx_monthly_stats_user_month ON monthly_stats(user_id, month_start);
            ''')
            await db.commit()
    
    async def get_or_create_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """Get user or create if not exists."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Try to get existing user
            async with db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
            
            if user:
                # Update username if changed
                await db.execute(
                    'UPDATE users SET username = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (username, user_id)
                )
                await db.commit()
                return dict(user)
            else:
                # Create new user
                await db.execute(
                    'INSERT INTO users (user_id, username) VALUES (?, ?)',
                    (user_id, username)
                )
                await db.commit()
                
                # Return the created user
                async with db.execute(
                    'SELECT * FROM users WHERE user_id = ?', (user_id,)
                ) as cursor:
                    user = await cursor.fetchone()
                    return dict(user)
    
    async def start_work_session(self, user_id: int, username: str) -> bool:
        """Start a work session for user."""
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure user exists
            await self.get_or_create_user(user_id, username)
            
            # Check if user already has active session
            async with db.execute(
                'SELECT id FROM work_sessions WHERE user_id = ? AND is_active = 1',
                (user_id,)
            ) as cursor:
                active_session = await cursor.fetchone()
            
            if active_session:
                return False  # Already has active session
            
            # Create new session
            await db.execute(
                'INSERT INTO work_sessions (user_id, start_time) VALUES (?, ?)',
                (user_id, datetime.now())
            )
            await db.commit()
            return True
    
    async def end_work_session(self, user_id: int, auto_ended: bool = False) -> Optional[Dict[str, Any]]:
        """End active work session for user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get active session
            async with db.execute(
                'SELECT * FROM work_sessions WHERE user_id = ? AND is_active = 1',
                (user_id,)
            ) as cursor:
                session = await cursor.fetchone()
            
            if not session:
                return None  # No active session
            
            end_time = datetime.now()
            start_time = datetime.fromisoformat(session['start_time'])
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # Update session
            await db.execute('''
                UPDATE work_sessions 
                SET end_time = ?, duration_minutes = ?, is_active = 0, auto_ended = ?
                WHERE id = ?
            ''', (end_time, duration_minutes, auto_ended, session['id']))
            
            await db.commit()
            
            # Update weekly and monthly stats
            await self._update_weekly_stats(user_id, duration_minutes, db)
            await self._update_monthly_stats(user_id, duration_minutes, db)
            
            return {
                'id': session['id'],
                'user_id': user_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration_minutes,
                'auto_ended': auto_ended
            }
    
    async def _update_weekly_stats(self, user_id: int, duration_minutes: int, db: aiosqlite.Connection) -> None:
        """Update weekly statistics."""
        today = datetime.now().date()
        # Get Monday of current week
        week_start = today - timedelta(days=today.weekday())
        
        await db.execute('''
            INSERT INTO weekly_stats (user_id, week_start, total_minutes, sessions_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, week_start) DO UPDATE SET
                total_minutes = total_minutes + ?,
                sessions_count = sessions_count + 1
        ''', (user_id, week_start, duration_minutes, duration_minutes))
    
    async def _update_monthly_stats(self, user_id: int, duration_minutes: int, db: aiosqlite.Connection) -> None:
        """Update monthly statistics."""
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        await db.execute('''
            INSERT INTO monthly_stats (user_id, month_start, total_minutes, sessions_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, month_start) DO UPDATE SET
                total_minutes = total_minutes + ?,
                sessions_count = sessions_count + 1
        ''', (user_id, month_start, duration_minutes, duration_minutes))
    
    async def get_active_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active work session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM work_sessions WHERE user_id = ? AND is_active = 1',
                (user_id,)
            ) as cursor:
                session = await cursor.fetchone()
                return dict(session) if session else None
    
    async def get_user_work_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's work history."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM work_sessions 
                WHERE user_id = ? AND is_active = 0 
                ORDER BY start_time DESC LIMIT ?
            ''', (user_id, limit)) as cursor:
                sessions = await cursor.fetchall()
                return [dict(session) for session in sessions]
    
    async def backup_database(self) -> str:
        """Create database backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'mesai_bot_backup_{timestamp}.db'
        backup_path = os.path.join(Config.BACKUP_DIRECTORY, backup_filename)
        
        shutil.copy2(self.db_path, backup_path)
        return backup_path
    
    async def reset_weekly_stats(self) -> int:
        """Reset weekly stats and return number of affected users."""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current week users count before reset
            async with db.execute('''
                SELECT COUNT(DISTINCT user_id) FROM weekly_stats 
                WHERE week_start = ?
            ''', (datetime.now().date() - timedelta(days=datetime.now().weekday()),)) as cursor:
                result = await cursor.fetchone()
                users_count = result[0] if result else 0
            
            # Delete current week stats (they'll be recreated as needed)
            await db.execute('''
                DELETE FROM weekly_stats 
                WHERE week_start = ?
            ''', (datetime.now().date() - timedelta(days=datetime.now().weekday()),))
            
            await db.commit()
            return users_count
    
    def get_connection(self):
        """Get database connection context manager."""
        return aiosqlite.connect(self.db_path)