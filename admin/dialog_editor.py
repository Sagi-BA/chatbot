"""
Dialog Editor Module for Admin Panel
Allows editing of individual dialog sections with sub-buttons, images, and settings
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
            log_audit_event("dialog_updated", user.get('username', 'unknown'),
                          "Dialog configuration updated")

        return True
    except Exception as e:
        st.error(f"שגיאה בשמירת הנתונים: {str(e)}")
        return False


def get_uploaded_images() -> List[str]:
    """Get list of all images in uploads folder."""
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


def get_uploaded_pdfs() -> List[str]:
    """Get list of all PDFs in data folder."""
    data_folder = "data"
    if not os.path.exists(data_folder):
        return []

    try:
        files = os.listdir(data_folder)
        pdfs = [f for f in files if f.lower().endswith('.pdf')]
        return sorted(pdfs)
    except Exception as e:
        st.error(f"שגיאה בטעינת רשימת PDFs: {str(e)}")
        return []


def save_uploaded_file(uploaded_file, folder: str = UPLOADS_FOLDER) -> Tuple[bool, str]:
    """Save an uploaded file to specified folder."""
    try:
        # Ensure folder exists
        os.makedirs(folder, exist_ok=True)

        # Save file
        file_path = os.path.join(folder, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        return True, uploaded_file.name
    except Exception as e:
        return False, f"שגיאה בשמירת הקובץ: {str(e)}"


@require_role("editor")
def render_dialog_editor():
    """Render the dialog editor interface."""
    st.header("💬 עורך דיאלוגים")

    # Load data
    data = load_matnas_data()

    if not data or "dialogs" not in data:
        st.error("❌ לא ניתן לטעון את נתוני הדיאלוגים")
        return

    dialogs = data["dialogs"]

    if not dialogs:
        st.info("אין דיאלוגים כרגע. צור כפתור חדש בעמוד 'כפתורים ראשיים' כדי ליצור דיאלוג.")
        return

    # Dialog selection
    dialog_keys = list(dialogs.keys())
    dialog_names = [dialogs[key].get('title', key) for key in dialog_keys]

    selected_index = st.selectbox(
        "בחר דיאלוג לעריכה",
        range(len(dialog_keys)),
        format_func=lambda i: f"{dialog_names[i]} ({dialog_keys[i]})",
        key="dialog_selector"
    )

    selected_key = dialog_keys[selected_index]
    dialog = dialogs[selected_key]

    st.divider()

    # Create tabs for different editing areas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "הגדרות כלליות",
        "הגדרות צ'אטבוט",
        "תמונות",
        "וידאו",
        "כפתורי משנה"
    ])

    with tab1:
        render_general_settings_tab(data, selected_key, dialog)

    with tab2:
        render_chatbot_settings_tab(data, selected_key, dialog)

    with tab3:
        render_dialog_images_tab(data, selected_key, dialog)

    with tab4:
        render_dialog_videos_tab(data, selected_key, dialog)

    with tab5:
        render_sub_buttons_tab(data, selected_key, dialog)


def normalize_color(color: str) -> str:
    """
    Normalize color to hex format.
    Converts CSS color names to hex.
    """
    # Common CSS colors to hex mapping
    css_colors = {
        'darksalmon': '#E9967A',
        'white': '#FFFFFF',
        'black': '#000000',
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0000FF',
        'yellow': '#FFFF00',
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'silver': '#C0C0C0',
        'gray': '#808080',
        'maroon': '#800000',
        'olive': '#808000',
        'lime': '#00FF00',
        'aqua': '#00FFFF',
        'teal': '#008080',
        'navy': '#000080',
        'fuchsia': '#FF00FF',
        'purple': '#800080'
    }

    # If it's already a hex color, return it
    if color.startswith('#'):
        return color

    # Convert CSS color name to hex
    color_lower = color.lower()
    if color_lower in css_colors:
        return css_colors[color_lower]

    # Default fallback
    return '#ffffff'


def render_general_settings_tab(data: Dict, dialog_key: str, dialog: Dict):
    """Render general settings tab for dialog."""
    st.subheader("⚙️ הגדרות כלליות")

    with st.form(f"general_settings_{dialog_key}"):
        # Title
        title = st.text_input("כותרת הדיאלוג", value=dialog.get('title', ''),
                             help="הכותרת המוצגת בראש הדף")

        # Description
        description = st.text_area("תיאור", value=dialog.get('description', ''),
                                  help="הטקסט המוצג מתחת לכותרת", height=100)

        # Background color - normalize to hex
        current_color = normalize_color(dialog.get('background_color', '#ffffff'))
        background_color = st.color_picker("צבע רקע", value=current_color,
                                          help="בחר צבע רקע לדיאלוג")

        # Submit button
        submitted = st.form_submit_button("💾 שמור שינויים", use_container_width=True)

        if submitted:
            # Update data
            data["dialogs"][dialog_key]["title"] = title
            data["dialogs"][dialog_key]["description"] = description
            data["dialogs"][dialog_key]["background_color"] = background_color

            # Save
            if save_matnas_data(data):
                st.success("✅ השינויים נשמרו בהצלחה!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ שגיאה בשמירת השינויים")


def render_chatbot_settings_tab(data: Dict, dialog_key: str, dialog: Dict):
    """Render chatbot settings tab for dialog."""
    st.subheader("🤖 הגדרות צ'אטבוט")

    with st.form(f"chatbot_settings_{dialog_key}"):
        # Is chatbot enabled
        is_chatbot = st.checkbox("הפעל צ'אטבוט", value=dialog.get('is_chatbot', False),
                                help="האם להציג ממשק צ'אט בדיאלוג זה")

        # System prompt
        system_prompt = st.text_area(
            "הנחיות מערכת (System Prompt)",
            value=dialog.get('system_prompt', ''),
            help="ההנחיות שמגדירות את התנהגות הצ'אטבוט",
            height=200
        )

        # PDF file selection
        available_pdfs = get_uploaded_pdfs()
        current_pdf = dialog.get('pdf_file', '')

        if current_pdf and current_pdf in available_pdfs:
            default_index = available_pdfs.index(current_pdf)
        else:
            default_index = 0 if available_pdfs else None

        if available_pdfs:
            pdf_file = st.selectbox(
                "קובץ PDF למקור מידע",
                options=available_pdfs,
                index=default_index,
                help="בחר קובץ PDF שישמש כמקור מידע לצ'אטבוט"
            )
        else:
            st.warning("⚠️ אין קבצי PDF זמינים. העלה קובץ PDF לתיקיית 'data'")
            pdf_file = current_pdf

        # Upload new PDF
        st.write("**העלאת PDF חדש:**")
        uploaded_pdf = st.file_uploader(
            "העלה קובץ PDF חדש",
            type=['pdf'],
            help="העלה קובץ PDF לתיקיית data"
        )

        # Submit button
        col1, col2 = st.columns([3, 1])

        with col1:
            submitted = st.form_submit_button("💾 שמור שינויים", use_container_width=True)

        with col2:
            upload_pdf = st.form_submit_button("📤 העלה PDF", use_container_width=True)

        if submitted:
            # Update data
            data["dialogs"][dialog_key]["is_chatbot"] = is_chatbot
            data["dialogs"][dialog_key]["system_prompt"] = system_prompt
            data["dialogs"][dialog_key]["pdf_file"] = pdf_file

            # Save
            if save_matnas_data(data):
                st.success("✅ הגדרות הצ'אטבוט נשמרו בהצלחה!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ שגיאה בשמירת השינויים")

        if upload_pdf and uploaded_pdf:
            success, result = save_uploaded_file(uploaded_pdf, folder="data")
            if success:
                st.success(f"✅ הקובץ {result} הועלה בהצלחה!")
                st.rerun()
            else:
                st.error(f"❌ {result}")


def render_dialog_images_tab(data: Dict, dialog_key: str, dialog: Dict):
    """Render images management tab for dialog."""
    st.subheader("🖼️ ניהול תמונות דיאלוג")

    current_images = dialog.get('images', [])

    # Upload new images
    st.write("**העלאת תמונות חדשות:**")
    uploaded_files = st.file_uploader(
        "בחר תמונות להעלאה",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        accept_multiple_files=True,
        help="ניתן להעלות מספר תמונות בבת אחת",
        key=f"upload_images_{dialog_key}"
    )

    if uploaded_files:
        if st.button("📤 העלה תמונות", use_container_width=True, key=f"upload_btn_{dialog_key}"):
            success_count = 0
            for uploaded_file in uploaded_files:
                success, result = save_uploaded_file(uploaded_file)
                if success:
                    # Add to dialog images if not already there
                    if result not in current_images:
                        current_images.append(result)
                    success_count += 1
                else:
                    st.error(f"❌ {result}")

            if success_count > 0:
                # Save updated data
                if 'images' not in data["dialogs"][dialog_key]:
                    data["dialogs"][dialog_key]['images'] = []
                data["dialogs"][dialog_key]["images"] = current_images
                if save_matnas_data(data):
                    st.success(f"✅ {success_count} תמונות הועלו בהצלחה!")
                    st.rerun()

    st.divider()

    # Display current images
    st.write("**תמונות קיימות בדיאלוג:**")

    if not current_images:
        st.info("אין תמונות בדיאלוג כרגע")
    else:
        for idx, image in enumerate(current_images):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                st.write(f"{idx + 1}. {image}")

            with col2:
                # Preview
                image_path = os.path.join(UPLOADS_FOLDER, image)
                if os.path.exists(image_path):
                    if st.button("👁️", key=f"preview_dialog_{dialog_key}_{idx}", help="תצוגה מקדימה"):
                        st.session_state[f"preview_dialog_image_{dialog_key}_{idx}"] = True

            with col3:
                # Move up
                if idx > 0:
                    if st.button("⬆️", key=f"up_dialog_{dialog_key}_{idx}", help="העבר למעלה"):
                        current_images[idx], current_images[idx-1] = current_images[idx-1], current_images[idx]
                        data["dialogs"][dialog_key]["images"] = current_images
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col4:
                # Move down
                if idx < len(current_images) - 1:
                    if st.button("⬇️", key=f"down_dialog_{dialog_key}_{idx}", help="העבר למטה"):
                        current_images[idx], current_images[idx+1] = current_images[idx+1], current_images[idx]
                        data["dialogs"][dialog_key]["images"] = current_images
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col5:
                # Delete
                if st.button("🗑️", key=f"delete_dialog_{dialog_key}_{idx}", help="מחק תמונה"):
                    st.session_state[f"confirm_delete_dialog_{dialog_key}_{idx}"] = True
                    st.rerun()

            # Preview image
            if st.session_state.get(f"preview_dialog_image_{dialog_key}_{idx}", False):
                image_path = os.path.join(UPLOADS_FOLDER, image)
                if os.path.exists(image_path):
                    st.image(image_path, width=300)
                    if st.button("✖️ סגור", key=f"close_preview_dialog_{dialog_key}_{idx}"):
                        del st.session_state[f"preview_dialog_image_{dialog_key}_{idx}"]
                        st.rerun()

            # Confirm delete
            if st.session_state.get(f"confirm_delete_dialog_{dialog_key}_{idx}", False):
                st.warning(f"⚠️ האם אתה בטוח שברצונך למחוק את '{image}'?")
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, מחק", key=f"confirm_yes_dialog_{dialog_key}_{idx}"):
                        # Remove from list
                        current_images.pop(idx)
                        data["dialogs"][dialog_key]["images"] = current_images

                        # Save
                        if save_matnas_data(data):
                            st.success("✅ התמונה נמחקה!")
                            del st.session_state[f"confirm_delete_dialog_{dialog_key}_{idx}"]
                            st.rerun()

                with col_no:
                    if st.button("ביטול", key=f"confirm_no_dialog_{dialog_key}_{idx}"):
                        del st.session_state[f"confirm_delete_dialog_{dialog_key}_{idx}"]
                        st.rerun()

            st.divider()


def render_dialog_videos_tab(data: Dict, dialog_key: str, dialog: Dict):
    """Render videos management tab for dialog."""
    st.subheader("🎥 ניהול וידאו דיאלוג")

    current_videos = dialog.get('videos', [])

    # Add new video
    st.write("**הוספת וידאו חדש:**")
    with st.form(f"add_video_{dialog_key}"):
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
                    if 'videos' not in data["dialogs"][dialog_key]:
                        data["dialogs"][dialog_key]['videos'] = []
                    data["dialogs"][dialog_key]["videos"] = current_videos

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
                if st.button("🗑️ מחק", key=f"delete_video_dialog_{dialog_key}_{idx}"):
                    st.session_state[f"confirm_delete_video_dialog_{dialog_key}_{idx}"] = True
                    st.rerun()

            # Confirm delete
            if st.session_state.get(f"confirm_delete_video_dialog_{dialog_key}_{idx}", False):
                st.warning("⚠️ האם אתה בטוח שברצונך למחוק וידאו זה?")
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("כן, מחק", key=f"confirm_yes_video_dialog_{dialog_key}_{idx}"):
                        current_videos.pop(idx)
                        data["dialogs"][dialog_key]["videos"] = current_videos

                        if save_matnas_data(data):
                            st.success("✅ הוידאו נמחק בהצלחה!")
                            del st.session_state[f"confirm_delete_video_dialog_{dialog_key}_{idx}"]
                            st.rerun()

                with col_no:
                    if st.button("ביטול", key=f"confirm_no_video_dialog_{dialog_key}_{idx}"):
                        del st.session_state[f"confirm_delete_video_dialog_{dialog_key}_{idx}"]
                        st.rerun()

            st.divider()


def render_sub_buttons_tab(data: Dict, dialog_key: str, dialog: Dict):
    """Render sub-buttons management tab for dialog."""
    st.subheader("🔘 ניהול כפתורי משנה")

    sub_buttons = dialog.get('buttons', [])

    # Create tabs
    tab1, tab2 = st.tabs(["רשימת כפתורים", "הוסף כפתור"])

    with tab1:
        render_sub_buttons_list(data, dialog_key, sub_buttons)

    with tab2:
        render_add_sub_button(data, dialog_key, sub_buttons)


def render_sub_buttons_list(data: Dict, dialog_key: str, sub_buttons: List[Dict]):
    """Render sub-buttons list."""
    st.write("**כפתורי משנה קיימים:**")

    if not sub_buttons:
        st.info("אין כפתורי משנה כרגע")
        return

    for idx, button in enumerate(sub_buttons):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

            with col1:
                st.write(f"**{button.get('name')}**")

            with col2:
                st.caption(f"מפתח: `{button.get('key')}`")

            with col3:
                # Move up
                if idx > 0:
                    if st.button("⬆️", key=f"sub_btn_up_{dialog_key}_{idx}", help="העבר למעלה"):
                        sub_buttons[idx], sub_buttons[idx-1] = sub_buttons[idx-1], sub_buttons[idx]
                        data["dialogs"][dialog_key]["buttons"] = sub_buttons
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col4:
                # Move down
                if idx < len(sub_buttons) - 1:
                    if st.button("⬇️", key=f"sub_btn_down_{dialog_key}_{idx}", help="העבר למטה"):
                        sub_buttons[idx], sub_buttons[idx+1] = sub_buttons[idx+1], sub_buttons[idx]
                        data["dialogs"][dialog_key]["buttons"] = sub_buttons
                        if save_matnas_data(data):
                            st.success("✅ הסדר עודכן!")
                            st.rerun()

            with col5:
                # Edit button
                if st.button("✏️", key=f"sub_btn_edit_{dialog_key}_{idx}", help="ערוך"):
                    st.session_state[f"editing_sub_button_{dialog_key}_{idx}"] = True
                    st.rerun()

            # Show button images
            button_images = button.get('images', [])
            if button_images:
                st.caption(f"תמונות: {len(button_images)}")

            # Edit form
            if st.session_state.get(f"editing_sub_button_{dialog_key}_{idx}", False):
                render_edit_sub_button_form(data, dialog_key, sub_buttons, idx)

            st.divider()

    # Delete button section
    st.subheader("🗑️ מחיקת כפתור משנה")

    button_to_delete = st.selectbox(
        "בחר כפתור למחיקה",
        options=range(len(sub_buttons)),
        format_func=lambda i: f"{sub_buttons[i].get('name')} ({sub_buttons[i].get('key')})",
        key=f"delete_sub_button_select_{dialog_key}"
    )

    if st.button("🗑️ מחק כפתור נבחר", type="secondary", key=f"delete_sub_btn_{dialog_key}"):
        st.session_state[f"confirm_delete_sub_button_{dialog_key}"] = button_to_delete
        st.rerun()

    # Confirmation dialog
    if f"confirm_delete_sub_button_{dialog_key}" in st.session_state:
        idx = st.session_state[f"confirm_delete_sub_button_{dialog_key}"]
        button = sub_buttons[idx]

        st.warning(f"⚠️ האם אתה בטוח שברצונך למחוק את הכפתור **'{button.get('name')}'**?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ כן, מחק", use_container_width=True, key=f"confirm_yes_sub_{dialog_key}"):
                sub_buttons.pop(idx)
                data["dialogs"][dialog_key]["buttons"] = sub_buttons

                if save_matnas_data(data):
                    st.success("✅ הכפתור נמחק בהצלחה!")
                    del st.session_state[f"confirm_delete_sub_button_{dialog_key}"]
                    st.rerun()

        with col2:
            if st.button("❌ ביטול", use_container_width=True, key=f"confirm_no_sub_{dialog_key}"):
                del st.session_state[f"confirm_delete_sub_button_{dialog_key}"]
                st.rerun()


def render_edit_sub_button_form(data: Dict, dialog_key: str, sub_buttons: List[Dict], idx: int):
    """Render edit sub-button form."""
    button = sub_buttons[idx]

    with st.form(key=f"edit_sub_button_form_{dialog_key}_{idx}"):
        st.subheader(f"✏️ עריכת כפתור: {button.get('name')}")

        # Button name
        name = st.text_input("שם הכפתור", value=button.get('name', ''))

        # Button key
        key = st.text_input("מפתח (key)", value=button.get('key', ''),
                           help="מזהה ייחודי באנגלית")

        # Button images
        st.write("**תמונות כפתור:**")
        available_images = get_uploaded_images()
        button_images = button.get('images', [])

        selected_images = st.multiselect(
            "בחר תמונות לכפתור",
            options=available_images,
            default=[img for img in button_images if img in available_images],
            help="ניתן לבחור מספר תמונות"
        )

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
            else:
                # Update button
                sub_buttons[idx] = {
                    "name": name,
                    "key": key,
                    "images": selected_images
                }

                data["dialogs"][dialog_key]["buttons"] = sub_buttons

                if save_matnas_data(data):
                    st.success("✅ הכפתור עודכן בהצלחה!")
                    del st.session_state[f"editing_sub_button_{dialog_key}_{idx}"]
                    st.rerun()

        if cancelled:
            del st.session_state[f"editing_sub_button_{dialog_key}_{idx}"]
            st.rerun()


def render_add_sub_button(data: Dict, dialog_key: str, sub_buttons: List[Dict]):
    """Render add sub-button form."""
    st.write("**הוספת כפתור משנה חדש:**")

    with st.form(f"add_sub_button_{dialog_key}"):
        # Button name
        name = st.text_input("שם הכפתור", placeholder="לדוגמה: זמני פתיחה")

        # Button key
        key = st.text_input("מפתח (key)", placeholder="לדוגמה: opening_hours",
                          help="מזהה ייחודי באנגלית")

        # Button images
        st.write("**תמונות כפתור:**")
        available_images = get_uploaded_images()

        selected_images = st.multiselect(
            "בחר תמונות לכפתור",
            options=available_images,
            help="ניתן לבחור מספר תמונות",
            key=f"new_sub_images_{dialog_key}"
        )

        # Submit
        submitted = st.form_submit_button("➕ הוסף כפתור", use_container_width=True)

        if submitted:
            if not name:
                st.error("❌ שם הכפתור לא יכול להיות ריק")
            elif not key:
                st.error("❌ מפתח לא יכול להיות ריק")
            elif any(btn.get('key') == key for btn in sub_buttons):
                st.error(f"❌ המפתח '{key}' כבר קיים")
            else:
                # Add button
                new_button = {
                    "name": name,
                    "key": key,
                    "images": selected_images
                }
                sub_buttons.append(new_button)

                data["dialogs"][dialog_key]["buttons"] = sub_buttons

                if save_matnas_data(data):
                    st.success(f"✅ הכפתור '{name}' נוסף בהצלחה!")
                    st.balloons()
                    st.rerun()
