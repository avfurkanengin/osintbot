import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import werkzeug.security as security

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "osint_bot.db"):
        self.db_path = db_path
        self.init_database()
        self.seed_users()  # Seed initial users
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table - stores all processed content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                sender_name TEXT,
                original_text TEXT NOT NULL,
                translated_text TEXT,
                media_type TEXT,
                media_path TEXT,
                classification TEXT,
                quality_score REAL DEFAULT 0,
                bias_score REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                posted_at TIMESTAMP,
                twitter_url TEXT,
                telegram_url TEXT,
                content_hash TEXT,
                similarity_hash TEXT,
                priority INTEGER DEFAULT 1
            )
        ''')
        
        # User actions table - tracks manual actions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        # Analytics table - stores performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Channels table - stores channel configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT 1,
                last_processed TIMESTAMP,
                total_posts INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_channel ON posts(channel_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_hash ON posts(content_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_post ON user_actions(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def seed_users(self):
        """Seed initial users if they don't exist"""
        users = [
            ('AdminKayra', 'Kayra123'),
            ('AdminFurkan', 'Furkan123'),
            ('AdminDogukan', 'Dogukan123'),
            ('AdminTest', 'Test123')
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for username, password in users:
            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
            if cursor.fetchone() is None:
                password_hash = security.generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
        conn.commit()
        conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'password_hash': user[2],
                'role': user[3]
            }
        return None
    
    def verify_password(self, password_hash: str, password: str) -> bool:
        return security.check_password_hash(password_hash, password)
    
    def add_post(self, post_data: Dict[str, Any]) -> Optional[int]:
        """Add a new post to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO posts (
                    message_id, channel_name, sender_name, original_text, 
                    translated_text, media_type, media_path, classification,
                    quality_score, bias_score, status, content_hash, 
                    similarity_hash, priority, telegram_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_data.get('message_id'),
                post_data.get('channel_name'),
                post_data.get('sender_name'),
                post_data.get('original_text'),
                post_data.get('translated_text'),
                post_data.get('media_type'),
                post_data.get('media_path'),
                post_data.get('classification'),
                post_data.get('quality_score', 0),
                post_data.get('bias_score', 0),
                post_data.get('status', 'pending'),
                post_data.get('content_hash'),
                post_data.get('similarity_hash'),
                post_data.get('priority', 1),
                post_data.get('telegram_url')
            ))
            
            post_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added post {post_id} to database")
            return post_id
            
        except sqlite3.IntegrityError as e:
            message_id = post_data.get('message_id', 'unknown')
            logger.warning(f"Post already exists (message_id: {message_id}): {e}")
            return None
        finally:
            conn.close()
    
    def get_posts(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get posts with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                id, message_id, channel_name, sender_name, original_text,
                translated_text, media_type, media_path, classification,
                quality_score, bias_score, status, created_at, processed_at,
                posted_at, twitter_url, telegram_url, priority
            FROM posts
        '''
        params: List[Any] = []
        
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.append(str(limit))
        params.append(str(offset))
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = [
            'id', 'message_id', 'channel_name', 'sender_name', 'original_text',
            'translated_text', 'media_type', 'media_path', 'classification',
            'quality_score', 'bias_score', 'status', 'created_at', 'processed_at',
            'posted_at', 'twitter_url', 'telegram_url', 'priority'
        ]
        
        return [dict(zip(columns, row)) for row in rows]
    
    def update_post_status(self, post_id: int, status: str, **kwargs) -> bool:
        """Update post status and additional fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = ['status = ?']
        params = [status]
        
        if status == 'posted':
            update_fields.append('posted_at = CURRENT_TIMESTAMP')
        elif status == 'processed':
            update_fields.append('processed_at = CURRENT_TIMESTAMP')
        
        for key, value in kwargs.items():
            if key in ['twitter_url', 'notes']:
                update_fields.append(f'{key} = ?')
                params.append(value)
        
        params.append(str(post_id))
        
        query = f'UPDATE posts SET {", ".join(update_fields)} WHERE id = ?'
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Updated post {post_id} status to {status}")
        
        return success
    
    def add_user_action(self, post_id: int, action_type: str, notes: Optional[str] = None):
        """Record user action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_actions (post_id, action_type, notes)
            VALUES (?, ?, ?)
        ''', (post_id, action_type, notes))
        
        conn.commit()
        conn.close()
        logger.info(f"Recorded action {action_type} for post {post_id}")
    
    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics data for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = {}
        
        # Posts by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM posts
            WHERE created_at >= ?
            GROUP BY status
        ''', (start_date.isoformat(),))
        analytics['posts_by_status'] = dict(cursor.fetchall())
        
        # Posts by channel
        cursor.execute('''
            SELECT channel_name, COUNT(*) as count
            FROM posts
            WHERE created_at >= ?
            GROUP BY channel_name
            ORDER BY count DESC
        ''', (start_date.isoformat(),))
        analytics['posts_by_channel'] = dict(cursor.fetchall())
        
        # Daily post counts
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM posts
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (start_date.isoformat(),))
        analytics['daily_posts'] = dict(cursor.fetchall())
        
        # User actions
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM user_actions
            WHERE timestamp >= ?
            GROUP BY action_type
        ''', (start_date.isoformat(),))
        analytics['user_actions'] = dict(cursor.fetchall())
        
        # Quality metrics
        cursor.execute('''
            SELECT 
                AVG(quality_score) as avg_quality,
                AVG(bias_score) as avg_bias,
                COUNT(*) as total_posts
            FROM posts
            WHERE created_at >= ?
        ''', (start_date.isoformat(),))
        row = cursor.fetchone()
        analytics['quality_metrics'] = {
            'avg_quality': row[0] or 0,
            'avg_bias': row[1] or 0,
            'total_posts': row[2] or 0
        }
        
        conn.close()
        return analytics
    
    def cleanup_old_posts(self, days: int = 30):
        """Clean up old posts based on retention policy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Archive old posts instead of deleting
        cursor.execute('''
            UPDATE posts 
            SET status = 'archived'
            WHERE created_at < ? AND status NOT IN ('posted', 'pending')
        ''', (cutoff_date.isoformat(),))
        
        archived_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Archived {archived_count} old posts")
        return archived_count 