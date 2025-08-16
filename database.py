"""
Database operations for track settings and user data
"""
import sqlite3
import logging
from datetime import datetime

DATABASE_FILE = "settings.db"

def init_database():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS track_settings (
                track_id TEXT PRIMARY KEY,
                track_name TEXT,
                artist_name TEXT,
                tempo REAL,
                energy REAL,
                custom_bpm REAL,
                speed REAL DEFAULT 1.0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
        
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")

def save_track_settings(track_id, settings):
    """Save or update track settings"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO track_settings 
            (track_id, track_name, artist_name, tempo, energy, custom_bpm, speed, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            track_id,
            settings.get('track_name'),
            settings.get('artist_name'), 
            settings.get('tempo'),
            settings.get('energy'),
            settings.get('custom_bpm'),
            settings.get('speed', 1.0),
            settings.get('notes'),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        logging.info(f"Settings saved for track {track_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to save settings for track {track_id}: {str(e)}")
        return False

def get_track_settings(track_id):
    """Get settings for a specific track"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT track_name, artist_name, tempo, energy, custom_bpm, speed, notes
            FROM track_settings 
            WHERE track_id = ?
        ''', (track_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'track_name': row[0],
                'artist_name': row[1],
                'tempo': row[2],
                'energy': row[3],
                'custom_bpm': row[4],
                'speed': row[5] or 1.0,
                'notes': row[6]
            }
        else:
            # Return default values if no settings found
            return {
                'tempo': None,
                'energy': 0.5,
                'custom_bpm': None,
                'speed': 1.0,
                'notes': ''
            }
            
    except Exception as e:
        logging.error(f"Failed to get settings for track {track_id}: {str(e)}")
        return {'tempo': None, 'energy': 0.5, 'custom_bpm': None, 'speed': 1.0, 'notes': ''}

def get_all_settings():
    """Get all saved track settings"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT track_id, track_name, artist_name, tempo, energy, custom_bpm, speed, notes, updated_at
            FROM track_settings 
            ORDER BY updated_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        settings = []
        for row in rows:
            settings.append({
                'track_id': row[0],
                'track_name': row[1],
                'artist_name': row[2],
                'tempo': row[3],
                'energy': row[4],
                'custom_bpm': row[5],
                'speed': row[6],
                'notes': row[7],
                'updated_at': row[8]
            })
            
        return settings
        
    except Exception as e:
        logging.error(f"Failed to get all settings: {str(e)}")
        return []
