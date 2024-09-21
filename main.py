import streamlit as st
import json
import os
import base64
from PIL import Image
from streamlit_carousel import carousel
from utils.PdfQAProcessor import PdfQAProcessor

# קונפיגורציה והגדרות
@st.cache_data
def load_data():
    try:
        with open('matnas_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("קובץ ה-JSON לא נמצא. אנא ודא שהקובץ 'matnas_data.json' קיים בתיקייה הנכונה.")
        return {}
    except json.JSONDecodeError:
        st.error("שגיאה בקריאת קובץ ה-JSON. אנא בדוק את תקינות הקובץ.")
        return {}

def set_page_config():
    st.set_page_config(page_title="צ'אטבוט המתנ\"ס", layout="wide")
    set_rtl_style()
    hide_streamlit_header_footer()

def set_rtl_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
            font-family: 'Heebo', sans-serif;
        }
        .stButton>button { float: right; }
        .stTextInput>div>div>input { text-align: right; }
        </style>
    """, unsafe_allow_html=True)

def hide_streamlit_header_footer():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
        </style>
    """, unsafe_allow_html=True)

def set_background_color(color):
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {color}; }}
        </style>
    """, unsafe_allow_html=True)

# פונקציות תצוגה
@st.cache_data
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def display_and_download_images(image_filenames, button_name):
    images = []
    for image_filename in image_filenames:
        image_path = os.path.abspath(os.path.join('uploads', image_filename))
        if os.path.exists(image_path):
            images.append({"title": f"{button_name} - {image_filename}", "img": image_path})
        else:
            st.error(f"התמונה {image_filename} לא נמצאה בנתיב: {image_path}")

    if len(images) == 1:
        st.image(images[0]["img"], use_column_width=True)
    elif len(images) > 1:
        carousel_items = [{"title": "", "text": "", "img": f"data:image/png;base64,{get_image_base64(img['img'])}"} for img in images]
        carousel(items=carousel_items, width=1.0)

    st.write("---")
    st.subheader("הורדת תמונות")
    for i, image in enumerate(images):
        image_b64 = get_image_base64(image["img"])
        st.markdown(f"""
            <a href="data:image/png;base64,{image_b64}" download="{image_filenames[i]}" 
               onclick="event.preventDefault(); const link = document.createElement('a'); link.href = this.href; link.download = this.download; document.body.appendChild(link); link.click(); document.body.removeChild(link);">
                הורד תמונה {i+1}
            </a>
        """, unsafe_allow_html=True)

def display_pdf_download(pdf_file):
    pdf_path = os.path.join('data', pdf_file)
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as pdf:
            pdf_bytes = pdf.read()
        st.download_button(
            label="📄 הורד PDF",
            data=pdf_bytes,
            file_name=pdf_file,
            mime="application/pdf",
        )
    else:
        st.error(f"קובץ ה-PDF {pdf_file} לא נמצא.")

def create_dialog(dialog_data):
    cols = st.columns([1] + [2] * len(dialog_data["buttons"]))
    
    if cols[0].button("חזרה לדף הראשי", key="back_to_main"):
        st.session_state.current_page = 'main'
        st.session_state.current_chat = None
        st.rerun()
    
    display_pdf_download(dialog_data["pdf_file"])
    
    for i, button in enumerate(dialog_data["buttons"], start=1):
        if cols[i].button(button["name"], key=f"{dialog_data['title']}_{button['key']}"):
            st.session_state.current_chat = button["key"]
            display_and_download_images(button["images"], button["name"])

# ניהול צ'אט
@st.cache_resource
def get_pdf_processor():
    return PdfQAProcessor()

def manage_chat(chat_key, system_prompt, pdf_name):
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}
    
    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []
    
    for message in st.session_state.chat_histories[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("הקלד את שאלתך כאן:"):
        st.session_state.chat_histories[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        processor = get_pdf_processor()
        answer = processor.process_pdf_and_answer(pdf_name, prompt, system_prompt)
        
        st.session_state.chat_histories[chat_key].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        
        st.rerun()

# תהליך ראשי
def main():
    # אתחול משתני המצב
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'main'
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}

    set_page_config()
    data = load_data()
    
    st.title("צ'אטבוט המתנ\"ס")
    
    if st.session_state.current_page == 'main':
        set_background_color(data["main_page"]["background_color"])
        st.subheader(data["main_page"]["description"])
        cols = st.columns(len(data["main_buttons"]))
        for i, button in enumerate(reversed(data["main_buttons"])):
            if cols[i].button(button["name"]):
                st.session_state.current_page = button["key"]
                st.rerun()
    else:
        dialog_data = data["dialogs"][st.session_state.current_page]
        set_background_color(dialog_data["background_color"])
        st.subheader(dialog_data["title"])
        st.write(dialog_data["description"])
        create_dialog(dialog_data)
        
        if dialog_data["is_chatbot"]:
            manage_chat(st.session_state.current_page, dialog_data["system_prompt"], dialog_data["pdf_file"])
        else:
            st.write("זהו מסך מידע. אין כאן אפשרות לצ'אט.")

if __name__ == "__main__":
    main()