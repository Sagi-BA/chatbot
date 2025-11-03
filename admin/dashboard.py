"""
Dashboard Module for Admin Panel
Displays statistics and overview
"""

import streamlit as st
import os
import json
from datetime import datetime
from admin.backup import get_backup_statistics, list_backups, create_backup, restore_backup
from admin.users import list_users


def count_files_in_folder(folder: str, extension: str = None) -> int:
    """
    Count files in a folder.

    Args:
        folder: Folder path
        extension: Optional file extension filter (e.g., '.pdf')

    Returns:
        Number of files
    """
    if not os.path.exists(folder):
        return 0

    try:
        files = os.listdir(folder)

        if extension:
            files = [f for f in files if f.lower().endswith(extension.lower())]

        return len(files)
    except Exception as e:
        print(f"Error counting files: {e}")
        return 0


def get_file_modification_time(file_path: str) -> datetime:
    """
    Get file modification time.

    Args:
        file_path: Path to file

    Returns:
        Datetime of last modification, or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None

    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        print(f"Error getting file modification time: {e}")
        return None


def load_matnas_data() -> dict:
    """
    Load matnas data JSON.

    Returns:
        Dictionary with matnas data
    """
    data_file = os.path.join('data', 'matnas_data.json')

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading matnas data: {e}")
        return {}


def get_user_count() -> int:
    """
    Get current user count from user_count.json.

    Returns:
        User count
    """
    count_file = os.path.join('data', 'user_count.json')

    try:
        with open(count_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('count', 0)
    except Exception as e:
        print(f"Error loading user count: {e}")
        return 0


def render_dashboard():
    """
    Render the main admin dashboard.
    """
    st.header("📊 לוח בקרה")

    # Top statistics
    render_statistics()

    st.divider()

    # Backup section
    render_backup_section()

    st.divider()

    # Quick actions
    render_quick_actions()


def render_statistics():
    """Render statistics cards."""
    st.subheader("סטטיסטיקות כלליות")

    # Load data
    matnas_data = load_matnas_data()
    dialogs_count = len(matnas_data.get('dialogs', {}))
    images_count = count_files_in_folder('uploads')
    pdfs_count = count_files_in_folder('data', '.pdf')
    user_count = get_user_count()
    admin_users_count = len(list_users())

    # Get last edit time
    data_file = os.path.join('data', 'matnas_data.json')
    last_edit = get_file_modification_time(data_file)

    # Create columns for statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="דיאלוגים",
            value=dialogs_count,
            help="מספר דיאלוגים במערכת"
        )

    with col2:
        st.metric(
            label="תמונות",
            value=images_count,
            help="מספר תמונות בתיקיית uploads"
        )

    with col3:
        st.metric(
            label="קבצי PDF",
            value=pdfs_count,
            help="מספר קבצי PDF בתיקיית data"
        )

    with col4:
        st.metric(
            label='סה"כ משתמשים',
            value=f"{user_count:,}",
            help="סך המשתמשים שביקרו באתר"
        )

    # Second row
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            label="מנהלי מערכת",
            value=admin_users_count,
            help="מספר משתמשי ניהול במערכת"
        )

    with col6:
        backup_stats = get_backup_statistics()
        st.metric(
            label="גיבויים",
            value=backup_stats['total_count'],
            help="מספר קבצי גיבוי במערכת"
        )

    with col7:
        st.metric(
            label="גודל גיבויים",
            value=backup_stats['total_size_formatted'],
            help="סה\"כ גודל קבצי גיבוי"
        )

    with col8:
        if last_edit:
            last_edit_str = last_edit.strftime("%d/%m/%Y %H:%M")
        else:
            last_edit_str = "לא ידוע"

        st.metric(
            label="עריכה אחרונה",
            value=last_edit_str,
            help="מתי נערך הקובץ הראשי בפעם האחרונה"
        )


def render_backup_section():
    """Render backup management section."""
    st.subheader("🗄️ ניהול גיבויים")

    col1, col2 = st.columns([2, 1])

    with col1:
        backup_stats = get_backup_statistics()
        last_backup = backup_stats.get('last_backup_time')

        if last_backup:
            time_diff = datetime.now() - last_backup
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)

            if hours > 0:
                time_str = f"לפני {hours} שעות ו-{minutes} דקות"
            else:
                time_str = f"לפני {minutes} דקות"

            st.info(f"📅 גיבוי אחרון: {last_backup.strftime('%d/%m/%Y %H:%M')} ({time_str})")
        else:
            st.warning("⚠️ אין גיבויים במערכת")

    with col2:
        if st.button("📦 צור גיבוי עכשיו", use_container_width=True):
            data_file = os.path.join('data', 'matnas_data.json')
            success, result = create_backup(data_file)

            if success:
                st.success(f"✅ גיבוי נוצר בהצלחה!")
                st.rerun()
            else:
                st.error(f"❌ שגיאה ביצירת גיבוי: {result}")

    # List recent backups
    st.write("**גיבויים אחרונים:**")

    backups = list_backups('matnas_data.json')

    if backups:
        # Show only last 5 backups
        for backup in backups[:5]:
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

            with col1:
                st.write(backup['filename'])

            with col2:
                st.write(backup['timestamp'].strftime('%d/%m/%Y %H:%M'))

            with col3:
                from admin.backup import format_file_size
                st.write(format_file_size(backup['size']))

            with col4:
                if st.button("♻️", key=f"restore_{backup['filename']}", help="שחזר גיבוי זה"):
                    st.session_state[f"confirm_restore_{backup['filename']}"] = True
                    st.rerun()

            # Restore confirmation
            if st.session_state.get(f"confirm_restore_{backup['filename']}", False):
                st.warning(f"⚠️ האם אתה בטוח שברצונך לשחזר את הגיבוי '{backup['filename']}'? פעולה זו תדרוס את הנתונים הנוכחיים!")

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, שחזר", key=f"confirm_restore_yes_{backup['filename']}"):
                        target_file = os.path.join('data', 'matnas_data.json')
                        success, error = restore_backup(backup['path'], target_file)

                        if success:
                            st.success("✅ הגיבוי שוחזר בהצלחה!")
                            del st.session_state[f"confirm_restore_{backup['filename']}"]
                            st.rerun()
                        else:
                            st.error(f"❌ {error}")

                with col_no:
                    if st.button("ביטול", key=f"confirm_restore_no_{backup['filename']}"):
                        del st.session_state[f"confirm_restore_{backup['filename']}"]
                        st.rerun()

        if len(backups) > 5:
            st.info(f"מוצגים 5 מתוך {len(backups)} גיבויים")

    else:
        st.info("אין גיבויים להצגה")


def render_quick_actions():
    """Render quick action buttons."""
    st.subheader("⚡ פעולות מהירות")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 ערוך עמוד ראשי", use_container_width=True):
            st.info("תכונה זו תהיה זמינה בשלב 2")

    with col2:
        if st.button("🔘 ערוך כפתורים", use_container_width=True):
            st.info("תכונה זו תהיה זמינה בשלב 2")

    with col3:
        if st.button("💬 ערוך דיאלוגים", use_container_width=True):
            st.info("תכונה זו תהיה זמינה בשלב 3")

    st.divider()

    # System information
    with st.expander("ℹ️ מידע מערכת"):
        st.write("**גרסה:** Phase 1.0")
        st.write("**תאריך עדכון:** נובמבר 2025")
        st.write("**סטטוס:** פעיל ✅")

        # Show Python and Streamlit versions
        import sys
        import streamlit as st_version

        st.write(f"**Python:** {sys.version.split()[0]}")
        st.write(f"**Streamlit:** {st_version.__version__}")
