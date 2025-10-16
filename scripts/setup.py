#!/usr/bin/env python3
"""
Setup script for PubMed ETL Application
This script helps users set up the database and run initial data loading.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import psycopg2
from src.database.database import DatabaseManager
from src.etl.pubmed_etl import PubMedETL

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit', 'requests', 'psycopg2', 'pandas', 
        'python-dotenv', 'openai', 'sqlalchemy', 'beautifulsoup4'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_database_connection():
    """Check if database connection is working"""
    print("\n🔍 Checking database connection...")
    
    try:
        db = DatabaseManager()
        # Try to create tables to test connection
        db.create_tables()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nPlease check your database configuration:")
        print("1. Ensure PostgreSQL is running")
        print("2. Verify database credentials in .env file")
        print("3. Make sure the database 'pubmed_db' exists")
        return False

def check_environment():
    """Check environment configuration"""
    print("\n🔍 Checking environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Creating .env file with default values...")
        
        env_content = """# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pubmed_db
DB_USER=postgres
DB_PASSWORD=postgres

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file with default values")
        print("⚠️  Please update the database password and add your OpenAI API key if needed")
        return False
    else:
        print("✅ .env file found")
    
    # Check OpenAI API key
    from config import OPENAI_API_KEY
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not configured (Q&A feature will be disabled)")
    
    return True

def run_initial_etl():
    """Run the initial ETL process to load sample data"""
    print("\n🚀 Running initial ETL process...")
    print("This will fetch articles about 'machine learning medicine' from PubMed")
    
    try:
        etl = PubMedETL()
        etl.process_articles("machine learning medicine", max_articles=50)  # Start with fewer articles
        print("✅ ETL process completed successfully!")
        return True
    except Exception as e:
        print(f"❌ ETL process failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🔬 PubMed ETL Application Setup")
    print("=" * 40)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Check environment
    if not check_environment():
        print("\n⚠️  Please configure your .env file and run setup again")
        sys.exit(1)
    
    # Step 3: Check database connection
    if not check_database_connection():
        sys.exit(1)
    
    # Step 4: Ask if user wants to run initial ETL
    print("\n" + "=" * 40)
    response = input("Would you like to run the initial ETL process to load sample data? (y/n): ").lower()
    
    if response in ['y', 'yes']:
        if run_initial_etl():
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Run: streamlit run streamlit_app.py")
            print("2. Open your browser to http://localhost:8501")
            print("3. Explore the data using the Search, Details, and Q&A tabs")
        else:
            print("\n⚠️  Setup completed but ETL failed. You can run it later with:")
            print("python pubmed_etl.py")
    else:
        print("\n✅ Setup completed!")
        print("\nTo load data later, run:")
        print("python pubmed_etl.py")
        print("\nTo start the web interface:")
        print("streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()
