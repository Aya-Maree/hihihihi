================================================================================
                    ENVIRONMENT CONFIGURATION
                    Household Event Planner - Prototype
================================================================================

--------------------------------------------------------------------------------
1. REQUIREMENTS
--------------------------------------------------------------------------------

Python Version:
  - Python 3.8 or higher
  - Check version: python --version

Operating System:
  - Windows 10/11
  - macOS
  - Linux

--------------------------------------------------------------------------------
2. DEPENDENCIES
--------------------------------------------------------------------------------

NO EXTERNAL PACKAGES REQUIRED!

This prototype uses only Python's built-in standard library:

  Module        Purpose                   
  ------------  --------------------------
  sqlite3       Database operations        
  getpass      Secure password input      
  os           File system operations    
  datetime     Date and time handling    
  hashlib      Password encryption       
  re           Regular expressions       
  sys          System parameters          

--------------------------------------------------------------------------------
3. ENVIRONMENT SETUP
--------------------------------------------------------------------------------

Step 1: Verify Python Installation
  Open terminal/command prompt and run:
    python --version
    python -m pip --version

  Expected output: Python 3.8.x or higher

Step 2: Navigate to Prototype Directory
  cd "path/to/project-phase-1-group-2-1/prototype"

Step 3: Run the Application
  python main.py

Step 4: Run Tests (Optional)
  python test.py

--------------------------------------------------------------------------------
4. FILE STRUCTURE
--------------------------------------------------------------------------------

project-phase-1-group-2-1/
  ├── prototype/
  │    ├── main.py         # Main application entry point
  │    ├── database.py     # SQLite database setup
  │    ├── models.py       # Data models
  │    ├── services.py     # Business logic
  │    ├── ui.py          # Command-line interface
  │    ├── test.py        # Test suite
  │    ├── README.md      # Usage instructions
  │    └── household_planner.db  # Created on first run

--------------------------------------------------------------------------------
5. TROUBLESHOOTING
--------------------------------------------------------------------------------

Issue: "python is not recognized"
Solution: Add Python to system PATH, or use full path to python.exe

Issue: "Module not found"
Solution: Should not happen - all modules are built-in. Try reinstalling Python.

Issue: Database locked
Solution: Close any other applications accessing the database file

--------------------------------------------------------------------------------
6. OUTPUT FILES
--------------------------------------------------------------------------------

The application creates these files automatically:

  - household_planner.db  (SQLite database with all data)
  - test_household.db     (temporary test database)

Both can be deleted to reset the application to a clean state.

================================================================================