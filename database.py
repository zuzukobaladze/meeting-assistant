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
        
        # Meeting insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meeting_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                effectiveness_score INTEGER,
                effectiveness_notes TEXT,
                engagement_analysis TEXT,  -- JSON string
                communication_patterns TEXT,  -- JSON string
                recommendations TEXT,  -- JSON string
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
    
    def save_meeting_summary(self, meeting_id: int, summary: str, action_items: List[Dict], 
                           decisions: List[Dict], key_topics: List[Dict]):
        """Save meeting analysis results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meeting_summaries (meeting_id, summary, action_items, decisions, key_topics)
            VALUES (?, ?, ?, ?, ?)
        ''', (meeting_id, summary, json.dumps(action_items), json.dumps(decisions), json.dumps(key_topics)))
        
        conn.commit()
        conn.close()
    
    def save_meeting_insights(self, meeting_id: int, insights: Dict):
        """Save meeting insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meeting_insights (meeting_id, effectiveness_score, effectiveness_notes,
                                        engagement_analysis, communication_patterns, recommendations)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            meeting_id,
            insights.get('effectiveness_score'),
            insights.get('effectiveness_notes'),
            json.dumps(insights.get('engagement_analysis', {})),
            json.dumps(insights.get('communication_patterns', {})),
            json.dumps(insights.get('recommendations', []))
        ))
        
        conn.commit()
        conn.close()
    
    def get_meeting_summary(self, meeting_id: int) -> Optional[Dict]:
        """Get meeting summary"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM meeting_summaries WHERE meeting_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (meeting_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data = dict(result)
            # Parse JSON fields
            for field in ['action_items', 'decisions', 'key_topics']:
                if data[field]:
                    data[field] = json.loads(data[field])
            return data
        return None
    
    def get_meeting_insights(self, meeting_id: int) -> Optional[Dict]:
        """Get meeting insights"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM meeting_insights WHERE meeting_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (meeting_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data = dict(result)
            # Parse JSON fields
            for field in ['engagement_analysis', 'communication_patterns', 'recommendations']:
                if data[field]:
                    data[field] = json.loads(data[field])
            return data
        return None
    
    def save_embeddings(self, meeting_id: int, embeddings_data: List[Dict]):
        """Save embeddings for a meeting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing embeddings for this meeting
        cursor.execute('DELETE FROM embeddings WHERE meeting_id = ?', (meeting_id,))
        
        # Insert new embeddings
        for item in embeddings_data:
            cursor.execute('''
                INSERT INTO embeddings (meeting_id, text_chunk, embedding, chunk_index)
                VALUES (?, ?, ?, ?)
            ''', (
                meeting_id,
                item['text'],
                json.dumps(item['embedding']),
                item.get('chunk_index', 0)
            ))
        
        conn.commit()
        conn.close()
    
    def get_all_embeddings(self) -> List[Dict]:
        """Get all embeddings from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, m.title 
            FROM embeddings e
            JOIN meetings m ON e.meeting_id = m.id
            WHERE m.status = 'transcribed'
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        embeddings = []
        for row in results:
            data = dict(row)
            data['embedding'] = json.loads(data['embedding'])
            data['metadata'] = {'title': data['title'], 'type': 'transcription'}
            embeddings.append(data)
        
        return embeddings
    
    def get_meeting_embeddings(self, meeting_id: int) -> List[Dict]:
        """Get embeddings for a specific meeting"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, m.title 
            FROM embeddings e
            JOIN meetings m ON e.meeting_id = m.id
            WHERE e.meeting_id = ?
        ''', (meeting_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        embeddings = []
        for row in results:
            data = dict(row)
            data['embedding'] = json.loads(data['embedding'])
            data['metadata'] = {'title': data['title'], 'type': 'transcription'}
            embeddings.append(data)
        
        return embeddings
    
    def search_meetings_by_text(self, search_query: str) -> List[Dict]:
        """Basic text search as fallback"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT m.*, t.full_text, s.summary
            FROM meetings m
            LEFT JOIN transcriptions t ON m.id = t.meeting_id
            LEFT JOIN meeting_summaries s ON m.id = s.meeting_id
            WHERE m.status = 'transcribed' 
            AND (m.title LIKE ? OR t.full_text LIKE ? OR s.summary LIKE ?)
            ORDER BY m.uploaded_at DESC
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results] 