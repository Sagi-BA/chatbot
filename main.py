import streamlit as st
import json
import os
import base64
from PIL import Image
from streamlit_carousel import carousel
from utils.chatbot import get_prompt

# פונקציה להגדרת עיצוב RTL
def set_rtl_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');

        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
            font-family: 'Heebo', sans-serif;
        }
        .stButton>button {
            float: right;
        }
        .stTextInput>div>div>input {
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# פונקציה לשינוי צבע הרקע
def set_background_color(color):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# טעינת הנתונים מקובץ JSON
def load_data():
    if os.path.exists('matnas_data.json'):
        with open('matnas_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)

# פונקציה להמרת תמונה ל-base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# פונקציה להצגת תמונה והורדתה
def display_and_download_images(image_filenames, button_name):
    try:
        images = []
        for image_filename in image_filenames:
            image_path = os.path.abspath(os.path.join('uploads', image_filename))
            if not os.path.exists(image_path):
                st.error(f"התמונה {image_filename} לא נמצאה בנתיב: {image_path}")
                continue
            
            images.append({"title": f"{button_name} - {image_filename}", "img": image_path})

        if len(images) == 1:
            st.image(images[0]["img"], use_column_width=True)
        elif len(images) > 1:
            carousel_items = [{"title": "", "text": "", "img": f"data:image/png;base64,{get_image_base64(img['img'])}"} for img in images]
            carousel(items=carousel_items, width=1.0)

        st.write("---")
        st.subheader("הורדת תמונות")
        for i, image in enumerate(images):
            image_b64 = get_image_base64(image["img"])
            download_link = f"""
            <a href="data:image/png;base64,{image_b64}" download="{image_filenames[i]}" 
               onclick="event.preventDefault(); const link = document.createElement('a'); link.href = this.href; link.download = this.download; document.body.appendChild(link); link.click(); document.body.removeChild(link);">
                הורד תמונה {i+1}
            </a>
            """
            st.markdown(download_link, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"שגיאה בטעינת התמונות: {str(e)}")

# פונקציה ליצירת דיאלוג
def create_dialog(dialog_data):
    st.subheader(dialog_data["title"])
    st.write(dialog_data["description"])
    
    # Create a row for all buttons including 'Back to Main'
    cols = st.columns(len(dialog_data["buttons"]) + 1)
    
    # 'Back to Main' button on the left (which is visually on the right in RTL)
    if cols[0].button("חזרה לדף הראשי", key="back_to_main"):
        st.session_state.current_page = 'main'
        st.session_state.current_chat = None
        st.rerun()
    
    # Other buttons
    for i, button in enumerate(dialog_data["buttons"], start=1):
        if cols[i].button(button["name"], key=f"{dialog_data['title']}_{button['key']}"):
            st.session_state.current_chat = button["key"]
            display_and_download_images(button["images"], button["name"])

# פונקציה לניהול הצ'אט
def manage_chat(chat_key, system_prompt):
    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []
    
    # הצגת היסטוריית הצ'אט
    for message in st.session_state.chat_histories[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # קבלת קלט מהמשתמש
    if prompt := st.chat_input("הקלד את שאלתך כאן:"):
        # הוספת ההודעה של המשתמש להיסטוריה
        st.session_state.chat_histories[chat_key].append({"role": "user", "content": prompt})
        
        # הצגת ההודעה של המשתמש
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # קבלת תשובה מה-AI
        response = get_prompt(system_prompt, prompt)
        
        # הוספת התשובה להיסטוריה
        st.session_state.chat_histories[chat_key].append({"role": "assistant", "content": response})
        
        # הצגת התשובה
        with st.chat_message("assistant"):
            st.markdown(response)

        st.rerun()


def hide_streamlit_header_footer():
    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
                content:'goodbye'; 
                visibility: visible;
                display: block;
                position: relative;
                #background-color: red;
                padding: 5px;
                top: 2px;
            }
            header {visibility: hidden;}
            #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)

# הגדרת המצב ההתחלתי של האפליקציה
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None
if 'chat_histories' not in st.session_state:
    st.session_state.chat_histories = {}

# הגדרת עיצוב RTL
set_rtl_style()

# טעינת הנתונים
data = load_data()
hide_streamlit_header_footer()

# עיצוב הדף הראשי
st.title("צ'אטבוט המתנ\"ס")

if st.session_state.current_page == 'main':
    set_background_color(data["main_page"]["background_color"])
    st.subheader(data["main_page"]["description"])
    cols = st.columns(len(data["main_buttons"]))
    for i, button in enumerate(reversed(data["main_buttons"])):  # Reverse the order for RTL
        if cols[i].button(button["name"]):
            st.session_state.current_page = button["key"]
            st.rerun()

else:
    dialog_data = data["dialogs"][st.session_state.current_page]
    set_background_color(dialog_data["background_color"])    
    create_dialog(dialog_data)
    
    if dialog_data["is_chatbot"]:
        manage_chat(st.session_state.current_page, dialog_data["system_prompt"])
    else:
        st.write("זהו מסך מידע. אין כאן אפשרות לצ'אט.")