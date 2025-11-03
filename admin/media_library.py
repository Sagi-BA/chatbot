"""
Media Library Manager Module for Admin Panel
Centralized management of images and PDFs
"""

import streamlit as st
import os
import shutil
from typing import List, Tuple, Dict
from datetime import datetime
from admin.auth import require_role, get_current_user, log_audit_event


# Constants
UPLOADS_FOLDER = "uploads"
DATA_FOLDER = "data"


def get_file_info(file_path: str) -> Dict:
    """Get file information including size and modification time."""
    try:
        stats = os.stat(file_path)
        return {
            'size': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime),
            'size_mb': round(stats.st_size / (1024 * 1024), 2)
        }
    except:
        return {'size': 0, 'modified': None, 'size_mb': 0}


def get_images_list() -> List[Dict]:
    """Get list of all images with metadata."""
    if not os.path.exists(UPLOADS_FOLDER):
        return []

    images = []
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    try:
        for filename in os.listdir(UPLOADS_FOLDER):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                file_path = os.path.join(UPLOADS_FOLDER, filename)
                info = get_file_info(file_path)
                images.append({
                    'filename': filename,
                    'path': file_path,
                    'size': info['size'],
                    'size_mb': info['size_mb'],
                    'modified': info['modified']
                })

        # Sort by modification time (newest first)
        images.sort(key=lambda x: x['modified'] if x['modified'] else datetime.min, reverse=True)
        return images
    except Exception as e:
        st.error(f"שגיאה בטעינת רשימת תמונות: {str(e)}")
        return []


def get_pdfs_list() -> List[Dict]:
    """Get list of all PDFs with metadata."""
    if not os.path.exists(DATA_FOLDER):
        return []

    pdfs = []

    try:
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(DATA_FOLDER, filename)
                info = get_file_info(file_path)
                pdfs.append({
                    'filename': filename,
                    'path': file_path,
                    'size': info['size'],
                    'size_mb': info['size_mb'],
                    'modified': info['modified']
                })

        # Sort by modification time (newest first)
        pdfs.sort(key=lambda x: x['modified'] if x['modified'] else datetime.min, reverse=True)
        return pdfs
    except Exception as e:
        st.error(f"שגיאה בטעינת רשימת PDFs: {str(e)}")
        return []


def delete_file(file_path: str) -> Tuple[bool, str]:
    """Delete a file from the filesystem."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, "הקובץ נמחק בהצלחה"
        else:
            return False, "הקובץ לא נמצא"
    except Exception as e:
        return False, f"שגיאה במחיקת הקובץ: {str(e)}"


def save_uploaded_file(uploaded_file, folder: str) -> Tuple[bool, str]:
    """Save an uploaded file to specified folder."""
    try:
        # Ensure folder exists
        os.makedirs(folder, exist_ok=True)

        # Save file
        file_path = os.path.join(folder, uploaded_file.name)

        # Check if file already exists
        if os.path.exists(file_path):
            return False, f"הקובץ '{uploaded_file.name}' כבר קיים"

        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        return True, uploaded_file.name
    except Exception as e:
        return False, f"שגיאה בשמירת הקובץ: {str(e)}"


def rename_file(old_path: str, new_name: str) -> Tuple[bool, str]:
    """Rename a file."""
    try:
        folder = os.path.dirname(old_path)
        new_path = os.path.join(folder, new_name)

        if os.path.exists(new_path):
            return False, f"הקובץ '{new_name}' כבר קיים"

        os.rename(old_path, new_path)
        return True, "הקובץ שונה בהצלחה"
    except Exception as e:
        return False, f"שגיאה בשינוי שם הקובץ: {str(e)}"


def get_storage_stats() -> Dict:
    """Get storage statistics for uploads and data folders."""
    stats = {
        'images_count': 0,
        'images_size': 0,
        'pdfs_count': 0,
        'pdfs_size': 0,
        'total_size': 0
    }

    # Images
    images = get_images_list()
    stats['images_count'] = len(images)
    stats['images_size'] = sum(img['size'] for img in images)

    # PDFs
    pdfs = get_pdfs_list()
    stats['pdfs_count'] = len(pdfs)
    stats['pdfs_size'] = sum(pdf['size'] for pdf in pdfs)

    # Total
    stats['total_size'] = stats['images_size'] + stats['pdfs_size']

    return stats


@require_role("editor")
def render_media_library():
    """Render the media library interface."""
    st.header("📁 ספריית מדיה")

    # Storage statistics
    stats = get_storage_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "תמונות",
            stats['images_count'],
            f"{round(stats['images_size'] / (1024*1024), 2)} MB"
        )

    with col2:
        st.metric(
            "קבצי PDF",
            stats['pdfs_count'],
            f"{round(stats['pdfs_size'] / (1024*1024), 2)} MB"
        )

    with col3:
        st.metric(
            "סה\"כ נפח",
            f"{round(stats['total_size'] / (1024*1024), 2)} MB",
            ""
        )

    st.divider()

    # Create tabs
    tab1, tab2 = st.tabs(["🖼️ ניהול תמונות", "📄 ניהול PDFs"])

    with tab1:
        render_images_tab()

    with tab2:
        render_pdfs_tab()


def render_images_tab():
    """Render images management tab."""
    st.subheader("🖼️ ניהול תמונות")

    # Upload new images
    st.write("**העלאת תמונות חדשות:**")
    uploaded_files = st.file_uploader(
        "בחר תמונות להעלאה",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        accept_multiple_files=True,
        help="ניתן להעלות מספר תמונות בבת אחת",
        key="media_library_images_upload"
    )

    if uploaded_files:
        if st.button("📤 העלה תמונות", use_container_width=True, key="upload_images_btn"):
            success_count = 0
            error_count = 0

            for uploaded_file in uploaded_files:
                success, result = save_uploaded_file(uploaded_file, UPLOADS_FOLDER)
                if success:
                    success_count += 1
                else:
                    st.error(f"❌ {result}")
                    error_count += 1

            if success_count > 0:
                user = get_current_user()
                if user:
                    log_audit_event(
                        "media_uploaded",
                        user.get('username', 'unknown'),
                        f"Uploaded {success_count} images"
                    )
                st.success(f"✅ {success_count} תמונות הועלו בהצלחה!")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} קבצים לא הועלו (כבר קיימים או שגיאה)")
                st.rerun()

    st.divider()

    # Display images
    st.write("**תמונות קיימות:**")

    images = get_images_list()

    if not images:
        st.info("אין תמונות בספרייה כרגע")
    else:
        # Filter and search
        search = st.text_input("🔍 חיפוש תמונה", placeholder="הקלד שם קובץ...", key="search_images")

        if search:
            images = [img for img in images if search.lower() in img['filename'].lower()]

        st.caption(f"מציג {len(images)} תמונות")

        # Display images in grid
        cols_per_row = 3
        for i in range(0, len(images), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, col in enumerate(cols):
                if i + j < len(images):
                    img = images[i + j]

                    with col:
                        # Display image
                        try:
                            st.image(img['path'], use_container_width=True)
                        except:
                            st.error(f"לא ניתן להציג {img['filename']}")

                        # File info
                        st.caption(f"**{img['filename']}**")
                        st.caption(f"גודל: {img['size_mb']} MB")
                        if img['modified']:
                            st.caption(f"עודכן: {img['modified'].strftime('%d/%m/%Y %H:%M')}")

                        # Actions
                        col_rename, col_delete = st.columns(2)

                        with col_rename:
                            if st.button("✏️", key=f"rename_img_{i+j}", help="שנה שם"):
                                st.session_state[f"renaming_img_{i+j}"] = True
                                st.rerun()

                        with col_delete:
                            if st.button("🗑️", key=f"delete_img_{i+j}", help="מחק"):
                                st.session_state[f"confirm_delete_img_{i+j}"] = True
                                st.rerun()

                        # Rename dialog
                        if st.session_state.get(f"renaming_img_{i+j}", False):
                            with st.form(key=f"rename_form_{i+j}"):
                                new_name = st.text_input("שם חדש", value=img['filename'])

                                col_save, col_cancel = st.columns(2)

                                with col_save:
                                    if st.form_submit_button("💾 שמור"):
                                        success, message = rename_file(img['path'], new_name)
                                        if success:
                                            st.success(f"✅ {message}")
                                            del st.session_state[f"renaming_img_{i+j}"]
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {message}")

                                with col_cancel:
                                    if st.form_submit_button("❌ ביטול"):
                                        del st.session_state[f"renaming_img_{i+j}"]
                                        st.rerun()

                        # Delete confirmation
                        if st.session_state.get(f"confirm_delete_img_{i+j}", False):
                            st.warning("⚠️ למחוק?")

                            col_yes, col_no = st.columns(2)

                            with col_yes:
                                if st.button("כן", key=f"yes_img_{i+j}"):
                                    success, message = delete_file(img['path'])
                                    if success:
                                        user = get_current_user()
                                        if user:
                                            log_audit_event(
                                                "media_deleted",
                                                user.get('username', 'unknown'),
                                                f"Deleted image: {img['filename']}"
                                            )
                                        st.success(f"✅ {message}")
                                        del st.session_state[f"confirm_delete_img_{i+j}"]
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")

                            with col_no:
                                if st.button("לא", key=f"no_img_{i+j}"):
                                    del st.session_state[f"confirm_delete_img_{i+j}"]
                                    st.rerun()


def render_pdfs_tab():
    """Render PDFs management tab."""
    st.subheader("📄 ניהול קבצי PDF")

    # Upload new PDFs
    st.write("**העלאת PDF חדש:**")
    uploaded_pdf = st.file_uploader(
        "בחר קובץ PDF להעלאה",
        type=['pdf'],
        help="קובץ PDF יועלה לתיקיית data",
        key="media_library_pdf_upload"
    )

    if uploaded_pdf:
        if st.button("📤 העלה PDF", use_container_width=True, key="upload_pdf_btn"):
            success, result = save_uploaded_file(uploaded_pdf, DATA_FOLDER)
            if success:
                user = get_current_user()
                if user:
                    log_audit_event(
                        "media_uploaded",
                        user.get('username', 'unknown'),
                        f"Uploaded PDF: {result}"
                    )
                st.success(f"✅ הקובץ {result} הועלה בהצלחה!")
                st.rerun()
            else:
                st.error(f"❌ {result}")

    st.divider()

    # Display PDFs
    st.write("**קבצי PDF קיימים:**")

    pdfs = get_pdfs_list()

    if not pdfs:
        st.info("אין קבצי PDF בספרייה כרגע")
    else:
        # Filter and search
        search = st.text_input("🔍 חיפוש PDF", placeholder="הקלד שם קובץ...", key="search_pdfs")

        if search:
            pdfs = [pdf for pdf in pdfs if search.lower() in pdf['filename'].lower()]

        st.caption(f"מציג {len(pdfs)} קבצי PDF")

        # Display PDFs in table
        for idx, pdf in enumerate(pdfs):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])

                with col1:
                    st.write(f"📄 **{pdf['filename']}**")

                with col2:
                    st.caption(f"גודל: {pdf['size_mb']} MB")

                with col3:
                    if pdf['modified']:
                        st.caption(f"עודכן: {pdf['modified'].strftime('%d/%m/%Y %H:%M')}")

                with col4:
                    if st.button("✏️", key=f"rename_pdf_{idx}", help="שנה שם"):
                        st.session_state[f"renaming_pdf_{idx}"] = True
                        st.rerun()

                with col5:
                    if st.button("🗑️", key=f"delete_pdf_{idx}", help="מחק"):
                        st.session_state[f"confirm_delete_pdf_{idx}"] = True
                        st.rerun()

                # Rename dialog
                if st.session_state.get(f"renaming_pdf_{idx}", False):
                    with st.form(key=f"rename_pdf_form_{idx}"):
                        new_name = st.text_input("שם חדש", value=pdf['filename'])

                        col_save, col_cancel = st.columns(2)

                        with col_save:
                            if st.form_submit_button("💾 שמור"):
                                success, message = rename_file(pdf['path'], new_name)
                                if success:
                                    st.success(f"✅ {message}")
                                    del st.session_state[f"renaming_pdf_{idx}"]
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")

                        with col_cancel:
                            if st.form_submit_button("❌ ביטול"):
                                del st.session_state[f"renaming_pdf_{idx}"]
                                st.rerun()

                # Delete confirmation
                if st.session_state.get(f"confirm_delete_pdf_{idx}", False):
                    st.warning(f"⚠️ האם למחוק את '{pdf['filename']}'?")
                    st.info("💡 מחיקת PDF עשויה להשפיע על דיאלוגים שמשתמשים בו")

                    col_yes, col_no = st.columns(2)

                    with col_yes:
                        if st.button("✅ כן, מחק", key=f"yes_pdf_{idx}"):
                            success, message = delete_file(pdf['path'])
                            if success:
                                user = get_current_user()
                                if user:
                                    log_audit_event(
                                        "media_deleted",
                                        user.get('username', 'unknown'),
                                        f"Deleted PDF: {pdf['filename']}"
                                    )
                                st.success(f"✅ {message}")
                                del st.session_state[f"confirm_delete_pdf_{idx}"]
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

                    with col_no:
                        if st.button("❌ ביטול", key=f"no_pdf_{idx}"):
                            del st.session_state[f"confirm_delete_pdf_{idx}"]
                            st.rerun()

                st.divider()
