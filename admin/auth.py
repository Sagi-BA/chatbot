"""
Authentication Module for Admin Panel
Handles user authentication, password hashing, and session management
"""

import streamlit as st
import bcrypt
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict


# Constants
SESSION_TIMEOUT_MINUTES = 30
WARNING_BEFORE_TIMEOUT_MINUTES = 5
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with 12 rounds.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def load_admin_users() -> Dict:
    """
    Load admin users from JSON file.

    Returns:
        Dictionary containing users data
    """
    users_file = os.path.join('data', 'admin_users.json')

    if not os.path.exists(users_file):
        return {"users": []}

    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading admin users: {e}")
        return {"users": []}


def save_admin_users(data: Dict) -> bool:
    """
    Save admin users to JSON file.

    Args:
        data: Dictionary containing users data

    Returns:
        True if successful, False otherwise
    """
    users_file = os.path.join('data', 'admin_users.json')

    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving admin users: {e}")
        return False


def get_lockout_key(username: str) -> str:
    """Get session state key for login lockout."""
    return f"login_lockout_{username}"


def get_attempts_key(username: str) -> str:
    """Get session state key for login attempts."""
    return f"login_attempts_{username}"


def is_locked_out(username: str) -> bool:
    """
    Check if user is locked out due to failed login attempts.

    Args:
        username: Username to check

    Returns:
        True if locked out, False otherwise
    """
    lockout_key = get_lockout_key(username)

    if lockout_key not in st.session_state:
        return False

    lockout_time = st.session_state[lockout_key]
    if datetime.now() > lockout_time:
        # Lockout expired
        del st.session_state[lockout_key]
        if get_attempts_key(username) in st.session_state:
            del st.session_state[get_attempts_key(username)]
        return False

    return True


def get_lockout_remaining_time(username: str) -> int:
    """
    Get remaining lockout time in seconds.

    Args:
        username: Username to check

    Returns:
        Remaining seconds, or 0 if not locked out
    """
    lockout_key = get_lockout_key(username)

    if lockout_key not in st.session_state:
        return 0

    lockout_time = st.session_state[lockout_key]
    remaining = (lockout_time - datetime.now()).total_seconds()
    return max(0, int(remaining))


def record_failed_attempt(username: str) -> int:
    """
    Record a failed login attempt.

    Args:
        username: Username that failed

    Returns:
        Number of attempts so far
    """
    attempts_key = get_attempts_key(username)

    if attempts_key not in st.session_state:
        st.session_state[attempts_key] = 0

    st.session_state[attempts_key] += 1
    attempts = st.session_state[attempts_key]

    # Lock out if max attempts reached
    if attempts >= MAX_LOGIN_ATTEMPTS:
        lockout_key = get_lockout_key(username)
        st.session_state[lockout_key] = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    return attempts


def reset_failed_attempts(username: str):
    """
    Reset failed login attempts for a user.

    Args:
        username: Username to reset
    """
    attempts_key = get_attempts_key(username)
    if attempts_key in st.session_state:
        del st.session_state[attempts_key]


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User dictionary (without password) if successful, None otherwise
    """
    # Check lockout
    if is_locked_out(username):
        return None

    # Load users
    data = load_admin_users()
    users = data.get("users", [])

    # Find user
    user = None
    for u in users:
        if u.get("username") == username and u.get("is_active", True):
            user = u
            break

    if not user:
        record_failed_attempt(username)
        return None

    # Verify password
    if not verify_password(password, user.get("password_hash", "")):
        record_failed_attempt(username)
        return None

    # Reset failed attempts on successful login
    reset_failed_attempts(username)

    # Update last login
    user["last_login"] = datetime.now().isoformat()
    save_admin_users(data)

    # Return user without password
    user_copy = user.copy()
    user_copy.pop("password_hash", None)

    return user_copy


def is_authenticated() -> bool:
    """
    Check if current session is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    if not st.session_state.get("admin_authenticated", False):
        return False

    # Check session timeout
    if "admin_login_time" in st.session_state:
        login_time = st.session_state["admin_login_time"]
        elapsed = (datetime.now() - login_time).total_seconds() / 60

        if elapsed > SESSION_TIMEOUT_MINUTES:
            # Session expired
            logout()
            return False

        # Check if warning needed
        if elapsed > (SESSION_TIMEOUT_MINUTES - WARNING_BEFORE_TIMEOUT_MINUTES):
            st.session_state["admin_session_warning"] = True

    return True


def get_current_user() -> Optional[Dict]:
    """
    Get current authenticated user.

    Returns:
        User dictionary or None if not authenticated
    """
    if not is_authenticated():
        return None

    return st.session_state.get("admin_user")


def login_user(user: Dict, remember_me: bool = False):
    """
    Log in a user and set session state.

    Args:
        user: User dictionary
        remember_me: Whether to remember the user
    """
    st.session_state["admin_authenticated"] = True
    st.session_state["admin_user"] = user
    st.session_state["admin_remember_me"] = remember_me
    st.session_state["admin_login_time"] = datetime.now()
    st.session_state["admin_session_warning"] = False
    st.session_state["admin_page"] = "dashboard"


def extend_session():
    """
    Extend the current session by resetting the login time.
    """
    if is_authenticated():
        st.session_state["admin_login_time"] = datetime.now()
        st.session_state["admin_session_warning"] = False


def logout():
    """
    Log out the current user and clear session state.
    """
    # Clear admin-related session state
    keys_to_clear = [
        "admin_authenticated",
        "admin_user",
        "admin_remember_me",
        "admin_login_time",
        "admin_session_warning",
        "admin_page"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def require_auth(func):
    """
    Decorator to require authentication for a function.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("נדרשת הזדהות. אנא התחבר מחדש.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_role(required_role: str):
    """
    Decorator to require a specific role for a function.

    Args:
        required_role: Required role (super_admin, editor, viewer)

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                st.error("נדרשת הזדהות. אנא התחבר מחדש.")
                st.stop()

            user = get_current_user()
            user_role = user.get("role", "viewer")

            # Role hierarchy: super_admin > editor > viewer
            roles_hierarchy = ["viewer", "editor", "super_admin"]

            if roles_hierarchy.index(user_role) < roles_hierarchy.index(required_role):
                st.error("אין לך הרשאות מספיקות לגשת לעמוד זה.")
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_audit_event(event_type: str, username: str, details: str = ""):
    """
    Log an audit event (foundation for Phase 7).

    Args:
        event_type: Type of event (login, logout, user_created, etc.)
        username: Username associated with event
        details: Additional details
    """
    audit_file = os.path.join('data', 'admin_audit.json')

    # Load existing audit log
    if os.path.exists(audit_file):
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)
        except:
            audit_data = {"events": []}
    else:
        audit_data = {"events": []}

    # Add new event
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "username": username,
        "details": details
    }

    audit_data["events"].append(event)

    # Keep only last 1000 events
    if len(audit_data["events"]) > 1000:
        audit_data["events"] = audit_data["events"][-1000:]

    # Save
    try:
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error logging audit event: {e}")
