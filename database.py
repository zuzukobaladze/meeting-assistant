import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = 'meeting_assistant.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Meetings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                duration REAL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transcribed_at TIMESTAMP,
                status TEXT DEFAULT 'uploaded'
            )
        ''')
        
        # Transcriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                full_text TEXT NOT NULL,
                segments TEXT,  -- JSON string of segments with speaker info
                language TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # Meeting summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meeting_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                summary TEXT NOT NULL,
                action_items TEXT,  -- JSON string
                decisions TEXT,     -- JSON string
                key_topics TEXT,    -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # Embeddings table for semantic search
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                text_chunk TEXT NOT NULL,
                embedding TEXT NOT NULL,  -- JSON string of vector
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_meeting(self, title: str, filename: str, file_path: str, duration: float = None) -> int:
        """Create a new meeting record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meetings (title, filename, file_path, duration)
            VALUES (?, ?, ?, ?)
        ''', (title, filename, file_path, duration))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return meeting_id
    
    def update_meeting_status(self, meeting_id: int, status: str):
        """Update meeting status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE meetings SET status = ? WHERE id = ?
        ''', (status, meeting_id))
        
        conn.commit()
        conn.close()
    
    def save_transcription(self, meeting_id: int, full_text: str, segments: List[Dict], 
                          language: str = None, confidence: float = None, duration: float = None):
        """Save transcription data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transcriptions (meeting_id, full_text, segments, language, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (meeting_id, full_text, json.dumps(segments), language, confidence))
        
        # Update meeting status, transcription timestamp, and duration
        update_query = '''
            UPDATE meetings SET status = 'transcribed', transcribed_at = CURRENT_TIMESTAMP
        '''
        params = [meeting_id]
        
        if duration is not None:
            update_query += ', duration = ?'
            params.insert(0, duration)
        
        update_query += ' WHERE id = ?'
        
        cursor.execute(update_query, params)
        
        conn.commit()
        conn.close()
    
    def get_meeting(self, meeting_id: int) -> Optional[Dict]:
        """Get meeting by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    def get_all_meetings(self) -> List[Dict]:
        """Get all meetings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM meetings ORDER BY uploaded_at DESC')
        results = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_transcription(self, meeting_id: int) -> Optional[Dict]:
        """Get transcription for a meeting"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transcriptions WHERE meeting_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (meeting_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data = dict(result)
            if data['segments']:
                data['segments'] = json.loads(data['segments'])
            return data
        return None 