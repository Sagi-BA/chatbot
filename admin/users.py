"""
User Management Module for Admin Panel
Handles CRUD operations for admin users
"""

import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from admin.auth import hash_password, get_current_user, require_role, log_audit_event


# User roles
ROLES = {
    "super_admin": "מנהל ראשי",
    "editor": "עורך",
    "viewer": "צופה"
}


def load_users() -> Dict:
    """
    Load all users from JSON file.

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
        print(f"Error loading users: {e}")
        return {"users": []}


def save_users(data: Dict) -> bool:
    """
    Save users to JSON file.

    Args:
        data: Dictionary containing users data

    Returns:
        True if successful, False otherwise
    """
    users_file = os.path.join('data', 'admin_users.json')

    try:
        # Create backup before saving
        from admin.backup import create_backup
        create_backup(users_file)

        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "שם משתמש לא יכול להיות רק."

    if len(username) < 3:
        return False, "שם משתמש חייב להכיל לפחות 3 תווים."

    if len(username) > 20:
        return False, "שם משתמש לא יכול להיות יותר מ-20 תווים."

    # Allow alphanumeric and underscore only
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "שם משתמש יכול להכיל רק אותיות אנגליות, מספרים וקו תחתון (_)."

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "כתובת אימייל לא יכולה להיות ריקה."

    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "כתובת אימייל לא תקינה."

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "סיסמה לא יכולה להיות ריקה."

    if len(password) < 8:
        return False, "סיסמה חייבת להכיל לפחות 8 תווים."

    # Check for at least one uppercase
    if not re.search(r'[A-Z]', password):
        return False, "סיסמה חייבת להכיל לפחות אות גדולה אחת באנגלית."

    # Check for at least one lowercase
    if not re.search(r'[a-z]', password):
        return False, "סיסמה חייבת להכיל לפחות אות קטנה אחת באנגלית."

    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False, "סיסמה חייבת להכיל לפחות ספרה אחת."

    return True, ""


def get_password_strength(password: str) -> Tuple[int, str]:
    """
    Calculate password strength.

    Args:
        password: Password to evaluate

    Returns:
        Tuple of (strength_score, strength_label)
        strength_score: 0-4 (weak to very strong)
        strength_label: Hebrew label
    """
    score = 0

    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[0-9]', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1

    strength_labels = {
        0: "חלשה מאוד",
        1: "חלשה",
        2: "בינונית",
        3: "חזקה",
        4: "חזקה מאוד",
        5: "חזקה מאוד"
    }

    return min(score, 4), strength_labels.get(score, "חלשה")


def username_exists(username: str, exclude_id: Optional[str] = None) -> bool:
    """
    Check if username already exists.

    Args:
        username: Username to check
        exclude_id: User ID to exclude from check (for updates)

    Returns:
        True if username exists, False otherwise
    """
    data = load_users()
    users = data.get("users", [])

    for user in users:
        if user.get("username") == username:
            if exclude_id and user.get("id") == exclude_id:
                continue
            return True

    return False


def create_initial_super_admin() -> bool:
    """
    Create initial super admin account if no users exist.

    Returns:
        True if created, False if already exists
    """
    data = load_users()
    users = data.get("users", [])

    if len(users) > 0:
        return False  # Users already exist

    # Create initial super admin
    initial_user = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password_hash": hash_password("Admin@Matnas2025"),
        "email": "sagi.baron76@gmail.com",
        "role": "super_admin",
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True,
        "must_change_password": True
    }

    data["users"] = [initial_user]
    save_users(data)

    log_audit_event("user_created", "system", "Initial super admin created")

    return True


def add_user(username: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    """
    Add a new user.

    Args:
        username: Username
        email: Email address
        password: Plain text password
        role: User role (super_admin, editor, viewer)

    Returns:
        Tuple of (success, error_message)
    """
    # Validate inputs
    valid, error = validate_username(username)
    if not valid:
        return False, error

    valid, error = validate_email(email)
    if not valid:
        return False, error

    valid, error = validate_password(password)
    if not valid:
        return False, error

    # Check if username exists
    if username_exists(username):
        return False, f"שם המשתמש '{username}' כבר קיים במערכת."

    # Validate role
    if role not in ROLES:
        return False, "תפקיד לא תקין."

    # Create new user
    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": hash_password(password),
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True,
        "must_change_password": False
    }

    # Load and save
    data = load_users()
    if "users" not in data:
        data["users"] = []

    data["users"].append(new_user)

    if save_users(data):
        current_user = get_current_user()
        log_audit_event("user_created", current_user.get("username", "unknown"),
                       f"Created user: {username} with role: {role}")
        return True, ""
    else:
        return False, "שגיאה בשמירת המשתמש. אנא נסה שוב."


def update_user(user_id: str, updates: Dict) -> Tuple[bool, str]:
    """
    Update a user's information.

    Args:
        user_id: User ID to update
        updates: Dictionary of fields to update

    Returns:
        Tuple of (success, error_message)
    """
    data = load_users()
    users = data.get("users", [])

    # Find user
    user_index = None
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            user_index = i
            break

    if user_index is None:
        return False, "משתמש לא נמצא."

    current_user = get_current_user()

    # Prevent self-role-change
    if current_user and current_user.get("id") == user_id and "role" in updates:
        return False, "אינך יכול לשנות את התפקיד של עצמך."

    # Validate email if being updated
    if "email" in updates:
        valid, error = validate_email(updates["email"])
        if not valid:
            return False, error

    # Validate role if being updated
    if "role" in updates and updates["role"] not in ROLES:
        return False, "תפקיד לא תקין."

    # Update user
    for key, value in updates.items():
        if key in ["email", "role", "is_active"]:
            users[user_index][key] = value

    data["users"] = users

    if save_users(data):
        log_audit_event("user_updated", current_user.get("username", "unknown"),
                       f"Updated user ID: {user_id}")
        return True, ""
    else:
        return False, "שגיאה בעדכון המשתמש. אנא נסה שוב."


def delete_user(user_id: str) -> Tuple[bool, str]:
    """
    Delete a user.

    Args:
        user_id: User ID to delete

    Returns:
        Tuple of (success, error_message)
    """
    data = load_users()
    users = data.get("users", [])

    current_user = get_current_user()

    # Prevent self-deletion
    if current_user and current_user.get("id") == user_id:
        return False, "אינך יכול למחוק את עצמך."

    # Find user
    user_to_delete = None
    for user in users:
        if user.get("id") == user_id:
            user_to_delete = user
            break

    if not user_to_delete:
        return False, "משתמש לא נמצא."

    # Check if this is the last super admin
    super_admin_count = sum(1 for u in users if u.get("role") == "super_admin")
    if user_to_delete.get("role") == "super_admin" and super_admin_count <= 1:
        return False, "לא ניתן למחוק את מנהל הראשי היחיד במערכת."

    # Delete user
    data["users"] = [u for u in users if u.get("id") != user_id]

    if save_users(data):
        log_audit_event("user_deleted", current_user.get("username", "unknown"),
                       f"Deleted user: {user_to_delete.get('username')}")
        return True, ""
    else:
        return False, "שגיאה במחיקת המשתמש. אנא נסה שוב."


def list_users() -> List[Dict]:
    """
    Get list of all users without passwords.

    Returns:
        List of user dictionaries
    """
    data = load_users()
    users = data.get("users", [])

    # Remove password hashes
    users_without_passwords = []
    for user in users:
        user_copy = user.copy()
        user_copy.pop("password_hash", None)
        users_without_passwords.append(user_copy)

    return users_without_passwords


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """
    Get a user by ID.

    Args:
        user_id: User ID

    Returns:
        User dictionary (without password) or None
    """
    data = load_users()
    users = data.get("users", [])

    for user in users:
        if user.get("id") == user_id:
            user_copy = user.copy()
            user_copy.pop("password_hash", None)
            return user_copy

    return None


def change_password(user_id: str, new_password: str, clear_must_change: bool = False) -> Tuple[bool, str]:
    """
    Change a user's password.

    Args:
        user_id: User ID
        new_password: New plain text password
        clear_must_change: Whether to clear the must_change_password flag

    Returns:
        Tuple of (success, error_message)
    """
    # Validate password
    valid, error = validate_password(new_password)
    if not valid:
        return False, error

    data = load_users()
    users = data.get("users", [])

    # Find user
    user_index = None
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            user_index = i
            break

    if user_index is None:
        return False, "משתמש לא נמצא."

    # Update password
    users[user_index]["password_hash"] = hash_password(new_password)

    if clear_must_change:
        users[user_index]["must_change_password"] = False

    data["users"] = users

    if save_users(data):
        current_user = get_current_user()
        log_audit_event("password_changed", current_user.get("username", "unknown"),
                       f"Password changed for user ID: {user_id}")
        return True, ""
    else:
        return False, "שגיאה בשינוי הסיסמה. אנא נסה שוב."


@require_role("super_admin")
def render_user_management():
    """
    Render user management interface (super admin only).
    """
    st.header("👥 ניהול משתמשים")

    # Tabs
    tab1, tab2 = st.tabs(["רשימת משתמשים", "הוסף משתמש חדש"])

    with tab1:
        render_user_list()

    with tab2:
        render_add_user_form()


def render_user_list():
    """Render the user list table."""
    st.subheader("רשימת משתמשים")

    users = list_users()

    if not users:
        st.info("אין משתמשים במערכת.")
        return

    current_user = get_current_user()

    # Display users in a table
    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 1, 2])

            with col1:
                st.write(f"**{user.get('username')}**")

            with col2:
                st.write(user.get('email', 'N/A'))

            with col3:
                role_label = ROLES.get(user.get('role'), user.get('role'))
                st.write(role_label)

            with col4:
                if user.get('is_active', True):
                    st.success("פעיל")
                else:
                    st.error("לא פעיל")

            with col5:
                # Edit and delete buttons
                col_edit, col_delete = st.columns(2)

                with col_edit:
                    if st.button("✏️", key=f"edit_{user.get('id')}", help="ערוך משתמש"):
                        st.session_state[f"editing_user_{user.get('id')}"] = True
                        st.rerun()

                with col_delete:
                    # Only show delete if not self and not last super admin
                    can_delete = user.get('id') != current_user.get('id')
                    if can_delete:
                        if st.button("🗑️", key=f"delete_{user.get('id')}", help="מחק משתמש"):
                            st.session_state[f"confirm_delete_{user.get('id')}"] = True
                            st.rerun()

            # Show edit form if editing
            if st.session_state.get(f"editing_user_{user.get('id')}", False):
                render_edit_user_form(user)

            # Show delete confirmation
            if st.session_state.get(f"confirm_delete_{user.get('id')}", False):
                st.warning(f"האם אתה בטוח שברצונך למחוק את המשתמש '{user.get('username')}'?")
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, מחק", key=f"confirm_yes_{user.get('id')}"):
                        success, error = delete_user(user.get('id'))
                        if success:
                            st.success("המשתמש נמחק בהצלחה!")
                            del st.session_state[f"confirm_delete_{user.get('id')}"]
                            st.rerun()
                        else:
                            st.error(error)

                with col_no:
                    if st.button("ביטול", key=f"confirm_no_{user.get('id')}"):
                        del st.session_state[f"confirm_delete_{user.get('id')}"]
                        st.rerun()

            st.divider()


def render_edit_user_form(user: Dict):
    """Render edit form for a user."""
    with st.form(key=f"edit_form_{user.get('id')}"):
        st.subheader(f"ערוך משתמש: {user.get('username')}")

        email = st.text_input("אימייל", value=user.get('email', ''))
        role = st.selectbox("תפקיד", options=list(ROLES.keys()),
                           format_func=lambda x: ROLES[x],
                           index=list(ROLES.keys()).index(user.get('role', 'viewer')))
        is_active = st.checkbox("חשבון פעיל", value=user.get('is_active', True))

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("שמור שינויים", use_container_width=True)

        with col2:
            cancelled = st.form_submit_button("ביטול", use_container_width=True)

        if submitted:
            updates = {
                "email": email,
                "role": role,
                "is_active": is_active
            }

            success, error = update_user(user.get('id'), updates)

            if success:
                st.success("המשתמש עודכן בהצלחה!")
                del st.session_state[f"editing_user_{user.get('id')}"]
                st.rerun()
            else:
                st.error(error)

        if cancelled:
            del st.session_state[f"editing_user_{user.get('id')}"]
            st.rerun()


def render_add_user_form():
    """Render form to add a new user."""
    st.subheader("הוסף משתמש חדש")

    with st.form("add_user_form"):
        username = st.text_input("שם משתמש", help="אותיות אנגליות, מספרים וקו תחתון בלבד")
        email = st.text_input("אימייל")
        password = st.text_input("סיסמה", type="password",
                                help="לפחות 8 תווים, עם אות גדולה, אות קטנה וספרה")

        # Password strength meter
        if password:
            strength_score, strength_label = get_password_strength(password)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(strength_score / 4)
            with col2:
                st.write(f"חוזק: {strength_label}")

        role = st.selectbox("תפקיד", options=list(ROLES.keys()),
                           format_func=lambda x: ROLES[x])

        submitted = st.form_submit_button("הוסף משתמש", use_container_width=True)

        if submitted:
            success, error = add_user(username, email, password, role)

            if success:
                st.success(f"המשתמש '{username}' נוסף בהצלחה!")
                st.rerun()
            else:
                st.error(error)
