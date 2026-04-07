"""
Database Initialization Script
Run this script to initialize the database and create all tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, reset_database
from config.settings import ensure_directories


def main():
    print("=" * 60)
    print("NCCR Rehabilitation System - Database Initialization")
    print("=" * 60)
    print()
    
    # Ensure all directories exist
    print("📁 Creating required directories...")
    ensure_directories()
    print("✅ Directories created\n")
    
    # Initialize database
    print("🗄️  Initializing database...")
    init_db()
    print("✅ Database initialized successfully\n")
    
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run the application: python main.py")
    print("2. Import your data using the API endpoints")
    print("3. Access the dashboard at http://localhost:8000")
    print()


if __name__ == "__main__":
    main()
