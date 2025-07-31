import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Conversation
from services.vector_store import VectorStore

def clear_all_conversations():
    db = SessionLocal()
    vector_store = VectorStore()
    
    try:
        # Delete all conversations from database
        deleted_count = db.query(Conversation).count()
        db.query(Conversation).delete()
        db.commit()
        print(f"Deleted {deleted_count} conversations from database")
        
        # Clear vector store collections
        try:
            vector_store.conversations_collection.delete(where={})
            print("Cleared conversations from vector store")
        except Exception as e:
            print(f"Warning: Could not clear vector store: {e}")
            
    except Exception as e:
        print(f"Error clearing conversations: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("All conversations cleared successfully")

if __name__ == "__main__":
    response = input("Are you sure you want to delete all conversations? This cannot be undone. (yes/no): ")
    if response.lower() == 'yes':
        clear_all_conversations()
    else:
        print("Operation cancelled")