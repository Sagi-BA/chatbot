"""
Admin Panel Entry Point
Main interface for the Matnas chatbot admin panel
"""

import streamlit as st
import os
from datetime import datetime, timedelta

from admin.auth import (
    is_authenticated, get_current_user, authenticate_user,
    login_user, logout, extend_session, is_locked_out,
    get_lockout_remaining_time, log_audit_event
)
from admin.users import create_initial_super_admin, render_user_management
from admin.dashboard import render_dashboard
from admin.main_page_editor import render_main_page_editor
from admin.buttons_manager import render_buttons_manager
from admin.dialog_editor import render_dialog_editor


def load_admin_styles():
    """Load admin panel CSS."""
    css_path = os.path.join('admin', 'styles.css')

    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_session_warning():
    """Render session timeout warning if needed."""
    if st.session_state.get("admin_session_warning", False):
        remaining_minutes = 5  # Warning shows 5 minutes before timeout

        st.warning(f"⚠️ **אזהרה:** הסשן שלך יפוג בעוד {remaining_minutes} דקות. האם תרצה להאריך את הסשן?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("הארך סשן", key="extend_session_btn"):
                extend_session()
                st.success("✅ הסשן הוארך ב-30 דקות נוספות")
                st.rerun()

        with col2:
            if st.button("התנתק עכשיו", key="logout_from_warning"):
                logout()
                st.rerun()


def render_login_page():
    """Render the login page."""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    st.title("🔐 התחברות - פאנל ניהול")
    st.subheader("מתנ\"ס העמק")

    st.divider()

    with st.form("login_form"):
        username = st.text_input("שם משתמש", placeholder="הזן שם משתמש")
        password = st.text_input("סיסמה", type="password", placeholder="הזן סיסמה")
        remember = st.checkbox("זכור אותי")

        submitted = st.form_submit_button("התחבר", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("❌ נא למלא את כל השדות")
            else:
                # Check if locked out
                if is_locked_out(username):
                    remaining = get_lockout_remaining_time(username)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    st.error(f"❌ חשבון זה נעול עקב ניסיונות התחברות כושלים רבים. נסה שוב בעוד {minutes}:{seconds:02d} דקות.")
                else:
                    # Authenticate
                    user = authenticate_user(username, password)

                    if user:
                        # Login the user first
                        login_user(user, remember)
                        log_audit_event("login_success", username, "User logged in successfully")

                        # Check if must change password
                        if user.get('must_change_password', False):
                            st.session_state['force_password_change'] = True
                            st.session_state['force_password_change_user'] = user
                            st.success("✅ התחברת בהצלחה! עכשיו שנה את הסיסמה שלך")
                            st.rerun()
                        else:
                            st.success(f"✅ התחברת בהצלחה! ברוך הבא, {user.get('username')}")
                            st.rerun()
                    else:
                        log_audit_event("login_failed", username, "Failed login attempt")
                        st.error("❌ שם משתמש או סיסמה שגויים")

    st.divider()

    # First time setup info
    with st.expander("ℹ️ כניסה ראשונה למערכת"):
        st.write("""
        **פרטי התחברות ראשוניים:**

        - **שם משתמש:** `admin`
        - **סיסמה:** `Admin@Matnas2025`

        ⚠️ **חשוב:** תתבקש לשנות את הסיסמה בכניסה הראשונה.
        """)

    st.markdown('</div>', unsafe_allow_html=True)


def render_password_change_form():
    """Render force password change form."""
    st.title("🔒 שינוי סיסמה נדרש")
    st.warning("⚠️ מסיבות אבטחה, חובה לשנות את הסיסמה בכניסה הראשונה.")

    user = st.session_state.get('force_password_change_user')

    if not user:
        st.error("שגיאה: לא נמצא משתמש")
        return

    with st.form("password_change_form"):
        new_password = st.text_input("סיסמה חדשה", type="password",
                                     help="לפחות 8 תווים, אות גדולה, אות קטנה וספרה")
        confirm_password = st.text_input("אשר סיסמה", type="password")

        # Show password strength
        if new_password:
            from admin.users import get_password_strength
            strength_score, strength_label = get_password_strength(new_password)

            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(strength_score / 4)
            with col2:
                st.write(f"חוזק: {strength_label}")

        submitted = st.form_submit_button("שנה סיסמה", use_container_width=True)

        if submitted:
            if not new_password or not confirm_password:
                st.error("❌ נא למלא את כל השדות")
            elif new_password != confirm_password:
                st.error("❌ הסיסמאות אינן תואמות")
            else:
                from admin.users import change_password
                success, error = change_password(user['id'], new_password, clear_must_change=True)

                if success:
                    st.success("✅ הסיסמה שונתה בהצלחה!")

                    # Log in the user
                    login_user(user, False)
                    log_audit_event("password_changed", user['username'], "Initial password changed")

                    # Clear force change flag
                    if 'force_password_change' in st.session_state:
                        del st.session_state['force_password_change']
                    if 'force_password_change_user' in st.session_state:
                        del st.session_state['force_password_change_user']

                    st.rerun()
                else:
                    st.error(f"❌ {error}")


def render_admin_header():
    """Render admin panel header with user info."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title("🔧 ניהול מתנ\"ס - פאנל ניהול")

    with col2:
        user = get_current_user()
        if user:
            from admin.users import ROLES
            role_label = ROLES.get(user.get('role'), user.get('role'))
            st.write(f"**{user.get('username')}**")
            st.caption(role_label)

    with col3:
        if st.button("🚪 התנתק", use_container_width=True):
            user = get_current_user()
            if user:
                log_audit_event("logout", user.get('username'), "User logged out")
            logout()
            st.rerun()


def render_sidebar_navigation():
    """Render sidebar navigation menu."""
    with st.sidebar:
        st.title("📋 תפריט ניהול")

        # Get current user role
        user = get_current_user()
        role = user.get('role', 'viewer') if user else 'viewer'

        # Navigation options based on role
        nav_options = ["📊 לוח בקרה"]

        # Only super admins can manage users
        if role == "super_admin":
            nav_options.append("👥 ניהול משתמשים")

        # Phase 2 features (editors and above)
        if role in ["super_admin", "editor"]:
            nav_options.extend([
                "📝 עמוד ראשי",
                "🔘 כפתורים ראשיים"
            ])

        # Phase 3 features (editors and above)
        if role in ["super_admin", "editor"]:
            nav_options.append("💬 עורך דיאלוגים")

        # Phase 4+ features (coming soon)
        nav_options.extend([
            "🤖 הגדרות צ'אטבוט (בקרוב)",
            "📁 ספריית מדיה (בקרוב)",
            "⚙️ הגדרות כלליות (בקרוב)"
        ])

        selected = st.radio("בחר עמוד:", nav_options, key="admin_nav")

        # Store selected page
        st.session_state["admin_page"] = selected

        st.divider()

        # Quick info
        st.caption("**מידע מהיר:**")
        st.caption(f"גרסה: Phase 3.0")
        st.caption(f"תאריך: {datetime.now().strftime('%d/%m/%Y')}")

        st.divider()

        # Support info
        with st.expander("📞 תמיכה"):
            st.write("**שגיא בר און**")
            st.write("📧 sagi.baron76@gmail.com")
            st.write("📱 054-999-5050")


def render_admin_interface():
    """Render the main admin interface."""
    # Check authentication
    if not is_authenticated():
        render_login_page()
        return

    # Check if password change is forced
    if st.session_state.get('force_password_change', False):
        render_password_change_form()
        return

    # Render header
    render_admin_header()

    # Render session warning if needed
    render_session_warning()

    st.divider()

    # Render sidebar navigation
    render_sidebar_navigation()

    # Get selected page
    selected_page = st.session_state.get("admin_page", "📊 לוח בקרה")

    # Render appropriate page
    if selected_page == "📊 לוח בקרה":
        render_dashboard()
    elif selected_page == "👥 ניהול משתמשים":
        render_user_management()
    elif selected_page == "📝 עמוד ראשי":
        render_main_page_editor()
    elif selected_page == "🔘 כפתורים ראשיים":
        render_buttons_manager()
    elif selected_page == "💬 עורך דיאלוגים":
        render_dialog_editor()
    else:
        # Coming soon pages
        st.info(f"⏳ תכונה זו ({selected_page}) תהיה זמינה בשלבים הבאים של הפיתוח.")

        st.write("""
        **מה צפוי בשלבים הבאים:**

        - **שלב 4:** הגדרות צ'אטבוט נוספות
        - **שלב 5:** ספריית מדיה מתקדמת
        - **שלב 5:** ספריית מדיה
        - **שלב 6:** הגדרות גלובליות
        - **שלב 7:** אנליטיקה ומעקב
        """)


def run_admin_panel():
    """
    Main entry point for admin panel.
    Called when ?admin=true is in URL.
    """
    # Set page config
    st.set_page_config(
        page_title="ניהול מתנ\"ס",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load admin styles
    load_admin_styles()

    # Initialize admin users if first run
    create_initial_super_admin()

    # Render admin interface
    render_admin_interface()


if __name__ == "__main__":
    # For testing purposes only
    run_admin_panel()
