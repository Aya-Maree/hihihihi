"""
Household Event Planner - Prototype
Main entry point

This prototype demonstrates the following use cases:
- UC1: Register User
- UC2: Login
- UC3: Create Event
- UC6: Create Task
- UC7: Assign Task
- UC10: Manage Categories

Requirements:
- Python 3.8 or higher
- No external dependencies required

Usage:
    python main.py
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import main


if __name__ == "__main__":
    print("=" * 60)
    print("  Household Event Planner - Prototype")
    print("  SE 4471B - Phase 2 Deliverable")
    print("=" * 60)
    print()
    print("  Starting application...")
    print()

    main()