"""
Database module for Household Event Planner Prototype
Provides SQLite database setup and operations
"""

import sqlite3
import os
from datetime import datetime


class Database:
    """Database manager for SQLite operations"""

    def __init__(self, db_path="household_planner.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")

    def create_tables(self):
        """Create all database tables"""
        cursor = self.connection.cursor()

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Households Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS households (
                household_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )
        """)

        # Household Members Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS household_members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                household_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                birth_date DATE,
                phone TEXT,
                relationship TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        # Categories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#3498db',
                icon TEXT DEFAULT 'event',
                is_default INTEGER DEFAULT 0,
                FOREIGN KEY (household_id) REFERENCES households(household_id)
            )
        """)

        # Recurring Patterns Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency TEXT NOT NULL,
                interval_val INTEGER DEFAULT 1,
                days_of_week TEXT,
                end_date DATE,
                occurrences INTEGER
            )
        """)

        # Venues Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS venues (
                venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                capacity INTEGER,
                notes TEXT
            )
        """)

        # Events Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                location TEXT,
                venue_id INTEGER,
                category_id INTEGER,
                is_recurring INTEGER DEFAULT 0,
                recurring_pattern_id INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (household_id) REFERENCES households(household_id),
                FOREIGN KEY (venue_id) REFERENCES venues(venue_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id),
                FOREIGN KEY (recurring_pattern_id) REFERENCES recurring_patterns(pattern_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)

        # Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date TIMESTAMP,
                assigned_member_id INTEGER,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (household_id) REFERENCES households(household_id),
                FOREIGN KEY (assigned_member_id) REFERENCES household_members(member_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)

        # Reminders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                task_id INTEGER,
                remind_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                message TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(event_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)

        # Invitations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                guest_email TEXT NOT NULL,
                guest_name TEXT,
                status TEXT DEFAULT 'pending',
                rsvp_date DATE,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(event_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_household ON events(household_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_household ON tasks(household_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")

        self.connection.commit()

    def execute(self, query, params=None):
        """Execute a query and return results"""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.connection.commit()
        return cursor

    def fetch_one(self, query, params=None):
        """Fetch one row"""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        """Fetch all rows"""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


# Global database instance
db = Database()


def get_db():
    """Get database instance"""
    return db