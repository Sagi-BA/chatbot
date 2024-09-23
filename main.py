import streamlit as st
from streamlit_carousel import carousel
from streamlit_extras.stylable_container import stylable_container
import asyncio
import json
import os
import base64
from PIL import Image

from utils.PdfQAProcessor import PdfQAProcessor
from utils.counter import initialize_user_count, increment_user_count, get_user_count
from utils.init import initialize

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {        
        'counted': False,
    }

# קונפיגורציה והגדרות
@st.cache_data(show_spinner=False, ttl=None)
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
    hide_streamlit_header_footer()
    
    # הוספת CSS לקיבוע ה-chat_input בתחתית
    st.markdown("""
        <style>
        .stChatFloatingInputContainer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 10px;
            z-index: 1000;
        }
        .main .block-container {
            padding-bottom: 80px;  /* מרווח קטן כדי למנוע חפיפה עם ה-input */
        }
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
@st.cache_data(show_spinner=False, ttl=None)
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
        
        # Encode the PDF content
        b64_pdf = base64.b64encode(pdf_bytes).decode()
        
        # Create a custom styled button with PDF icon and black text (larger size)
        custom_button = f"""
        <a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_file}" 
           style="text-decoration: none; color: black; background-color: #f0f0f0; padding: 15px 25px; border-radius: 8px; display: inline-flex; align-items: center; border: 1px solid #ddd; font-size: 16px; transition: all 0.3s;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span style="margin-right: 15px; color: black;">הורד מסמך שהבוט אומן עליו</span>
        </a>
        """
        return custom_button
    else:
        return None

def page_transition_callback(next_page):
    st.session_state.next_page = next_page

def create_dialog(dialog_data):
    cols = st.columns([1] + [2] * len(dialog_data["buttons"]))
    
    if cols[0].button("חזרה לדף הראשי", key="back_to_main", on_click=page_transition_callback, args=('main',)):
        pass  # The actual state change is handled in the callback
    
    for i, button in enumerate(dialog_data["buttons"], start=1):
        button_key = f"{dialog_data['title']}_{button['key']}"
        if cols[i].button(button["name"], key=button_key, on_click=button_callback, args=(button["key"], button.get("images", []))):
            pass  # The actual state change is handled in the callback

def button_callback(button_key, images):
    st.session_state.current_chat = button_key
    st.session_state.current_images = images

@st.cache_resource
def get_pdf_processor():
    return PdfQAProcessor()

# ניהול צ'אט
def manage_chat(chat_key, system_prompt, pdf_name):
    if 'chat_histories' not in st.session_state:        
        st.session_state.chat_histories = {}
    
    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []
        # Clear conversation history when starting a new chat
        get_pdf_processor().clear_conversation_history()

    for message in st.session_state.chat_histories[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("הקלד את שאלתך כאן:"):  
        st.session_state.chat_histories[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner('מעבד את השאלה שלך...'):
            processor = get_pdf_processor()            
            answer = processor.process_pdf_and_answer(pdf_name, prompt, system_prompt)
        
        st.session_state.chat_histories[chat_key].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        
        st.rerun()
            
def load_html_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return f.read()
    
def load_footer():
    footer_path = os.path.join('utils', 'footer.md')
    if os.path.exists(footer_path):
        with open(footer_path, 'r', encoding='utf-8') as footer_file:
            return footer_file.read()
    return None  # Return None if the file doesn't exist

def display_images():
    if 'current_images' in st.session_state and st.session_state.current_images:
        display_and_download_images(st.session_state.current_images, st.session_state.current_chat)

# תהליך ראשי
async def main():
    
    # אתחול משתני המצב
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'main'
    if 'next_page' not in st.session_state:
        st.session_state.next_page = None
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}

    set_page_config()
    data = load_data()    
    title, image_path, footer_content = initialize()

    st.title(title, anchor=None, help="נוצר על ידי שגיא בר און")

    expander_html = load_html_file('expander.html')
    st.markdown(expander_html, unsafe_allow_html=True)
    
    # Handle page transitions
    if st.session_state.next_page is not None:
        st.session_state.current_page = st.session_state.next_page
        st.session_state.next_page = None
        st.session_state.current_chat = None
        st.session_state.current_images = []
        st.rerun()

    if st.session_state.current_page == 'main':
        set_background_color(data["main_page"]["background_color"])
        st.header(data["main_page"]["title"])
        st.subheader(data["main_page"]["description"])

        # Add carousel for main page if images are provided
        if "images" in data["main_page"]:
            main_images = data["main_page"]["images"]
            carousel_items = []
            for image in main_images:
                image_path = os.path.abspath(os.path.join('uploads', image))
                if os.path.exists(image_path):
                    carousel_items.append({
                        "title": "",
                        "text": "",
                        "img": f"data:image/png;base64,{get_image_base64(image_path)}"
                    })
                else:
                    st.error(f"התמונה {image} לא נמצאה בנתיב: {image_path}")
            
            if carousel_items:
                carousel(items=carousel_items, width=1.0)

        cols = st.columns(len(data["main_buttons"]))
        for i, button in enumerate(reversed(data["main_buttons"])):
            if cols[i].button(button["name"], on_click=page_transition_callback, args=(button["key"],)):
                pass  # The actual state change is handled in the callback
    else:
        dialog_data = data["dialogs"][st.session_state.current_page]
        set_background_color(dialog_data["background_color"])
        st.header(dialog_data["title"])
        
        # with col2:
        pdf_button = display_pdf_download(dialog_data["pdf_file"])
        if pdf_button:
            st.markdown(pdf_button, unsafe_allow_html=True)
        
        create_dialog(dialog_data)
        
        # Display images only if they are present in the current state
        if 'current_images' in st.session_state and st.session_state.current_images:
            display_images()
        
        if dialog_data["is_chatbot"]:            
            manage_chat(st.session_state.current_page, dialog_data["system_prompt"], dialog_data["pdf_file"])
            
            if st.session_state.chat_histories[st.session_state.current_page] == []:
                with st.chat_message("assistant"):
                    st.markdown(dialog_data["description"])   
        else:
            st.write("זהו מסך מידע. אין כאן אפשרות לצ'אט.")             

    # Display footer content    
    if footer_content:
        st.markdown("---")
        st.markdown(footer_content, unsafe_allow_html=True)
        
    # Display user count after the chatbot
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'><a href='https://api.whatsapp.com/send?phone=972549995050' alt='Contact Me' target='_blank'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)
        
if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    initialize_user_count()
    asyncio.run(main())