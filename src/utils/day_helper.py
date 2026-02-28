from datetime import datetime

def get_current_day() -> str:
    return datetime.now().strftime("%Y-%m-%d")