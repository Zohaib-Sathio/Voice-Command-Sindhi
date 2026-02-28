import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.config import init_db, engine
from src.database.schema import Transcription, User, UserUsage

if __name__ == "__main__":
    print("🚀 Initializing MySQL database...")
    print(f"Database URL: {engine.url}")

    try:
        init_db()
        print("\n✅ Database initialization completed successfully!")
        print("\nCreated tables:")
        print("  - transcriptions")
        print("  - users")
        print("  - user_usage")
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        print("\nPlease check:")
        print("  1. MySQL server is running and accessible")
        print("  2. Database credentials in .env file are correct")
        print("  3. Database exists (CREATE DATABASE fortvoice_db; if needed)")
        print("  4. User has CREATE TABLE permissions")
        sys.exit(1)
