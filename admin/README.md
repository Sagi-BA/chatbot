# Admin Panel Module
## Matnas Chatbot - Phase 1

**Version:** 1.0.0
**Phase:** Authentication & User Management
**Date:** November 2025

---

## 📁 Module Structure

```
admin/
├── __init__.py          # Package initialization
├── auth.py              # Authentication & session management
├── users.py             # User CRUD operations & UI
├── dashboard.py         # Admin dashboard & statistics
├── backup.py            # Backup utilities
├── styles.css           # RTL Hebrew styles
└── README.md            # This file
```

---

## 📚 Module Documentation

### auth.py

**Purpose:** Authentication, password hashing, session management

**Key Functions:**
- `hash_password(password)` - Hash password with bcrypt
- `verify_password(password, hashed)` - Verify password
- `authenticate_user(username, password)` - Login authentication
- `is_authenticated()` - Check if session is valid
- `get_current_user()` - Get current user info
- `login_user(user, remember_me)` - Set session state
- `logout()` - Clear session
- `extend_session()` - Reset timeout timer
- `require_auth(func)` - Decorator for protected functions
- `require_role(role)` - Decorator for role-based access
- `log_audit_event(type, username, details)` - Log actions

**Constants:**
- `SESSION_TIMEOUT_MINUTES = 30`
- `WARNING_BEFORE_TIMEOUT_MINUTES = 5`
- `MAX_LOGIN_ATTEMPTS = 5`
- `LOCKOUT_DURATION_MINUTES = 15`

---

### users.py

**Purpose:** User management CRUD operations

**Key Functions:**
- `load_users()` - Load users from JSON
- `save_users(data)` - Save users to JSON
- `validate_username(username)` - Validate username format
- `validate_email(email)` - Validate email format
- `validate_password(password)` - Validate password strength
- `get_password_strength(password)` - Calculate strength (0-4)
- `username_exists(username)` - Check for duplicates
- `create_initial_super_admin()` - First-run setup
- `add_user(username, email, password, role)` - Create user
- `update_user(user_id, updates)` - Modify user
- `delete_user(user_id)` - Remove user
- `list_users()` - Get all users (without passwords)
- `get_user_by_id(user_id)` - Get single user
- `change_password(user_id, new_password)` - Update password
- `render_user_management()` - UI for user management
- `render_user_list()` - Display users table
- `render_edit_user_form(user)` - Edit form
- `render_add_user_form()` - Add form

**Roles:**
```python
ROLES = {
    "super_admin": "מנהל ראשי",
    "editor": "עורך",
    "viewer": "צופה"
}
```

---

### dashboard.py

**Purpose:** Admin dashboard and statistics

**Key Functions:**
- `count_files_in_folder(folder, extension)` - File counter
- `get_file_modification_time(file_path)` - Last edit time
- `load_matnas_data()` - Load main JSON
- `get_user_count()` - Get public user count
- `render_dashboard()` - Main dashboard UI
- `render_statistics()` - Display stat cards
- `render_backup_section()` - Backup management UI
- `render_quick_actions()` - Quick action buttons

**Statistics Displayed:**
- Dialogs count
- Images count
- PDFs count
- Total users (public app)
- Admin users count
- Backups count
- Total backup size
- Last edit timestamp

---

### backup.py

**Purpose:** Backup and restore functionality

**Key Functions:**
- `ensure_backup_folder()` - Create backups folder
- `generate_backup_filename(source_file)` - Create timestamp name
- `create_backup(source_file)` - Create backup
- `list_backups(source_file)` - List all backups
- `restore_backup(backup_path, target_file)` - Restore backup
- `delete_backup(backup_path)` - Delete backup
- `cleanup_old_backups(source_file, keep_count)` - Auto-cleanup
- `get_last_backup_info(source_file)` - Last backup details
- `format_file_size(size_bytes)` - Human-readable size
- `get_backup_statistics()` - Backup stats

**Constants:**
- `BACKUP_FOLDER = 'data/backups'`
- `MAX_BACKUPS_TO_KEEP = 30`

**Backup Filename Format:**
```
basename_BACKUP_YYYYMMDD_HHMMSS.json
```

---

### styles.css

**Purpose:** RTL Hebrew styling for admin panel

**Key Features:**
- Global RTL direction
- Hebrew font stack (Heebo, Rubik, Arial)
- Right-aligned inputs
- RTL tables
- RTL navigation
- Custom metric cards
- Login page styling
- Responsive design
- Accessibility (focus states)
- Print styles

**Font Priority:**
```css
font-family: 'Heebo', 'Rubik', Arial, sans-serif;
```

---

## 🔐 Security Features

### Password Security:
- **Hashing:** bcrypt with 12 rounds
- **Requirements:** Min 8 chars, uppercase, lowercase, digit
- **Strength Meter:** 5-level visual indicator

### Login Security:
- **Attempt Limiting:** Max 5 failures
- **Lockout:** 15 minutes after 5 failures
- **Lockout Timer:** Real-time countdown

### Session Security:
- **Timeout:** 30 minutes inactivity
- **Warning:** 5 minutes before timeout
- **Extension:** Manual extend button
- **Activity Tracking:** Resets on interaction

### Access Control:
- **Role-Based:** 3 roles (Super Admin, Editor, Viewer)
- **Decorators:** `@require_auth`, `@require_role`
- **Self-Protection:** Cannot delete/demote self
- **Last Admin:** Cannot delete last super admin

### Audit Logging:
- **Events:** Login, logout, user actions
- **Storage:** `data/admin_audit.json`
- **Retention:** Last 1000 events

---

## 📦 Dependencies

```python
import streamlit as st
import bcrypt
import json
import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque
```

**External Packages:**
- `streamlit` - Web framework
- `bcrypt>=4.0.1` - Password hashing

---

## 🚀 Usage

### Importing:
```python
from admin.auth import is_authenticated, require_role
from admin.users import add_user, delete_user
from admin.dashboard import render_dashboard
from admin.backup import create_backup, restore_backup
```

### Example - Protected Function:
```python
from admin.auth import require_role

@require_role("super_admin")
def admin_only_function():
    # Only super admins can access this
    pass
```

### Example - Create User:
```python
from admin.users import add_user

success, error = add_user(
    username="newadmin",
    email="admin@example.com",
    password="SecurePass123",
    role="editor"
)

if success:
    print("User created!")
else:
    print(f"Error: {error}")
```

### Example - Create Backup:
```python
from admin.backup import create_backup

success, path = create_backup("data/matnas_data.json")

if success:
    print(f"Backup created: {path}")
else:
    print(f"Error: {path}")
```

---

## 🗂️ Data Files

### Input Files:
- `data/matnas_data.json` - Main app configuration (read-only in Phase 1)
- `data/user_count.json` - Public user counter (read-only)

### Output Files:
- `data/admin_users.json` - Admin user accounts
- `data/admin_audit.json` - Audit log
- `data/backups/*.json` - Backup files

### File Permissions:
- All JSON files: Read/Write
- Backups folder: Read/Write/Delete

---

## 🧪 Testing

### Unit Tests:
```python
# Run syntax check
python -m py_compile admin/*.py

# Import test
python -c "from admin.auth import hash_password; print('OK')"
```

### Manual Testing:
1. Login with valid credentials
2. Login with invalid credentials
3. Create new user
4. Edit user
5. Delete user
6. Create backup
7. Restore backup
8. Test Hebrew RTL display
9. Test session timeout
10. Test role permissions

---

## 🔍 Troubleshooting

### Import Errors:
```python
# Make sure you're in the project root
import sys
sys.path.append('/path/to/chatbot')
```

### bcrypt Not Found:
```bash
pip install bcrypt>=4.0.1
```

### CSS Not Loading:
```python
# Verify file exists
import os
print(os.path.exists('admin/styles.css'))  # Should be True
```

### Session Not Persisting:
```python
# Check session state
import streamlit as st
print(st.session_state.get('admin_authenticated', False))
```

---

## 📝 Code Style

### Naming Conventions:
- **Functions:** `snake_case`
- **Classes:** `PascalCase` (none in Phase 1)
- **Constants:** `UPPER_CASE`
- **Private:** `_leading_underscore`

### Docstrings:
```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    pass
```

### Type Hints:
```python
from typing import Dict, List, Optional, Tuple

def func(data: Dict) -> Optional[str]:
    pass
```

---

## 🌍 Internationalization

### Language:
- **UI:** Hebrew (עברית)
- **Code:** English
- **Comments:** English
- **Documentation:** Hebrew + English

### Hebrew Strings:
```python
# Error messages
"שם משתמש או סיסמה שגויים"

# Success messages
"המשתמש נוסף בהצלחה!"

# Labels
"שם משתמש", "סיסמה", "אימייל"
```

---

## 🔄 Future Enhancements (Phase 2+)

### Planned:
- [ ] Content editing (Phase 2)
- [ ] Media library (Phase 5)
- [ ] Settings management (Phase 6)
- [ ] Analytics dashboard (Phase 7)

### Possible:
- [ ] Email notifications
- [ ] Two-factor authentication (2FA)
- [ ] Password reset via email
- [ ] Bulk user operations
- [ ] Export audit logs to CSV

---

## 📞 Support

**Developer:** AI Assistant
**Client:** Sagi Baron
**Email:** sagi.baron76@gmail.com
**WhatsApp:** +972-54-999-5050

---

## 📜 License

Proprietary - Created for Matnas Ha'emek

---

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Nov 2025 | Initial release - Authentication & user management |

---

**End of Admin Module Documentation**
