"""
Business logic services for Household Event Planner Prototype
"""

import re
from datetime import datetime
from models import User, Household, HouseholdMember, Category, Event, Task


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    def register(username, password, email=None):
        """
        Register a new user
        UC1: Register User

        Args:
            username: Unique username
            password: User's password
            email: Optional email address

        Returns:
            tuple: (success, message, user)
        """
        # Validate username
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters", None

        # Check if username already exists
        if User.find_by_username(username):
            return False, "Username already exists", None

        # Validate password
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters", None

        # Validate email if provided
        if email:
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                return False, "Invalid email format", None

        # Create new user
        password_hash = User.hash_password(password)
        user = User(username=username, password_hash=password_hash, email=email, role='member')
        user.save()

        return True, "Registration successful", user

    @staticmethod
    def login(username, password):
        """
        Authenticate user
        UC2: Login

        Args:
            username: User's username
            password: User's password

        Returns:
            tuple: (success, message, user)
        """
        user = User.authenticate(username, password)

        if user:
            return True, f"Welcome back, {user.username}!", user
        else:
            return False, "Invalid username or password", None


class HouseholdService:
    """Service for household management"""

    @staticmethod
    def create_household(name, owner):
        """
        Create a new household

        Args:
            name: Household name
            owner: Owner user object

        Returns:
            Household object
        """
        household = Household(name=name, owner_id=owner.user_id)
        household.save()

        # Create default category for household
        category = Category(
            household_id=household.household_id,
            name="General",
            color="#3498db",
            icon="event",
            is_default=True
        )
        category.save()

        # Add owner as household member
        member = HouseholdMember(
            user_id=owner.user_id,
            household_id=household.household_id,
            name=owner.username,
            relationship="Self"
        )
        member.save()

        return household

    @staticmethod
    def get_household_for_user(user):
        """Get household for a user"""
        return Household.find_by_owner(user.user_id)

    @staticmethod
    def add_member(household_id, name, relationship):
        """Add member to household"""
        member = HouseholdMember(
            household_id=household_id,
            name=name,
            relationship=relationship
        )
        member.save()
        return member

    @staticmethod
    def get_members(household_id):
        """Get all household members"""
        return HouseholdMember.find_by_household(household_id)


class CategoryService:
    """Service for category management"""

    @staticmethod
    def get_categories(household_id):
        """Get all categories for a household"""
        return Category.find_by_household(household_id)

    @staticmethod
    def create_category(household_id, name, color="#3498db", icon="event"):
        """
        Create a new category
        UC10: Manage Categories

        Args:
            household_id: Household ID
            name: Category name
            color: Hex color code
            icon: Icon name

        Returns:
            Category object
        """
        # Check if category name already exists
        categories = Category.find_by_household(household_id)
        for cat in categories:
            if cat.name.lower() == name.lower():
                return None, "Category name already exists"

        category = Category(
            household_id=household_id,
            name=name,
            color=color,
            icon=icon,
            is_default=False
        )
        category.save()
        return category, "Category created successfully"

    @staticmethod
    def update_category(category_id, name, color, icon):
        """Update an existing category"""
        category = Category.find_by_id(category_id)
        if category:
            category.name = name
            category.color = color
            category.icon = icon
            category.save()
            return True, "Category updated"
        return False, "Category not found"

    @staticmethod
    def delete_category(category_id):
        """Delete a category"""
        category = Category.find_by_id(category_id)
        if category:
            if category.is_default:
                return False, "Cannot delete default category"
            category_id = category.category_id
            household_id = category.household_id
            # Delete the category
            import sqlite3
            from database import get_db
            db = get_db()
            db.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
            # Move events to default category
            default = Category.get_default(household_id)
            if default:
                db.execute(
                    "UPDATE events SET category_id = ? WHERE category_id = ?",
                    (default.category_id, category_id)
                )
            return True, "Category deleted"
        return False, "Category not found"


class EventService:
    """Service for event management"""

    @staticmethod
    def create_event(household_id, title, description, start_time, end_time=None,
                     location=None, category_id=None, created_by=None):
        """
        Create a new event
        UC3: Create Event

        Args:
            household_id: Household ID
            title: Event title
            description: Event description
            start_time: Start datetime
            end_time: Optional end datetime
            location: Optional location
            category_id: Optional category ID
            created_by: User ID who created the event

        Returns:
            tuple: (success, message, event)
        """
        # Validate required fields
        if not title or len(title) > 100:
            return False, "Title is required and must be less than 100 characters", None

        if not start_time:
            return False, "Start time is required", None

        # Validate end time if provided
        if end_time:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M") if isinstance(start_time, str) else start_time
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M") if isinstance(end_time, str) else end_time
            if end_dt <= start_dt:
                return False, "End time must be after start time", None

        # Create event
        event = Event(
            household_id=household_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            category_id=category_id,
            created_by=created_by
        )
        event.save()

        return True, "Event created successfully", event

    @staticmethod
    def update_event(event_id, title, description, start_time, end_time=None,
                     location=None, category_id=None):
        """
        Update an event
        UC4: Edit Event

        Args:
            event_id: Event ID
            title: Updated title
            description: Updated description
            start_time: Updated start time
            end_time: Optional updated end time
            location: Optional updated location
            category_id: Optional updated category

        Returns:
            tuple: (success, message)
        """
        event = Event.find_by_id(event_id)
        if not event:
            return False, "Event not found"

        event.title = title
        event.description = description
        event.start_time = start_time
        event.end_time = end_time
        event.location = location
        event.category_id = category_id
        event.save()

        return True, "Event updated successfully"

    @staticmethod
    def delete_event(event_id):
        """
        Delete an event
        UC5: Delete Event

        Args:
            event_id: Event ID

        Returns:
            tuple: (success, message)
        """
        event = Event.find_by_id(event_id)
        if not event:
            return False, "Event not found"

        event.delete()
        return True, "Event deleted successfully"

    @staticmethod
    def get_events(household_id):
        """Get all events for a household"""
        return Event.find_by_household(household_id)

    @staticmethod
    def get_upcoming_events(household_id, days=7):
        """Get upcoming events"""
        return Event.find_upcoming(household_id, days)

    @staticmethod
    def get_event_by_id(event_id):
        """Get event by ID"""
        return Event.find_by_id(event_id)


class TaskService:
    """Service for task management"""

    @staticmethod
    def create_task(household_id, title, description=None, due_date=None,
                    priority='medium', created_by=None):
        """
        Create a new task
        UC6: Create Task

        Args:
            household_id: Household ID
            title: Task title
            description: Optional description
            due_date: Optional due date
            priority: Task priority (low, medium, high)
            created_by: User ID who created the task

        Returns:
            tuple: (success, message, task)
        """
        if not title or len(title) > 100:
            return False, "Title is required and must be less than 100 characters", None

        task = Task(
            household_id=household_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            created_by=created_by,
            status='pending'
        )
        task.save()

        return True, "Task created successfully", task

    @staticmethod
    def assign_task(task_id, member_id):
        """
        Assign a task to a household member
        UC7: Assign Task

        Args:
            task_id: Task ID
            member_id: Member ID to assign

        Returns:
            tuple: (success, message)
        """
        task = Task.find_by_id(task_id)
        if not task:
            return False, "Task not found"

        member = HouseholdMember.find_by_id(member_id)
        if not member:
            return False, "Member not found"

        task.assigned_member_id = member_id
        task.save()

        return True, f"Task assigned to {member.name}"

    @staticmethod
    def update_task_status(task_id, new_status):
        """
        Update task status
        UC8: Update Task Status

        Args:
            task_id: Task ID
            new_status: New status (pending, in_progress, completed, cancelled)

        Returns:
            tuple: (success, message)
        """
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        task = Task.find_by_id(task_id)
        if not task:
            return False, "Task not found"

        task.update_status(new_status)
        return True, f"Task status updated to {new_status}"

    @staticmethod
    def get_tasks(household_id):
        """Get all tasks for a household"""
        return Task.find_by_household(household_id)

    @staticmethod
    def get_pending_tasks(household_id):
        """Get pending tasks"""
        return Task.find_pending(household_id)

    @staticmethod
    def get_task_by_id(task_id):
        """Get task by ID"""
        return Task.find_by_id(task_id)

    @staticmethod
    def delete_task(task_id):
        """Delete a task"""
        task = Task.find_by_id(task_id)
        if task:
            task.delete()
            return True, "Task deleted"
        return False, "Task not found"