"""
Test script for Household Event Planner Prototype
Verifies that all components work correctly
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database creation"""
    print("Testing database creation...")
    from database import Database

    # Create a test database
    db = Database("test_household.db")

    # Test that tables exist
    cursor = db.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    required_tables = ['users', 'households', 'household_members', 'categories',
                      'events', 'tasks', 'reminders', 'invitations']

    for table in required_tables:
        if table in tables:
            print(f"  [OK] Table '{table}' exists")
        else:
            print(f"  [FAIL] Table '{table}' missing")
            return False

    db.close()
    return True


def test_models():
    """Test data models"""
    print("\nTesting data models...")
    from models import User, Household, Category, Event, Task

    # Test User model
    print("  Testing User model...")
    user = User(username="testuser", password_hash=User.hash_password("password123"), email="test@test.com")
    print(f"    [OK] User created: {user.username}")

    # Test authentication
    user_auth = User.authenticate("testuser", "password123")
    if user_auth:
        print(f"    [OK] Authentication works")
    else:
        print(f"    [FAIL] Authentication failed")

    return True


def test_services():
    """Test business logic services"""
    print("\nTesting services...")

    # Remove test database if exists
    if os.path.exists("test_household.db"):
        os.remove("test_household.db")

    from database import Database
    db = Database("test_household.db")

    from services import AuthService, HouseholdService, CategoryService

    # Test registration
    print("  Testing registration...")
    success, message, user = AuthService.register("demo_user", "password123", "demo@test.com")
    if success:
        print(f"    [OK] Registration: {message}")
    else:
        print(f"    [FAIL] Registration failed: {message}")
        return False

    # Test login
    print("  Testing login...")
    success, message, user = AuthService.login("demo_user", "password123")
    if success:
        print(f"    [OK] Login: {message}")
    else:
        print(f"    [FAIL] Login failed: {message}")
        return False

    # Create household
    print("  Testing household creation...")
    household = HouseholdService.create_household("Test Household", user)
    print(f"    [OK] Household created: {household.name}")

    # Create category
    print("  Testing category creation...")
    category, message = CategoryService.create_category(household.household_id, "Birthday", "#ff0000")
    if category:
        print(f"    [OK] Category created: {category.name}")
    else:
        print(f"    [FAIL] Category creation failed: {message}")

    # Create event
    print("  Testing event creation...")
    from services import EventService
    success, message, event = EventService.create_event(
        household.household_id,
        "Test Event",
        "This is a test event",
        "2026-04-01 10:00",
        "2026-04-01 12:00",
        "Test Location",
        category.category_id if category else None,
        user.user_id
    )
    if success:
        print(f"    [OK] Event created: {event.title}")
    else:
        print(f"    [FAIL] Event creation failed: {message}")

    # Create task
    print("  Testing task creation...")
    from services import TaskService
    success, message, task = TaskService.create_task(
        household.household_id,
        "Test Task",
        "This is a test task",
        "2026-04-05 15:00",
        "high",
        user.user_id
    )
    if success:
        print(f"    [OK] Task created: {task.title}")
    else:
        print(f"    [FAIL] Task creation failed: {message}")

    # Assign task
    print("  Testing task assignment...")
    members = HouseholdService.get_members(household.household_id)
    if members:
        success, message = TaskService.assign_task(task.task_id, members[0].member_id)
        if success:
            print(f"    [OK] Task assigned: {message}")
        else:
            print(f"    [FAIL] Task assignment failed: {message}")

    db.close()

    # Clean up test database
    if os.path.exists("test_household.db"):
        os.remove("test_household.db")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("  Household Event Planner - Test Suite")
    print("=" * 60)
    print()

    all_passed = True

    try:
        if not test_database():
            all_passed = False

        if not test_models():
            all_passed = False

        if not test_services():
            all_passed = False

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  All tests passed!")
    else:
        print("  Some tests failed!")
    print("=" * 60)


if __name__ == "__main__":
    main()