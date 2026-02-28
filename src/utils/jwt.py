import jwt
import os
from datetime import datetime, timezone, timedelta
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv

load_dotenv(override=True)
# Move these later to .env file.
# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
# JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS"))


JWT_SECRET_KEY = "fastapi-ubl-jwt-secret-key"
JWT_EXPIRATION_HOURS = 24*30

def generate_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def validate_jwt_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error validating token: {str(e)}")