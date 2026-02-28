from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.database.schema import Transcription
from datetime import datetime, timezone
from src.database.schema import User, UserUsage


def insert_transcription(db: Session, data: dict) -> dict:
    try:
        created_at = None
        if "created_at" in data and data["created_at"]:
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            else:
                created_at = data["created_at"]
            
        transcription = Transcription(
            file_id=data["file_id"],
            transcription_text=data.get("transcription_text"),
            language=data.get("language"),
            gpt_response=data.get("gpt_response"),
            iscorrect=False,
            created_at=created_at if created_at else datetime.now(timezone.utc)
        )

        db.add(transcription)
        db.commit()
        db.refresh(transcription)

        return {
            "success": True,
            "message": "Transcription inserted successfully",
            "file_id": transcription.file_id
        }

    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }



def update_transcription_is_correct(db: Session, file_id: str) -> dict:
    
    try:
        transcription = db.query(Transcription).filter(Transcription.file_id == file_id).first()
        
        if not transcription:
            return {
                "success": False,
                "message": f"Transcription with file_id '{file_id}' not found"
            }
        
        transcription.iscorrect = True
        db.commit()
        db.refresh(transcription)
        
        return {
            "success": True,
            "message": "Record updated successfully",
            "file_id": transcription.file_id,
            "iscorrect": transcription.iscorrect
        }
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }


# Synchronous wrapper functions for compatibility with existing code
# These can be used with run_in_threadpool in FastAPI routes

def sync_insert_transcription(data: dict) -> dict:
    """
    Synchronous wrapper for insert_transcription.
    Creates its own database session for thread-safe operations.
    Used with run_in_threadpool in background tasks.
    """
    from src.utils.database_config import SessionLocal
    
    db = SessionLocal()
    try:
        result = insert_transcription(db, data)
        return result
    finally:
        db.close()



def sync_update_transcription_is_correct(file_id: str) -> dict:
    """
    Synchronous wrapper for update_transcription_is_correct.
    Creates its own database session for thread-safe operations.
    """
    from src.utils.database_config import SessionLocal
    
    db = SessionLocal()
    try:
        result = update_transcription_is_correct(db, file_id)
        return result
    finally:
        db.close()


def create_user(db: Session, user_id: str) -> dict:
    try:
        if db.query(User).filter(User.user_id == user_id).first():
            return {
                "success": False,
                "message": f"User with user_id '{user_id}' already exists"
            }
        
        user = User(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user.user_id
        }
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }



def get_user(db: Session, user_id: str) -> dict | None:
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        return {
            "success": True,
            "message": "User retrieved successfully",
            "user_id": user.user_id
        }
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}") 


def add_usage(db: Session, user_id: str, day: str, count: int) -> dict:
    if isinstance(day, str):
        day = datetime.fromisoformat(day.replace("Z", "+00:00")).date().isoformat()
    try:
        user_usage = db.query(UserUsage).filter(UserUsage.user_id == user_id, UserUsage.day == day).first()
        if user_usage:
            user_usage.usage_count += count
        else:
            user_usage = UserUsage(user_id=user_id, day=day, usage_count=count)
            db.add(user_usage)
        db.commit()
        db.refresh(user_usage)
        return {
            "success": True,
            "message": "Usage added successfully",
            "user_id": user_usage.user_id,
            "day": user_usage.day,
            "usage_count": user_usage.usage_count
        }
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }


def update_usage(db: Session, user_id: str, day: str, count: int) -> dict:
    if isinstance(day, str):
        day = datetime.fromisoformat(day.replace("Z", "+00:00")).date().isoformat()
    try:
        user_usage = db.query(UserUsage).filter(UserUsage.user_id == user_id, UserUsage.day == day).first()
        if not user_usage:
            return {
                "success": False,
                "message": f"User usage with user_id '{user_id}' and day '{day}' not found"
            }
        user_usage.usage_count = count
        db.commit()
        db.refresh(user_usage)
        return {
            "success": True,
            "message": "Usage updated successfully",
            "user_id": user_usage.user_id,
            "day": user_usage.day,
            "usage_count": user_usage.usage_count  }
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }


def get_usage(db: Session, user_id: str, day: str) -> int:
    try:
        if isinstance(day, str):
            day = datetime.fromisoformat(day.replace("Z", "+00:00")).date().isoformat()
        user_usage = db.query(UserUsage).filter(UserUsage.user_id == user_id, UserUsage.day == day).first()
        if user_usage:
            return user_usage.usage_count
        return 0
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}")
        return 0
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return 0