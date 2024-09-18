import os
import json
import streamlit as st

# File to store user count
DATA_FOLDER = 'data'
USER_COUNT_FILE = os.path.join(DATA_FOLDER, 'user_count.json')

def initialize_user_count():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    if not os.path.exists(USER_COUNT_FILE):
        with open(USER_COUNT_FILE, 'w') as f:
            json.dump({"count": 0}, f)

def get_user_count(formatted=False):
    try:
        with open(USER_COUNT_FILE, 'r') as f:
            data = json.load(f)
        count = data.get("count", 0)
        if formatted:            
            return format_count(count)
        return count
    except (json.JSONDecodeError, FileNotFoundError):
        return 0

def increment_user_count():
    count = get_user_count()
    count += 1    
    with open(USER_COUNT_FILE, 'w') as f:
        json.dump({"count": count}, f)
    return count

def decrement_user_count():
    print("Decrementing user count")
    
    count = get_user_count()
    count = max(0, count - 1)  # Ensure count doesn't go below 0
    with open(USER_COUNT_FILE, 'w') as f:
        json.dump({"count": count}, f)
    return count

def format_count(count):
    """Format the count with commas and round to nearest thousand if over 1000"""    
    if count >= 1000:
        return f"{count:,}"
    return f"{count:,}"
