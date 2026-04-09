"""
Data models for Household Event Planner Prototype
"""

import hashlib
from datetime import datetime
from database import get_db


class User:
    """User model"""

    def __init__(self, user_id=None, username=None, password_hash=None,
                 email=None, role='member', created_at=None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.role = role
        self.created_at = created_at or datetime.now()

    @staticmethod
    def hash_password(password):
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def save(self):
        """Save user to database"""
        db = get_db()
        if self.user_id:
            db.execute(
                "UPDATE users SET username=?, password_hash=?, email=?, role=? WHERE user_id=?",
                (self.username, self.password_hash, self.email, self.role, self.user_id)
            )
        else:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)",
                (self.username, self.password_hash, self.email, self.role)
            )
            self.user_id = cursor.lastrowid
        return self

    @staticmethod
    def authenticate(username, password):
        """Authenticate user with username and password"""
        db = get_db()
        password_hash = User.hash_password(password)
        row = db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                password_hash=row['password_hash'],
                email=row['email'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None

    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                password_hash=row['password_hash'],
                email=row['email'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None

    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                password_hash=row['password_hash'],
                email=row['email'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at
        }


class Household:
    """Household model"""

    def __init__(self, household_id=None, name=None, owner_id=None, created_at=None):
        self.household_id = household_id
        self.name = name
        self.owner_id = owner_id
        self.created_at = created_at or datetime.now()

    def save(self):
        """Save household to database"""
        db = get_db()
        if self.household_id:
            db.execute(
                "UPDATE households SET name=? WHERE household_id=?",
                (self.name, self.household_id)
            )
        else:
            cursor = db.execute(
                "INSERT INTO households (name, owner_id) VALUES (?, ?)",
                (self.name, self.owner_id)
            )
            self.household_id = cursor.lastrowid
        return self

    @staticmethod
    def find_by_id(household_id):
        """Find household by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM households WHERE household_id = ?", (household_id,))
        if row:
            return Household(
                household_id=row['household_id'],
                name=row['name'],
                owner_id=row['owner_id'],
                created_at=row['created_at']
            )
        return None

    @staticmethod
    def find_by_owner(owner_id):
        """Find household by owner"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM households WHERE owner_id = ?", (owner_id,))
        if row:
            return Household(
                household_id=row['household_id'],
                name=row['name'],
                owner_id=row['owner_id'],
                created_at=row['created_at']
            )
        return None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'household_id': self.household_id,
            'name': self.name,
            'owner_id': self.owner_id,
            'created_at': self.created_at
        }


class HouseholdMember:
    """HouseholdMember model"""

    def __init__(self, member_id=None, user_id=None, household_id=None,
                 name=None, birth_date=None, phone=None,
                 relationship=None, is_active=True):
        self.member_id = member_id
        self.user_id = user_id
        self.household_id = household_id
        self.name = name
        self.birth_date = birth_date
        self.phone = phone
        self.relationship = relationship
        self.is_active = is_active

    def save(self):
        """Save household member to database"""
        db = get_db()
        if self.member_id:
            db.execute(
                """UPDATE household_members SET name=?, birth_date=?, phone=?,
                relationship=?, is_active=? WHERE member_id=?""",
                (self.name, self.birth_date, self.phone, self.relationship,
                 1 if self.is_active else 0, self.member_id)
            )
        else:
            cursor = db.execute(
                """INSERT INTO household_members (user_id, household_id, name,
                birth_date, phone, relationship) VALUES (?, ?, ?, ?, ?, ?)""",
                (self.user_id, self.household_id, self.name, self.birth_date,
                 self.phone, self.relationship)
            )
            self.member_id = cursor.lastrowid
        return self

    @staticmethod
    def find_by_household(household_id):
        """Find all members of a household"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM household_members WHERE household_id = ? AND is_active = 1",
            (household_id,)
        )
        return [HouseholdMember(
            member_id=row['member_id'],
            user_id=row['user_id'],
            household_id=row['household_id'],
            name=row['name'],
            birth_date=row['birth_date'],
            phone=row['phone'],
            relationship=row['relationship'],
            is_active=bool(row['is_active'])
        ) for row in rows]

    @staticmethod
    def find_by_id(member_id):
        """Find member by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM household_members WHERE member_id = ?", (member_id,))
        if row:
            return HouseholdMember(
                member_id=row['member_id'],
                user_id=row['user_id'],
                household_id=row['household_id'],
                name=row['name'],
                birth_date=row['birth_date'],
                phone=row['phone'],
                relationship=row['relationship'],
                is_active=bool(row['is_active'])
            )
        return None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'member_id': self.member_id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'name': self.name,
            'birth_date': self.birth_date,
            'phone': self.phone,
            'relationship': self.relationship,
            'is_active': self.is_active
        }


class Category:
    """Category model"""

    def __init__(self, category_id=None, household_id=None, name=None,
                 color='#3498db', icon='event', is_default=False):
        self.category_id = category_id
        self.household_id = household_id
        self.name = name
        self.color = color
        self.icon = icon
        self.is_default = is_default

    def save(self):
        """Save category to database"""
        db = get_db()
        if self.category_id:
            db.execute(
                "UPDATE categories SET name=?, color=?, icon=? WHERE category_id=?",
                (self.name, self.color, self.icon, self.category_id)
            )
        else:
            cursor = db.execute(
                "INSERT INTO categories (household_id, name, color, icon, is_default) VALUES (?, ?, ?, ?, ?)",
                (self.household_id, self.name, self.color, self.icon, 1 if self.is_default else 0)
            )
            self.category_id = cursor.lastrowid
        return self

    @staticmethod
    def find_by_household(household_id):
        """Find all categories for a household"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM categories WHERE household_id = ?",
            (household_id,)
        )
        return [Category(
            category_id=row['category_id'],
            household_id=row['household_id'],
            name=row['name'],
            color=row['color'],
            icon=row['icon'],
            is_default=bool(row['is_default'])
        ) for row in rows]

    @staticmethod
    def find_by_id(category_id):
        """Find category by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM categories WHERE category_id = ?", (category_id,))
        if row:
            return Category(
                category_id=row['category_id'],
                household_id=row['household_id'],
                name=row['name'],
                color=row['color'],
                icon=row['icon'],
                is_default=bool(row['is_default'])
            )
        return None

    @staticmethod
    def get_default(household_id):
        """Get default category for household"""
        db = get_db()
        row = db.fetch_one(
            "SELECT * FROM categories WHERE household_id = ? AND is_default = 1",
            (household_id,)
        )
        if row:
            return Category(
                category_id=row['category_id'],
                household_id=row['household_id'],
                name=row['name'],
                color=row['color'],
                icon=row['icon'],
                is_default=True
            )
        return None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'category_id': self.category_id,
            'household_id': self.household_id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'is_default': self.is_default
        }


class Event:
    """Event model"""

    def __init__(self, event_id=None, household_id=None, title=None, description=None,
                 start_time=None, end_time=None, location=None, venue_id=None,
                 category_id=None, is_recurring=False, recurring_pattern_id=None,
                 created_by=None, created_at=None):
        self.event_id = event_id
        self.household_id = household_id
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.venue_id = venue_id
        self.category_id = category_id
        self.is_recurring = is_recurring
        self.recurring_pattern_id = recurring_pattern_id
        self.created_by = created_by
        self.created_at = created_at or datetime.now()

    def save(self):
        """Save event to database"""
        db = get_db()
        if self.event_id:
            db.execute(
                """UPDATE events SET title=?, description=?, start_time=?, end_time=?,
                location=?, venue_id=?, category_id=?, is_recurring=?,
                recurring_pattern_id=? WHERE event_id=?""",
                (self.title, self.description, self.start_time, self.end_time,
                 self.location, self.venue_id, self.category_id, self.is_recurring,
                 self.recurring_pattern_id, self.event_id)
            )
        else:
            cursor = db.execute(
                """INSERT INTO events (household_id, title, description, start_time,
                end_time, location, venue_id, category_id, is_recurring,
                recurring_pattern_id, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.household_id, self.title, self.description, self.start_time,
                 self.end_time, self.location, self.venue_id, self.category_id,
                 self.is_recurring, self.recurring_pattern_id, self.created_by)
            )
            self.event_id = cursor.lastrowid
        return self

    @staticmethod
    def find_by_household(household_id):
        """Find all events for a household"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM events WHERE household_id = ? ORDER BY start_time",
            (household_id,)
        )
        return [Event(
            event_id=row['event_id'],
            household_id=row['household_id'],
            title=row['title'],
            description=row['description'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            location=row['location'],
            venue_id=row['venue_id'],
            category_id=row['category_id'],
            is_recurring=bool(row['is_recurring']),
            recurring_pattern_id=row['recurring_pattern_id'],
            created_by=row['created_by'],
            created_at=row['created_at']
        ) for row in rows]

    @staticmethod
    def find_upcoming(household_id, days=7):
        """Find upcoming events"""
        db = get_db()
        from datetime import timedelta
        end_date = datetime.now() + timedelta(days=days)
        rows = db.fetch_all(
            """SELECT * FROM events WHERE household_id = ? AND start_time >= ?
            AND start_time <= ? ORDER BY start_time""",
            (household_id, datetime.now(), end_date)
        )
        return [Event(
            event_id=row['event_id'],
            household_id=row['household_id'],
            title=row['title'],
            description=row['description'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            location=row['location'],
            venue_id=row['venue_id'],
            category_id=row['category_id'],
            is_recurring=bool(row['is_recurring']),
            recurring_pattern_id=row['recurring_pattern_id'],
            created_by=row['created_by'],
            created_at=row['created_at']
        ) for row in rows]

    @staticmethod
    def find_by_id(event_id):
        """Find event by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM events WHERE event_id = ?", (event_id,))
        if row:
            return Event(
                event_id=row['event_id'],
                household_id=row['household_id'],
                title=row['title'],
                description=row['description'],
                start_time=row['start_time'],
                end_time=row['end_time'],
                location=row['location'],
                venue_id=row['venue_id'],
                category_id=row['category_id'],
                is_recurring=bool(row['is_recurring']),
                recurring_pattern_id=row['recurring_pattern_id'],
                created_by=row['created_by'],
                created_at=row['created_at']
            )
        return None

    def delete(self):
        """Delete event"""
        db = get_db()
        db.execute("DELETE FROM events WHERE event_id = ?", (self.event_id,))

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'household_id': self.household_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'category_id': self.category_id,
            'is_recurring': self.is_recurring,
            'created_by': self.created_by
        }


class Task:
    """Task model"""

    def __init__(self, task_id=None, household_id=None, title=None, description=None,
                 due_date=None, assigned_member_id=None, status='pending',
                 priority='medium', created_by=None, created_at=None):
        self.task_id = task_id
        self.household_id = household_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.assigned_member_id = assigned_member_id
        self.status = status
        self.priority = priority
        self.created_by = created_by
        self.created_at = created_at or datetime.now()

    def save(self):
        """Save task to database"""
        db = get_db()
        if self.task_id:
            db.execute(
                """UPDATE tasks SET title=?, description=?, due_date=?,
                assigned_member_id=?, status=?, priority=? WHERE task_id=?""",
                (self.title, self.description, self.due_date, self.assigned_member_id,
                 self.status, self.priority, self.task_id)
            )
        else:
            cursor = db.execute(
                """INSERT INTO tasks (household_id, title, description, due_date,
                assigned_member_id, status, priority, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.household_id, self.title, self.description, self.due_date,
                 self.assigned_member_id, self.status, self.priority, self.created_by)
            )
            self.task_id = cursor.lastrowid
        return self

    @staticmethod
    def find_by_household(household_id):
        """Find all tasks for a household"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM tasks WHERE household_id = ? ORDER BY due_date",
            (household_id,)
        )
        return [Task(
            task_id=row['task_id'],
            household_id=row['household_id'],
            title=row['title'],
            description=row['description'],
            due_date=row['due_date'],
            assigned_member_id=row['assigned_member_id'],
            status=row['status'],
            priority=row['priority'],
            created_by=row['created_by'],
            created_at=row['created_at']
        ) for row in rows]

    @staticmethod
    def find_pending(household_id):
        """Find pending tasks"""
        db = get_db()
        rows = db.fetch_all(
            "SELECT * FROM tasks WHERE household_id = ? AND status IN ('pending', 'in_progress') ORDER BY due_date",
            (household_id,)
        )
        return [Task(
            task_id=row['task_id'],
            household_id=row['household_id'],
            title=row['title'],
            description=row['description'],
            due_date=row['due_date'],
            assigned_member_id=row['assigned_member_id'],
            status=row['status'],
            priority=row['priority'],
            created_by=row['created_by'],
            created_at=row['created_at']
        ) for row in rows]

    @staticmethod
    def find_by_id(task_id):
        """Find task by ID"""
        db = get_db()
        row = db.fetch_one("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        if row:
            return Task(
                task_id=row['task_id'],
                household_id=row['household_id'],
                title=row['title'],
                description=row['description'],
                due_date=row['due_date'],
                assigned_member_id=row['assigned_member_id'],
                status=row['status'],
                priority=row['priority'],
                created_by=row['created_by'],
                created_at=row['created_at']
            )
        return None

    def update_status(self, new_status):
        """Update task status"""
        self.status = new_status
        self.save()

    def delete(self):
        """Delete task"""
        db = get_db()
        db.execute("DELETE FROM tasks WHERE task_id = ?", (self.task_id,))

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'household_id': self.household_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date,
            'assigned_member_id': self.assigned_member_id,
            'status': self.status,
            'priority': self.priority,
            'created_by': self.created_by
        }