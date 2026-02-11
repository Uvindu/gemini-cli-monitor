import sqlite3
import os
import datetime
import json
import glob

# Use local data directory relative to this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "geminiwatch.db")
GEMINI_DIR = os.path.expanduser("~/.gemini")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            session_id TEXT,
            message_id TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cached_tokens INTEGER,
            thought_tokens INTEGER,
            total_tokens INTEGER,
            UNIQUE(session_id, message_id)
        )
    ''')
    conn.commit()
    conn.close()

def sync_from_gemini():
    """Sync data from ~/.gemini session files into SQLite."""
    init_db()
    session_files = glob.glob(os.path.join(GEMINI_DIR, "tmp", "*", "chats", "session-*.json"))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    new_records = 0
    for f_path in session_files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                session_id = data.get("sessionId")
                for msg in data.get("messages", []):
                    if msg.get("type") == "gemini":
                        message_id = msg.get("id")
                        timestamp = msg.get("timestamp")
                        model = msg.get("model", "unknown")
                        tokens = msg.get("tokens", {})
                        
                        input_tokens = tokens.get("input", 0)
                        output_tokens = tokens.get("output", 0)
                        cached_tokens = tokens.get("cached", 0)
                        thought_tokens = tokens.get("thoughts", 0)
                        total_tokens = tokens.get("total", 0)
                        
                        try:
                            c.execute('''
                                INSERT INTO requests (timestamp, session_id, message_id, model, input_tokens, output_tokens, cached_tokens, thought_tokens, total_tokens)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (timestamp, session_id, message_id, model, input_tokens, output_tokens, cached_tokens, thought_tokens, total_tokens))
                            new_records += 1
                        except sqlite3.IntegrityError:
                            # If it exists, we might want to update it if the schema changed
                            # But for now, we'll just skip.
                            pass
        except Exception as e:
            continue
            
    conn.commit()
    conn.close()
    return new_records

def get_recent_requests(limit=10):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM requests ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_model_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Count requests per model today
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    c.execute('''
        SELECT model, COUNT(*) 
        FROM requests 
        WHERE timestamp LIKE ? 
        GROUP BY model
    ''', (f'{today}%',))
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Aggregates
    c.execute('''
        SELECT 
            SUM(input_tokens), 
            SUM(output_tokens), 
            SUM(cached_tokens), 
            SUM(thought_tokens),
            COUNT(*) 
        FROM requests
    ''')
    res = c.fetchone()
    total_in, total_out, total_cached, total_thought, total_reqs = [x or 0 for x in res]
    
    # Today's tokens (UTC)
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    c.execute('''
        SELECT 
            SUM(input_tokens), 
            SUM(output_tokens), 
            SUM(cached_tokens), 
            SUM(thought_tokens)
        FROM requests 
        WHERE timestamp LIKE ?
    ''', (f'{today}%',))
    res_today = c.fetchone()
    today_in, today_out, today_cached, today_thought = [x or 0 for x in res_today]

    conn.close()
    return {
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_cached_tokens": total_cached,
        "total_thought_tokens": total_thought,
        "today_input_tokens": today_in,
        "today_output_tokens": today_out,
        "today_cached_tokens": today_cached,
        "today_thought_tokens": today_thought,
        "total_requests": total_reqs
    }

if __name__ == "__main__":
    init_db()
    print(f"Synced {sync_from_gemini()} new records.")
