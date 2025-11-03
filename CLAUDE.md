# Chatbot Project - High-Level Documentation

## Project Overview

This is a Hebrew-language chatbot application built for a community center (Matnas Ha'emek) using Streamlit. The application provides information about various services including swimming pool details, events, general information, and a business index through an interactive multi-page interface with AI-powered Q&A capabilities.

## Project Goals

- Provide an intuitive Hebrew-language interface for community center visitors
- Enable AI-powered Q&A using RAG (Retrieval Augmented Generation) with PDF documents
- Display relevant images, videos, and information for different services
- Track user engagement through user counting
- Support multiple dialog flows (pool, events, general info, business index)

## Technology Stack

### Core Framework
- **Streamlit**: Main web application framework
- **Python**: Backend language (async support for main process)

### AI/ML Components
- **OpenAI API**: Text embeddings and chat completions
- **Groq API**: Alternative LLM provider support
- **PyMuPDF (fitz)**: PDF text extraction
- **NumPy**: Vector operations for embeddings and similarity calculations

### UI Components
- **streamlit-carousel**: Image carousel functionality
- **streamlit-extras**: Additional UI components (stylable containers)

### Additional Libraries
- **python-dotenv**: Environment variable management
- **aiohttp**: Async HTTP requests (for Telegram integration)
- **PIL (Pillow)**: Image processing

## Project Structure

```
chatbot/
├── main.py                          # Main application entry point
├── matnas_data.json                 # Configuration for UI, dialogs, and content
├── expander.html                    # Custom HTML components
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
├── data/                           # Data files
│   ├── user_count.json            # User tracking
│   ├── *.pdf                      # PDF documents for Q&A
├── embeddings/                     # Cached embeddings
│   └── *_embeddings.pkl           # Precomputed embeddings
├── uploads/                        # Images and media
│   └── *.jpeg, *.png              # UI images
└── utils/                          # Utility modules
    ├── PdfQAProcessor.py          # RAG implementation
    ├── counter.py                 # User counting
    ├── init.py                    # Initialization
    ├── chatbot.py                 # Chatbot utilities
    ├── TelegramSender.py          # Telegram integration
    ├── tools.py                   # General utilities
    └── footer.md                  # Footer content
```

## Key Components

### 1. Main Application ([main.py](main.py))

**Responsibilities:**
- Page configuration and styling
- Multi-page navigation system
- Chat interface management
- Image/video display
- User counting

**Key Functions:**
- `main()`: Async entry point managing page flow
- `manage_chat()`: Handles chatbot conversations
- `create_dialog()`: Renders dialog pages with buttons
- `display_and_download_images()`: Image gallery and download
- `load_data()`: Loads configuration from JSON

### 2. PDF Q&A Processor ([utils/PdfQAProcessor.py](utils/PdfQAProcessor.py))

**Responsibilities:**
- PDF text extraction
- Text chunking (2000 character chunks)
- Embedding generation and caching
- Semantic search using cosine similarity
- Answer generation with conversation history (10-message context window)

**Key Methods:**
- `process_pdf_and_answer()`: Main pipeline for Q&A
- `get_top_relevant_chunks()`: Retrieves top-3 relevant chunks
- `generate_answer()`: LLM-based answer generation
- `clear_conversation_history()`: Resets conversation context

### 3. Configuration ([matnas_data.json](matnas_data.json))

**Structure:**
- `main_page`: Landing page configuration
- `main_buttons`: Navigation buttons
- `dialogs`: Individual page configurations
  - `title`, `description`, `background_color`
  - `is_chatbot`: Enable/disable chat functionality
  - `system_prompt`: AI behavior instructions
  - `pdf_file`: Source document for RAG
  - `buttons`, `images`, `videos`: UI elements

## Coding Style

### General Principles
- Use Hebrew for UI strings and comments
- Keep functions focused and single-purpose
- Use type hints sparingly (existing code doesn't use them extensively)
- Async/await for main entry point only

### Naming Conventions
- **Functions**: `snake_case` (e.g., `load_data()`, `manage_chat()`)
- **Variables**: `snake_case` (e.g., `pdf_name`, `system_prompt`)
- **Classes**: `PascalCase` (e.g., `PdfQAProcessor`)
- **Constants**: `UPPER_CASE` (environment variables)

### Code Organization
- Use `@st.cache_data` for expensive operations (data loading, image encoding)
- Use `@st.cache_resource` for singleton instances (PdfQAProcessor)
- Separate display logic from data processing
- Keep session state management centralized

### Error Handling
- Use try-except blocks for file operations
- Provide Hebrew error messages for user-facing errors
- Log errors with print statements for debugging

## Important Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run main.py

# Run with auto-reload (development mode)
streamlit run main.py --server.runOnSave true
```

### Git Operations

```bash
# Reset to remote state (DESTRUCTIVE)
git reset --hard origin/main
git clean -fd

# Fetch latest changes
git fetch --all

# Pull changes
git pull
```

### Python Environment Setup (VS Code)

1. Open Command Palette: `Ctrl+Shift+P`
2. Select: `Python: Select Interpreter`
3. Choose appropriate Python environment

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
MODEL_TYPE="chatgpt"               # or "qroq" for Groq
MAX_TOKENS=1024                    # Response length limit
OPENAI_API_KEY="sk-..."           # OpenAI API key
EMBEDDINGS_MODEL="text-embedding-ada-002"  # or text-embedding-3-small
LLM_MODEL="gpt-4o"                # or "llama3-70b-8192" for Groq
GROQ_API_KEY="gsk_..."            # Required if MODEL_TYPE="qroq"
```

## RAG (Retrieval Augmented Generation) Flow

1. **Initialization**: Load or create PDF embeddings
2. **Question Processing**: User asks question in Hebrew
3. **Embedding**: Create embedding for question
4. **Retrieval**: Find top-3 most similar chunks using cosine similarity
5. **Context Building**: Combine relevant chunks + conversation history
6. **Generation**: LLM generates answer based on context
7. **History Update**: Store Q&A in conversation history (max 10 exchanges)

## Session State Management

Key session state variables:
- `state.counted`: User count flag
- `current_page`: Current page identifier
- `next_page`: Target page for transitions
- `current_chat`: Active chat session key
- `chat_histories`: Dictionary of chat histories per dialog
- `current_images`: Images to display
- `current_videos`: Videos to display

## Styling Notes

- RTL (Right-to-Left) layout for Hebrew text
- Custom CSS for hiding Streamlit branding
- Fixed chat input at bottom
- Background colors per dialog (configurable in JSON)
- Responsive layout with Streamlit columns

## User Tracking

- Increments counter on first session state initialization
- Persists count in `data/user_count.json`
- Displays total user count in footer with WhatsApp contact link

## PDF Document Requirements

- Place all PDF documents in `data/` folder
- PDFs should contain Hebrew text
- Text is extracted and chunked into 2000-character segments
- Embeddings are cached in `embeddings/` folder as `.pkl` files

## Known Patterns

### Adding a New Dialog

1. Add PDF document to `data/`
2. Update `matnas_data.json`:
   - Add button to `main_buttons`
   - Add dialog configuration to `dialogs`
3. Add images to `uploads/`
4. Test chat functionality and image display

### Modifying System Prompts

Edit the `system_prompt` field in `matnas_data.json` for each dialog. The system prompt controls:
- AI personality and tone
- Response format
- Handling of missing information
- Language and cultural context

### Clearing Embeddings Cache

Delete files in `embeddings/` folder to force regeneration:
```bash
rm embeddings/*.pkl
```

## Common Issues

### Git Working Tree Error
**Error**: "Please clean your repository working tree before checkout"

**Solution**:
```bash
# Option 1: Stash changes (keeps them)
git stash

# Option 2: Discard changes (permanent)
git reset --hard HEAD
git clean -fd

# Option 3: Commit changes
git add .
git commit -m "Description of changes"
```

### Missing API Keys
Ensure `.env` file exists with valid API keys for OpenAI/Groq.

### PDF Not Found
Verify PDF files are in `data/` folder and filenames match `matnas_data.json`.

### Embedding Errors
Delete cached embeddings and regenerate:
```bash
rm embeddings/*.pkl
```

## Future Considerations

- Add authentication for admin features
- Implement analytics dashboard
- Support additional languages
- Add voice input/output
- Integrate with CRM systems
- Implement A/B testing for system prompts
- Add feedback mechanism for answer quality

## Contact

Created by: Shagy Bar-On
WhatsApp Support: +972-54-999-5050

---

**Last Updated**: 2025-11-03
