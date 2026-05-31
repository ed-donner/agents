import sqlite3
from datetime import datetime


class DatabaseUtils:
    def __init__(self):
        self.conn = sqlite3.connect('career_agent.db')
        self.cursor = self.conn.cursor()
        self.create_unknown_questions_table()

    def create_unknown_questions_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS unknown_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            user_id TEXT,
            timestamp TEXT,
            notes TEXT,
            answered INTEGER DEFAULT 0
        )
        ''')
        self.conn.commit()

    def insert_unknown_question(self, question, user_id, notes = None):
        timestamp = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO unknown_questions (question, user_id, notes, timestamp) VALUES (?, ?, ?, ?)', (question, user_id, notes, timestamp))
        self.conn.commit()

    def mark_as_answered(self, question_id):
        self.cursor.execute('UPDATE unknown_questions SET answered = 1 WHERE id = ?', (question_id,))
        self.conn.commit()

    def get_unknown_questions(self):
        self.cursor.execute('SELECT * FROM unknown_questions WHERE answered = 0')
        rows = self.cursor.fetchall()
        return rows

    def close(self):
        self.conn.close()