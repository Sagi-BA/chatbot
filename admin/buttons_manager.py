"""
Main Buttons Manager Module for Admin Panel
Allows editing of main navigation buttons
"""

import streamlit as st
import json
import re
from typing import Dict, List, Tuple
from admin.auth import require_role, get_current_user, log_audit_event
from admin.backup import create_backup


# Constants
MATNAS_DATA_FILE = "matnas_data.json"


def load_matnas_data() -> Dict:
    """Load matnas data from JSON file."""
    try:
        with open(MATNAS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {str(e)}")
        return {}


def save_matnas_data(data: Dict) -> bool:
    """Save matnas data to JSON file (with automatic backup)."""
    try:
        # Create backup first
        success, backup_path = create_backup(MATNAS_DATA_FILE)
        if not success:
            st.warning(f"⚠️ לא ניתן ליצור גיבוי: {backup_path}")

        # Save data
        with open(MATNAS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Log audit event
        user = get_current_user()
        if user:
            log_audit_event("main_buttons_updated", user.get('username', 'unknown'),
                          "Main buttons configuration updated")

        return True
    except Exception as e:
        st.error(f"שגיאה בשמירת הנתונים: {str(e)}")
        return False


def generate_key_from_name(name: str) -> str:
    """
    Generate a key from button name.

    Args:
        name: Button name in Hebrew

    Returns:
        Key in English (lowercase, underscores)
    """
    # Simple transliteration or just use lowercase with underscores
    # For now, just create a simple key
    key = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    key = re.sub(r'_+', '_', key).strip('_')

    # If key is empty (all Hebrew), use a generic name
    if not key:
        import random
        key = f"button_{random.randint(1000, 9999)}"

    return key


def key_exists(key: str, buttons: List[Dict], exclude_index: int = -1) -> bool:
    """
    Check if a key already exists in buttons list.

    Args:
        key: Key to check
        buttons: List of button dictionaries
        exclude_index: Index to exclude from check (for editing)

    Returns:
        True if key exists, False otherwise
    """
    for idx, button in enumerate(buttons):
        if idx != exclude_index and button.get('key') == key:
            return True
    return False


def ensure_dialog_exists(data: Dict, key: str):
    """
    Ensure a dialog exists for the given key.
    If not, create a minimal dialog structure.

    Args:
        data: Full matnas data
        key: Dialog key
    """
    if "dialogs" not in data:
        data["dialogs"] = {}

    if key not in data["dialogs"]:
        # Create minimal dialog
        data["dialogs"][key] = {
            "title": "כותרת חדשה",
            "description": "תיאור חדש",
            "background_color": "#ffffff",
            "is_chatbot": False,
            "system_prompt": "",
            "pdf_file": "",
            "videos": [],
            "images": [],
            "buttons": []
        }


@require_role("editor")
def render_buttons_manager():
    """Render the main buttons manager interface."""
    st.header("🔘 ניהול כפתורים ראשיים")

    # Load data
    data = load_matnas_data()

    if not data or "main_buttons" not in data:
        st.error("❌ לא ניתן לטעון את נתוני הכפתורים")
        return

    main_buttons = data["main_buttons"]

    # Create tabs
    tab1, tab2 = st.tabs(["רשימת כפתורים", "הוסף כפתור חדש"])

    with tab1:
        render_buttons_list_tab(data, main_buttons)

    with tab2:
        render_add_button_tab(data, main_buttons)


def render_buttons_list_tab(data: Dict, main_buttons: List[Dict]):
    """Render buttons list tab."""
    st.subheader("📋 כפתורים קיימים")

    if not main_buttons:
        st.info("אין כפתורים כרגע")
        return

    for idx, button in enumerate(main_buttons):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

            with col1:
                st.write(f"**{button.get('name')}**")

            with col2:
                st.caption(f"מפתח: `{button.get('key')}`")

            with col3:
                # Move up
                if idx > 0:
                    if st.button("⬆️", key=f"btn_up_{idx}", help="העבר למעלה"):
                        main_buttons[idx], main_buttons[idx-1] = main_buttons[idx-1], main_buttons[idx]
                        data["main_buttons"] = main_buttons
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col4:
                # Move down
                if idx < len(main_buttons) - 1:
                    if st.button("⬇️", key=f"btn_down_{idx}", help="העבר למטה"):
                        main_buttons[idx], main_buttons[idx+1] = main_buttons[idx+1], main_buttons[idx]
                        data["main_buttons"] = main_buttons
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col5:
                # Edit button
                if st.button("✏️", key=f"btn_edit_{idx}", help="ערוך"):
                    st.session_state[f"editing_button_{idx}"] = True
                    st.rerun()

            # Edit form
            if st.session_state.get(f"editing_button_{idx}", False):
                render_edit_button_form(data, main_buttons, idx)

            st.divider()

    # Delete button section (separate to avoid conflicts)
    st.subheader("🗑️ מחיקת כפתורים")

    button_to_delete = st.selectbox(
        "בחר כפתור למחיקה",
        options=range(len(main_buttons)),
        format_func=lambda i: f"{main_buttons[i].get('name')} ({main_buttons[i].get('key')})",
        key="delete_button_select"
    )

    if st.button("🗑️ מחק כפתור נבחר", type="secondary"):
        st.session_state["confirm_delete_button"] = button_to_delete
        st.rerun()

    # Confirmation dialog
    if "confirm_delete_button" in st.session_state:
        idx = st.session_state["confirm_delete_button"]
        button = main_buttons[idx]

        st.warning(f"⚠️ האם אתה בטוח שברצונך למחוק את הכפתור **'{button.get('name')}'**?")
        st.info(f"💡 הדיאלוג המקושר (מפתח: `{button.get('key')}`) לא יימחק, רק הכפתור יוסר מהתפריט הראשי.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ כן, מחק", use_container_width=True):
                main_buttons.pop(idx)
                data["main_buttons"] = main_buttons

                if save_matnas_data(data):
                    st.success("✅ הכפתור נמחק בהצלחה!")
                    del st.session_state["confirm_delete_button"]
                    st.rerun()

        with col2:
            if st.button("❌ ביטול", use_container_width=True):
                del st.session_state["confirm_delete_button"]
                st.rerun()


def render_edit_button_form(data: Dict, main_buttons: List[Dict], idx: int):
    """Render edit button form."""
    button = main_buttons[idx]

    with st.form(key=f"edit_button_form_{idx}"):
        st.subheader(f"✏️ עריכת כפתור: {button.get('name')}")

        # Button name
        name = st.text_input("שם הכפתור", value=button.get('name', ''))

        # Button key
        key = st.text_input("מפתח (key)", value=button.get('key', ''),
                           help="מזהה ייחודי באנגלית (אותיות קטנות, קווים תחתונים)")

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("💾 שמור שינויים", use_container_width=True)

        with col2:
            cancelled = st.form_submit_button("❌ ביטול", use_container_width=True)

        if submitted:
            # Validate
            if not name:
                st.error("❌ שם הכפתור לא יכול להיות ריק")
            elif not key:
                st.error("❌ מפתח לא יכול להיות ריק")
            elif key_exists(key, main_buttons, exclude_index=idx):
                st.error(f"❌ המפתח '{key}' כבר קיים")
            else:
                # Update button
                old_key = button.get('key')
                main_buttons[idx] = {"name": name, "key": key}

                # If key changed, update dialog key
                if old_key != key and old_key in data.get("dialogs", {}):
                    data["dialogs"][key] = data["dialogs"].pop(old_key)

                # Ensure dialog exists
                ensure_dialog_exists(data, key)

                data["main_buttons"] = main_buttons

                if save_matnas_data(data):
                    st.success("✅ הכפתור עודכן בהצלחה!")
                    del st.session_state[f"editing_button_{idx}"]
                    st.rerun()

        if cancelled:
            del st.session_state[f"editing_button_{idx}"]
            st.rerun()


def render_add_button_tab(data: Dict, main_buttons: List[Dict]):
    """Render add button tab."""
    st.subheader("➕ הוספת כפתור חדש")

    with st.form("add_button_form"):
        # Button name
        name = st.text_input("שם הכפתור", placeholder="לדוגמה: חוגים")

        # Auto-generate key or manual
        col1, col2 = st.columns([2, 1])

        with col1:
            key = st.text_input("מפתח (key)", placeholder="לדוגמה: classes",
                              help="מזהה ייחודי באנגלית. ריק = יווצר אוטומטית")

        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            auto_key = st.checkbox("צור מפתח אוטומטית", value=True)

        # Submit
        submitted = st.form_submit_button("➕ הוסף כפתור", use_container_width=True)

        if submitted:
            if not name:
                st.error("❌ שם הכפתור לא יכול להיות ריק")
            else:
                # Generate key if needed
                if auto_key or not key:
                    generated_key = generate_key_from_name(name)

                    # Ensure uniqueness
                    base_key = generated_key
                    counter = 1
                    while key_exists(generated_key, main_buttons):
                        generated_key = f"{base_key}_{counter}"
                        counter += 1

                    final_key = generated_key
                else:
                    final_key = key

                # Check if key exists
                if key_exists(final_key, main_buttons):
                    st.error(f"❌ המפתח '{final_key}' כבר קיים")
                else:
                    # Add button
                    new_button = {"name": name, "key": final_key}
                    main_buttons.append(new_button)

                    # Ensure dialog exists
                    ensure_dialog_exists(data, final_key)

                    data["main_buttons"] = main_buttons

                    if save_matnas_data(data):
                        st.success(f"✅ הכפתור '{name}' נוסף בהצלחה!")
                        st.info(f"💡 נוצר דיאלוג חדש עם המפתח: `{final_key}`")
                        st.balloons()
                        st.rerun()
