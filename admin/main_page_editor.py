"""
Main Page Editor Module for Admin Panel
Allows editing of main page content, images, videos, and buttons
"""

import streamlit as st
import json
import os
from typing import Dict, List, Tuple
from admin.auth import require_role, get_current_user, log_audit_event
from admin.backup import create_backup


# Constants
MATNAS_DATA_FILE = "matnas_data.json"
UPLOADS_FOLDER = "uploads"


def load_matnas_data() -> Dict:
    """
    Load matnas data from JSON file.

    Returns:
        Dictionary with matnas data
    """
    try:
        with open(MATNAS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {str(e)}")
        return {}


def save_matnas_data(data: Dict) -> bool:
    """
    Save matnas data to JSON file (with automatic backup).

    Args:
        data: Dictionary with matnas data

    Returns:
        True if successful, False otherwise
    """
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
            log_audit_event("main_page_updated", user.get('username', 'unknown'),
                          "Main page configuration updated")

        return True
    except Exception as e:
        st.error(f"שגיאה בשמירת הנתונים: {str(e)}")
        return False


def get_uploaded_images() -> List[str]:
    """
    Get list of all images in uploads folder.

    Returns:
        List of image filenames
    """
    if not os.path.exists(UPLOADS_FOLDER):
        return []

    try:
        files = os.listdir(UPLOADS_FOLDER)
        # Filter for image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        images = [f for f in files if any(f.lower().endswith(ext) for ext in image_extensions)]
        return sorted(images)
    except Exception as e:
        st.error(f"שגיאה בטעינת רשימת תמונות: {str(e)}")
        return []


def save_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Save an uploaded file to the uploads folder.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (success, filename_or_error)
    """
    try:
        # Ensure uploads folder exists
        os.makedirs(UPLOADS_FOLDER, exist_ok=True)

        # Save file
        file_path = os.path.join(UPLOADS_FOLDER, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        return True, uploaded_file.name
    except Exception as e:
        return False, f"שגיאה בשמירת הקובץ: {str(e)}"


def delete_image_file(filename: str) -> Tuple[bool, str]:
    """
    Delete an image file from uploads folder.

    Args:
        filename: Name of file to delete

    Returns:
        Tuple of (success, error_message)
    """
    try:
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, ""
        else:
            return False, "הקובץ לא נמצא"
    except Exception as e:
        return False, f"שגיאה במחיקת הקובץ: {str(e)}"


@require_role("editor")
def render_main_page_editor():
    """
    Render the main page editor interface.
    """
    st.header("📝 עריכת עמוד ראשי")

    # Load data
    data = load_matnas_data()

    if not data or "main_page" not in data:
        st.error("❌ לא ניתן לטעון את נתוני העמוד הראשי")
        return

    main_page = data["main_page"]

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["הגדרות כלליות", "ניהול תמונות", "ניהול וידאו"])

    with tab1:
        render_general_settings_tab(data, main_page)

    with tab2:
        render_images_tab(data, main_page)

    with tab3:
        render_videos_tab(data, main_page)


def render_general_settings_tab(data: Dict, main_page: Dict):
    """Render general settings tab."""
    st.subheader("⚙️ הגדרות כלליות")

    with st.form("general_settings_form"):
        # Title
        title = st.text_input("כותרת העמוד", value=main_page.get('title', ''),
                             help="הכותרת המוצגת בראש העמוד")

        # Description
        description = st.text_area("תיאור", value=main_page.get('description', ''),
                                  help="הטקסט המוצג מתחת לכותרת", height=100)

        # Background color
        background_color = st.color_picker("צבע רקע", value=main_page.get('background_color', '#ffffff'),
                                          help="בחר צבע רקע לעמוד")

        # Submit button
        submitted = st.form_submit_button("💾 שמור שינויים", use_container_width=True)

        if submitted:
            # Update data
            data["main_page"]["title"] = title
            data["main_page"]["description"] = description
            data["main_page"]["background_color"] = background_color

            # Save
            if save_matnas_data(data):
                st.success("✅ השינויים נשמרו בהצלחה!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ שגיאה בשמירת השינויים")


def render_images_tab(data: Dict, main_page: Dict):
    """Render images management tab."""
    st.subheader("🖼️ ניהול תמונות קרוסלה")

    current_images = main_page.get('images', [])

    # Upload new images
    st.write("**העלאת תמונות חדשות:**")
    uploaded_files = st.file_uploader(
        "בחר תמונות להעלאה",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        accept_multiple_files=True,
        help="ניתן להעלות מספר תמונות בבת אחת"
    )

    if uploaded_files:
        if st.button("📤 העלה תמונות", use_container_width=True):
            success_count = 0
            for uploaded_file in uploaded_files:
                success, result = save_uploaded_file(uploaded_file)
                if success:
                    # Add to main page images if not already there
                    if result not in current_images:
                        current_images.append(result)
                    success_count += 1
                else:
                    st.error(f"❌ {result}")

            if success_count > 0:
                # Save updated data
                data["main_page"]["images"] = current_images
                if save_matnas_data(data):
                    st.success(f"✅ {success_count} תמונות הועלו בהצלחה!")
                    st.rerun()

    st.divider()

    # Display current images
    st.write("**תמונות קיימות בקרוסלה:**")

    if not current_images:
        st.info("אין תמונות בקרוסלה כרגע")
    else:
        for idx, image in enumerate(current_images):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                st.write(f"{idx + 1}. {image}")

            with col2:
                # Preview
                image_path = os.path.join(UPLOADS_FOLDER, image)
                if os.path.exists(image_path):
                    if st.button("👁️", key=f"preview_{idx}", help="תצוגה מקדימה"):
                        st.session_state[f"preview_image_{idx}"] = True

            with col3:
                # Move up
                if idx > 0:
                    if st.button("⬆️", key=f"up_{idx}", help="העבר למעלה"):
                        current_images[idx], current_images[idx-1] = current_images[idx-1], current_images[idx]
                        data["main_page"]["images"] = current_images
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col4:
                # Move down
                if idx < len(current_images) - 1:
                    if st.button("⬇️", key=f"down_{idx}", help="העבר למטה"):
                        current_images[idx], current_images[idx+1] = current_images[idx+1], current_images[idx]
                        data["main_page"]["images"] = current_images
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col5:
                # Delete
                if st.button("🗑️", key=f"delete_{idx}", help="מחק תמונה"):
                    st.session_state[f"confirm_delete_{idx}"] = True
                    st.rerun()

            # Preview image
            if st.session_state.get(f"preview_image_{idx}", False):
                image_path = os.path.join(UPLOADS_FOLDER, image)
                if os.path.exists(image_path):
                    st.image(image_path, width=300)
                    if st.button("✖️ סגור", key=f"close_preview_{idx}"):
                        del st.session_state[f"preview_image_{idx}"]
                        st.rerun()

            # Confirm delete
            if st.session_state.get(f"confirm_delete_{idx}", False):
                st.warning(f"⚠️ האם אתה בטוח שברצונך למחוק את '{image}'?")
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, מחק", key=f"confirm_yes_{idx}"):
                        # Remove from list
                        current_images.pop(idx)
                        data["main_page"]["images"] = current_images

                        # Save
                        if save_matnas_data(data):
                            st.success("✅ התמונה נמחקה מהקרוסלה!")
                            del st.session_state[f"confirm_delete_{idx}"]
                            st.rerun()

                with col_no:
                    if st.button("ביטול", key=f"confirm_no_{idx}"):
                        del st.session_state[f"confirm_delete_{idx}"]
                        st.rerun()

            st.divider()


def render_videos_tab(data: Dict, main_page: Dict):
    """Render videos management tab."""
    st.subheader("🎥 ניהול וידאו")

    current_videos = main_page.get('videos', [])

    # Add new video
    st.write("**הוספת וידאו חדש:**")
    with st.form("add_video_form"):
        video_url = st.text_input(
            "כתובת URL של וידאו YouTube",
            placeholder="https://youtu.be/...",
            help="הדבק כתובת URL של וידאו מ-YouTube"
        )

        submitted = st.form_submit_button("➕ הוסף וידאו", use_container_width=True)

        if submitted:
            if video_url:
                if video_url not in current_videos:
                    current_videos.append(video_url)
                    data["main_page"]["videos"] = current_videos

                    if save_matnas_data(data):
                        st.success("✅ הוידאו נוסף בהצלחה!")
                        st.rerun()
                else:
                    st.warning("⚠️ הוידאו כבר קיים ברשימה")
            else:
                st.error("❌ נא להזין כתובת URL")

    st.divider()

    # Display current videos
    st.write("**וידאו קיימים:**")

    if not current_videos:
        st.info("אין וידאו כרגע")
    else:
        for idx, video_url in enumerate(current_videos):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"{idx + 1}. {video_url}")
                # Try to display video
                try:
                    st.video(video_url)
                except:
                    st.warning("לא ניתן להציג תצוגה מקדימה")

            with col2:
                if st.button("🗑️ מחק", key=f"delete_video_{idx}"):
                    st.session_state[f"confirm_delete_video_{idx}"] = True
                    st.rerun()

            # Confirm delete
            if st.session_state.get(f"confirm_delete_video_{idx}", False):
                st.warning("⚠️ האם אתה בטוח שברצונך למחוק וידאו זה?")
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, מחק", key=f"confirm_yes_video_{idx}"):
                        current_videos.pop(idx)
                        data["main_page"]["videos"] = current_videos

                        if save_matnas_data(data):
                            st.success("✅ הוידאו נמחק בהצלחה!")
                            del st.session_state[f"confirm_delete_video_{idx}"]
                            st.rerun()

                with col_no:
                    if st.button("ביטול", key=f"confirm_no_video_{idx}"):
                        del st.session_state[f"confirm_delete_video_{idx}"]
                        st.rerun()

            st.divider()
