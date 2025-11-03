"""
Global Settings Editor Module for Admin Panel
Manage application-wide configuration settings
"""

import streamlit as st
import json
import os
from typing import Dict
from datetime import datetime
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
            log_audit_event("global_settings_updated", user.get('username', 'unknown'),
                          "Global settings updated")

        return True
    except Exception as e:
        st.error(f"שגיאה בשמירת הנתונים: {str(e)}")
        return False


def get_data_structure_info(data: Dict) -> Dict:
    """Get information about the data structure."""
    info = {
        'has_main_page': 'main_page' in data,
        'has_main_buttons': 'main_buttons' in data,
        'has_dialogs': 'dialogs' in data,
        'dialogs_count': len(data.get('dialogs', {})),
        'main_buttons_count': len(data.get('main_buttons', [])),
        'main_page_images': len(data.get('main_page', {}).get('images', [])),
        'main_page_videos': len(data.get('main_page', {}).get('videos', [])),
    }

    # Count total sub-buttons across all dialogs
    total_sub_buttons = 0
    for dialog_key, dialog in data.get('dialogs', {}).items():
        total_sub_buttons += len(dialog.get('buttons', []))

    info['total_sub_buttons'] = total_sub_buttons

    return info


@require_role("super_admin")
def render_global_settings():
    """Render the global settings interface."""
    st.header("⚙️ הגדרות כלליות")

    st.info("💡 דף זה מיועד להגדרות מתקדמות של המערכת. שינויים כאן משפיעים על כל האפליקציה.")

    # Load data
    data = load_matnas_data()

    if not data:
        st.error("❌ לא ניתן לטעון את נתוני המערכת")
        return

    # Get structure info
    info = get_data_structure_info(data)

    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 סקירה כללית",
        "🔧 הגדרות מתקדמות",
        "📋 מבנה נתונים"
    ])

    with tab1:
        render_overview_tab(data, info)

    with tab2:
        render_advanced_settings_tab(data)

    with tab3:
        render_data_structure_tab(data, info)


def render_overview_tab(data: Dict, info: Dict):
    """Render overview tab with system statistics."""
    st.subheader("📊 סקירה כללית")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("דיאלוגים", info['dialogs_count'])
        st.metric("כפתורים ראשיים", info['main_buttons_count'])
        st.metric("תמונות בעמוד הראשי", info['main_page_images'])

    with col2:
        st.metric("סה\"כ כפתורי משנה", info['total_sub_buttons'])
        st.metric("וידאו בעמוד הראשי", info['main_page_videos'])

    st.divider()

    # System health checks
    st.write("**בדיקות תקינות:**")

    checks = []

    # Check main page exists
    if info['has_main_page']:
        checks.append(("✅", "עמוד ראשי מוגדר"))
    else:
        checks.append(("❌", "עמוד ראשי חסר"))

    # Check main buttons exist
    if info['has_main_buttons'] and info['main_buttons_count'] > 0:
        checks.append(("✅", f"{info['main_buttons_count']} כפתורים ראשיים"))
    else:
        checks.append(("⚠️", "אין כפתורים ראשיים"))

    # Check dialogs exist
    if info['has_dialogs'] and info['dialogs_count'] > 0:
        checks.append(("✅", f"{info['dialogs_count']} דיאלוגים"))
    else:
        checks.append(("⚠️", "אין דיאלוגים"))

    # Check for orphaned dialogs (dialogs not linked to main buttons)
    main_button_keys = [btn.get('key') for btn in data.get('main_buttons', [])]
    dialog_keys = list(data.get('dialogs', {}).keys())
    orphaned = [key for key in dialog_keys if key not in main_button_keys]

    if orphaned:
        checks.append(("⚠️", f"{len(orphaned)} דיאלוגים לא מקושרים: {', '.join(orphaned)}"))
    else:
        checks.append(("✅", "כל הדיאלוגים מקושרים"))

    for icon, message in checks:
        st.write(f"{icon} {message}")

    st.divider()

    # Quick actions
    st.write("**פעולות מהירות:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 רענן נתונים", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📦 צור גיבוי ידני", use_container_width=True):
            success, backup_path = create_backup(MATNAS_DATA_FILE)
            if success:
                st.success(f"✅ גיבוי נוצר: {os.path.basename(backup_path)}")
            else:
                st.error(f"❌ {backup_path}")


def render_advanced_settings_tab(data: Dict):
    """Render advanced settings tab."""
    st.subheader("🔧 הגדרות מתקדמות")

    st.warning("⚠️ הגדרות אלו משפיעות על כל המערכת. שנה בזהירות!")

    # Main page default settings
    st.write("**הגדרות ברירת מחדל לעמוד הראשי:**")

    with st.form("main_page_defaults_form"):
        main_page = data.get('main_page', {})

        default_bg_color = st.color_picker(
            "צבע רקע ברירת מחדל",
            value=main_page.get('background_color', '#ffffff'),
            help="צבע רקע שישמש כברירת מחדל"
        )

        submitted = st.form_submit_button("💾 שמור הגדרות", use_container_width=True)

        if submitted:
            if 'main_page' not in data:
                data['main_page'] = {}

            data['main_page']['background_color'] = default_bg_color

            if save_matnas_data(data):
                st.success("✅ ההגדרות נשמרו בהצלחה!")
                st.rerun()

    st.divider()

    # Data maintenance
    st.write("**תחזוקת נתונים:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧹 נקה דיאלוגים לא מקושרים", use_container_width=True):
            st.session_state['confirm_clean_orphaned'] = True
            st.rerun()

    with col2:
        if st.button("🔗 סנכרן כפתורים ודיאלוגים", use_container_width=True):
            st.session_state['confirm_sync_dialogs'] = True
            st.rerun()

    # Confirm clean orphaned dialogs
    if st.session_state.get('confirm_clean_orphaned', False):
        st.warning("⚠️ פעולה זו תמחק דיאלוגים שאינם מקושרים לכפתורים ראשיים. האם להמשיך?")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✅ כן, מחק", key="confirm_clean_yes"):
                main_button_keys = [btn.get('key') for btn in data.get('main_buttons', [])]
                dialog_keys = list(data.get('dialogs', {}).keys())
                orphaned = [key for key in dialog_keys if key not in main_button_keys]

                if orphaned:
                    for key in orphaned:
                        del data['dialogs'][key]

                    if save_matnas_data(data):
                        st.success(f"✅ {len(orphaned)} דיאלוגים נמחקו")
                        del st.session_state['confirm_clean_orphaned']
                        st.rerun()
                else:
                    st.info("אין דיאלוגים לא מקושרים למחיקה")
                    del st.session_state['confirm_clean_orphaned']

        with col_no:
            if st.button("❌ ביטול", key="confirm_clean_no"):
                del st.session_state['confirm_clean_orphaned']
                st.rerun()

    # Confirm sync dialogs
    if st.session_state.get('confirm_sync_dialogs', False):
        st.info("💡 פעולה זו תיצור דיאלוגים חסרים עבור כפתורים ראשיים ללא דיאלוג")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✅ כן, סנכרן", key="confirm_sync_yes"):
                created_count = 0
                for button in data.get('main_buttons', []):
                    key = button.get('key')
                    if key not in data.get('dialogs', {}):
                        # Create minimal dialog
                        data['dialogs'][key] = {
                            "title": button.get('name', 'כותרת חדשה'),
                            "description": "תיאור חדש",
                            "background_color": "#ffffff",
                            "is_chatbot": False,
                            "system_prompt": "",
                            "pdf_file": "",
                            "videos": [],
                            "images": [],
                            "buttons": []
                        }
                        created_count += 1

                if created_count > 0:
                    if save_matnas_data(data):
                        st.success(f"✅ {created_count} דיאלוגים נוצרו")
                        del st.session_state['confirm_sync_dialogs']
                        st.rerun()
                else:
                    st.info("כל הכפתורים כבר מקושרים לדיאלוגים")
                    del st.session_state['confirm_sync_dialogs']

        with col_no:
            if st.button("❌ ביטול", key="confirm_sync_no"):
                del st.session_state['confirm_sync_dialogs']
                st.rerun()


def render_data_structure_tab(data: Dict, info: Dict):
    """Render data structure tab."""
    st.subheader("📋 מבנה נתונים")

    st.write("**מידע על מבנה הנתונים:**")

    # Main page structure
    with st.expander("🏠 עמוד ראשי", expanded=True):
        main_page = data.get('main_page', {})

        st.json({
            "title": main_page.get('title', ''),
            "description": main_page.get('description', ''),
            "background_color": main_page.get('background_color', ''),
            "images_count": len(main_page.get('images', [])),
            "videos_count": len(main_page.get('videos', []))
        })

    # Main buttons structure
    with st.expander(f"🔘 כפתורים ראשיים ({info['main_buttons_count']})", expanded=False):
        for button in data.get('main_buttons', []):
            st.write(f"- **{button.get('name')}** (key: `{button.get('key')}`)")

    # Dialogs structure
    with st.expander(f"💬 דיאלוגים ({info['dialogs_count']})", expanded=False):
        for dialog_key, dialog in data.get('dialogs', {}).items():
            st.write(f"**{dialog_key}** - {dialog.get('title')}")
            st.json({
                "is_chatbot": dialog.get('is_chatbot', False),
                "pdf_file": dialog.get('pdf_file', ''),
                "images_count": len(dialog.get('images', [])),
                "videos_count": len(dialog.get('videos', [])),
                "buttons_count": len(dialog.get('buttons', []))
            })
            st.divider()

    # Export/Import
    st.divider()
    st.write("**ייצוא/ייבוא נתונים:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 ייצא נתונים ל-JSON", use_container_width=True):
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 הורד קובץ JSON",
                data=json_str,
                file_name=f"matnas_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col2:
        st.info("💡 ייבוא נתונים יהיה זמין בעדכון הבא")
