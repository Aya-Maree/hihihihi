"""
User Interface module for Household Event Planner Prototype
Command-line interface for user interaction
"""

import os
import sys
from datetime import datetime
from services import AuthService, HouseholdService, CategoryService, EventService, TaskService
from rag import RAGPipeline


class CLI:
    """Command-line interface for the application"""

    def __init__(self):
        self.current_user = None
        self.current_household = None

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, text):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60)

    def print_menu(self, title, options):
        """Print a menu with options"""
        self.print_header(title)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print("-" * 60)

    def get_input(self, prompt):
        """Get user input"""
        return input(f"\n{prompt}: ").strip()

    def get_password(self, prompt):
        """Get password input (hidden)"""
        import getpass
        return getpass.getpass(f"{prompt}: ").strip()

    def press_enter(self):
        """Wait for user to press Enter"""
        input("\n  Press Enter to continue...")

    def show_error(self, message):
        """Show error message"""
        print(f"\n  ERROR: {message}")

    def show_success(self, message):
        """Show success message"""
        print(f"\n  SUCCESS: {message}")

    # ==================== AUTHENTICATION ====================

    def show_login(self):
        """Show login screen - UC2"""
        self.clear_screen()
        self.print_header("Household Event Planner - Login")

        print("\n  Welcome! Please login to continue.")
        print("  (Or type 'register' to create a new account)")

        username = self.get_input("Username")
        if username.lower() == 'register':
            self.show_register()
            return

        password = self.get_password("Password")

        success, message, user = AuthService.login(username, password)

        if success:
            self.current_user = user
            self.show_success(message)
            # Check if user has a household
            household = HouseholdService.get_household_for_user(user)
            if household:
                self.current_household = household
            else:
                self.prompt_create_household()
        else:
            self.show_error(message)
            self.press_enter()

    def show_register(self):
        """Show registration screen - UC1"""
        self.clear_screen()
        self.print_header("Household Event Planner - Register")

        print("\n  Create a new account:")
        username = self.get_input("Username")
        email = self.get_input("Email (optional)")
        password = self.get_password("Password")
        confirm = self.get_password("Confirm Password")

        if password != confirm:
            self.show_error("Passwords do not match!")
            self.press_enter()
            return

        success, message, user = AuthService.register(username, password, email if email else None)

        if success:
            self.show_success(message)
            self.current_user = user
            self.press_enter()
            self.prompt_create_household()
        else:
            self.show_error(message)
            self.press_enter()

    def prompt_create_household(self):
        """Prompt user to create a household"""
        self.clear_screen()
        self.print_header("Setup Household")

        print(f"\n  Hello, {self.current_user.username}!")
        print("  You need to create a household to get started.")

        name = self.get_input("Household name")

        if name:
            self.current_household = HouseholdService.create_household(name, self.current_user)
            self.show_success(f"Household '{name}' created successfully!")
            self.press_enter()
        else:
            self.show_error("Household name is required!")
            self.press_enter()
            self.prompt_create_household()

    def logout(self):
        """Logout user"""
        self.current_user = None
        self.current_household = None

    # ==================== DASHBOARD ====================

    def show_dashboard(self):
        """Show main dashboard - UC13"""
        self.clear_screen()
        self.print_header(f"Dashboard - {self.current_household.name}")

        # Get upcoming events
        events = EventService.get_upcoming_events(self.current_household.household_id, 7)
        tasks = TaskService.get_pending_tasks(self.current_household.household_id)

        print(f"\n  Logged in as: {self.current_user.username}")
        print(f"  Role: {self.current_user.role}")

        print("\n  --- UPCOMING EVENTS (Next 7 days) ---")
        if events:
            for event in events[:5]:
                start = event.start_time if isinstance(event.start_time, str) else event.start_time.strftime("%Y-%m-%d %H:%M")
                print(f"  • {start}: {event.title}")
        else:
            print("  No upcoming events")

        print("\n  --- PENDING TASKS ---")
        if tasks:
            for task in tasks[:5]:
                due = task.due_date if task.due_date else "No due date"
                due_str = due if isinstance(due, str) else due.strftime("%Y-%m-%d %H:%M") if due else "No due date"
                print(f"  • [{task.status}] {task.title} (Due: {due_str})")
        else:
            print("  No pending tasks")

        print("\n  --- QUICK ACTIONS ---")
        print("  1. View All Events")
        print("  2. View All Tasks")
        print("  3. Create Event")
        print("  4. Create Task")
        print("  5. Manage Categories")
        print("  6. Manage Members")
        print("  7. AI Assistant (RAG)")
        print("  8. Logout")

        choice = self.get_input("Choose option")

        if choice == '1':
            self.show_events()
        elif choice == '2':
            self.show_tasks()
        elif choice == '3':
            self.show_create_event()
        elif choice == '4':
            self.show_create_task()
        elif choice == '5':
            self.show_categories()
        elif choice == '6':
            self.show_members()
        elif choice == '7':
            self.show_ai_assistant()
        elif choice == '8':
            self.logout()
            self.show_login()
        else:
            self.show_dashboard()

    # ==================== EVENTS ====================

    def show_events(self):
        """Show events list"""
        self.clear_screen()
        self.print_header("Events")

        events = EventService.get_events(self.current_household.household_id)

        if events:
            print("\n  --- ALL EVENTS ---")
            for i, event in enumerate(events, 1):
                start = event.start_time if isinstance(event.start_time, str) else event.start_time.strftime("%Y-%m-%d %H:%M")
                print(f"  {i}. {event.title}")
                print(f"     Date: {start}")
                if event.location:
                    print(f"     Location: {event.location}")
                print()
        else:
            print("\n  No events found.")

        print("\n  1. Create Event")
        print("  2. Back to Dashboard")

        choice = self.get_input("Choose option")

        if choice == '1':
            self.show_create_event()
        elif choice == '2':
            self.show_dashboard()
        else:
            self.show_events()

    def show_create_event(self):
        """Show create event form - UC3"""
        self.clear_screen()
        self.print_header("Create Event")

        title = self.get_input("Event title")
        description = self.get_input("Description (optional)")
        start_time = self.get_input("Start time (YYYY-MM-DD HH:MM)")
        end_time = self.get_input("End time (YYYY-MM-DD HH:MM, optional)")
        location = self.get_input("Location (optional)")

        # Show categories
        categories = CategoryService.get_categories(self.current_household.household_id)
        print("\n  Available Categories:")
        for cat in categories:
            print(f"    {cat.category_id}. {cat.name}")

        category_input = self.get_input("Category ID (optional)")
        category_id = int(category_input) if category_input and category_input.isdigit() else None

        success, message, event = EventService.create_event(
            self.current_household.household_id,
            title,
            description,
            start_time,
            end_time if end_time else None,
            location,
            category_id,
            self.current_user.user_id
        )

        if success:
            self.show_success(message)
        else:
            self.show_error(message)

        self.press_enter()
        self.show_events()

    # ==================== TASKS ====================

    def show_tasks(self):
        """Show tasks list"""
        self.clear_screen()
        self.print_header("Tasks")

        tasks = TaskService.get_tasks(self.current_household.household_id)

        if tasks:
            print("\n  --- ALL TASKS ---")
            for i, task in enumerate(tasks, 1):
                due_str = task.due_date if isinstance(task.due_date, str) else (task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date")
                print(f"  {i}. [{task.status.upper()}] {task.title}")
                print(f"     Priority: {task.priority}")
                print(f"     Due: {due_str}")
                print()
        else:
            print("\n  No tasks found.")

        print("\n  1. Create Task")
        print("  2. Back to Dashboard")

        choice = self.get_input("Choose option")

        if choice == '1':
            self.show_create_task()
        elif choice == '2':
            self.show_dashboard()
        else:
            self.show_tasks()

    def show_create_task(self):
        """Show create task form - UC6"""
        self.clear_screen()
        self.print_header("Create Task")

        title = self.get_input("Task title")
        description = self.get_input("Description (optional)")
        due_date = self.get_input("Due date (YYYY-MM-DD HH:MM, optional)")

        print("\n  Priority levels: low, medium, high")
        priority = self.get_input("Priority (default: medium)").lower()
        if priority not in ['low', 'medium', 'high']:
            priority = 'medium'

        success, message, task = TaskService.create_task(
            self.current_household.household_id,
            title,
            description,
            due_date if due_date else None,
            priority,
            self.current_user.user_id
        )

        if success:
            self.show_success(message)

            # Ask to assign task
            members = HouseholdService.get_members(self.current_household.household_id)
            if members:
                print("\n  Available members:")
                for m in members:
                    print(f"    {m.member_id}. {m.name}")

                assign = self.get_input("Assign to member? (member ID or 'n')")
                if assign and assign.isdigit():
                    TaskService.assign_task(task.task_id, int(assign))
                    self.show_success("Task assigned!")
        else:
            self.show_error(message)

        self.press_enter()
        self.show_tasks()

    # ==================== CATEGORIES ====================

    def show_categories(self):
        """Show categories management - UC10"""
        self.clear_screen()
        self.print_header("Manage Categories")

        categories = CategoryService.get_categories(self.current_household.household_id)

        print("\n  --- CATEGORIES ---")
        for cat in categories:
            default = " (Default)" if cat.is_default else ""
            print(f"  {cat.category_id}. {cat.name} {default}")

        print("\n  1. Add Category")
        print("  2. Back to Dashboard")

        choice = self.get_input("Choose option")

        if choice == '1':
            self.show_add_category()
        elif choice == '2':
            self.show_dashboard()
        else:
            self.show_categories()

    def show_add_category(self):
        """Add a new category"""
        self.clear_screen()
        self.print_header("Add Category")

        name = self.get_input("Category name")

        print("\n  Colors available: #3498db (blue), #e74c3c (red), #2ecc71 (green), #f39c12 (orange), #9b59b6 (purple)")
        color = self.get_input("Color (hex code, default: #3498db)")
        if not color:
            color = "#3498db"

        category, message = CategoryService.create_category(
            self.current_household.household_id,
            name,
            color
        )

        if category:
            self.show_success(message)
        else:
            self.show_error(message)

        self.press_enter()
        self.show_categories()

    # ==================== MEMBERS ====================

    def show_members(self):
        """Show household members"""
        self.clear_screen()
        self.print_header("Household Members")

        members = HouseholdService.get_members(self.current_household.household_id)

        print("\n  --- MEMBERS ---")
        for m in members:
            print(f"  • {m.name} ({m.relationship})")

        print("\n  1. Add Member")
        print("  2. Back to Dashboard")

        choice = self.get_input("Choose option")

        if choice == '1':
            self.show_add_member()
        elif choice == '2':
            self.show_dashboard()
        else:
            self.show_members()

    def show_add_member(self):
        """Add a new household member"""
        self.clear_screen()
        self.print_header("Add Member")

        name = self.get_input("Member name")
        relationship = self.get_input("Relationship (e.g., Spouse, Child, Roommate)")

        member = HouseholdService.add_member(
            self.current_household.household_id,
            name,
            relationship
        )

        self.show_success(f"Member '{name}' added!")
        self.press_enter()
        self.show_members()

    # ==================== AI ASSISTANT (RAG) ====================

    def show_ai_assistant(self):
        """Show AI Assistant with RAG pipeline"""
        self.clear_screen()
        self.print_header("AI Assistant - RAG Pipeline Demo")

        print("\n  Ask me about your events and tasks!")
        print("  Examples: 'What events do I have?', 'Show my pending tasks'")
        print("  'When is my event?', 'List all tasks'")

        # Initialize RAG pipeline
        rag = RAGPipeline(self.current_household.household_id)

        # Load documents
        docs = rag.document_store.load_documents()
        print(f"\n  Loaded {len(docs)} documents from your household database")

        print("\n" + "-" * 50)

        # Interactive Q&A
        while True:
            question = self.get_input("\nYour question (or 'back' to exit)")

            if question.lower() == 'back':
                break

            if not question:
                continue

            print("\n  [RAG Pipeline Processing...]")
            print("  Step 1: Retrieving relevant documents...")
            print("  Step 2: Generating response...")

            response = rag.query(question)

            print("\n  === AI Response ===")
            print(response)
            print("=" * 50)

        self.show_dashboard()

    # ==================== MAIN ====================

    def run(self):
        """Run the application"""
        self.show_login()

        while self.current_user and self.current_household:
            self.show_dashboard()


def main():
    """Main entry point"""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()