# 🚀 Embedding Migration Guide: OpenAI → MPA/sambert

**Date:** November 3, 2025
**Migration Type:** OpenAI Embeddings → MPA/sambert (Hebrew-Optimized)
**Estimated Time:** 30-45 minutes
**Risk Level:** LOW ✅

---

## 📋 What's Changed

### Before (OpenAI):
- Embedding Model: text-embedding-3-small or text-embedding-ada-002
- Dimensions: 1536
- Cost: ~$0.0004/month (negligible)
- Language: Multilingual (good for Hebrew)

### After (MPA/sambert):
- Embedding Model: MPA/sambert (Hugging Face)
- Dimensions: 768 (50% smaller!)
- Cost: **FREE** (local inference)
- Language: **Hebrew-optimized** (better for Hebrew text!)

---

## ✅ Prerequisites

Before starting, ensure you have:

- [x] Python 3.8+ installed
- [x] Git access to the repository
- [x] Admin access to the server/environment
- [x] Backup of current `.env` file
- [x] ~2GB free RAM (for model)
- [x] ~500MB free disk space (for model download)

---

## 🛠️ Migration Steps

### Step 1: Backup Current System (5 minutes)

```bash
# Navigate to project directory
cd c:\projects\chatbot

# Backup current embeddings
mkdir embeddings_backup
copy embeddings\*.pkl embeddings_backup\

# Backup .env file
copy .env .env.backup

# Verify backups
dir embeddings_backup
dir .env.backup
```

**Expected Result:**
```
embeddings_backup/
  - business_index_embeddings.pkl
  - pool_embeddings.pkl
```

---

### Step 2: Install New Dependencies (10 minutes)

```bash
# Install new Python packages
pip install sentence-transformers>=2.2.2
pip install torch>=2.0.0
pip install transformers>=4.35.0
pip install huggingface-hub>=0.19.0

# Verify installation
python -c "from sentence_transformers import SentenceTransformer; print('✅ Installation successful!')"
```

**Expected Output:**
```
✅ Installation successful!
```

**If GPU Available (Optional but Faster):**
```bash
# Install GPU-accelerated PyTorch (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Troubleshooting:**
- **Error: "No module named 'sentence_transformers'"**
  - Solution: Run `pip install sentence-transformers`
- **Error: "torch not found"**
  - Solution: Run `pip install torch`

---

### Step 3: Update Environment Configuration (3 minutes)

**Edit your `.env` file:**

```env
# OLD configuration (comment out or remove):
# EMBEDDINGS_MODEL="text-embedding-3-small"

# NEW configuration (add these lines):
EMBEDDING_METHOD="local"  # Use local MPA/sambert model
# HUGGINGFACE_API_KEY="hf_xxxxx"  # Optional, not needed for local

# Keep existing LLM configuration:
MODEL_TYPE="chatgpt"  # or "qroq"
MAX_TOKENS=1024
OPENAI_API_KEY="sk-xxxxx"  # Still needed for LLM generation
LLM_MODEL="gpt-4o"  # or "llama3-70b-8192"
```

**Minimal .env Example:**
```env
MODEL_TYPE="chatgpt"
MAX_TOKENS=1024
OPENAI_API_KEY="sk-xxxxx"
LLM_MODEL="gpt-4o"
EMBEDDING_METHOD="local"
```

---

### Step 4: Replace PdfQAProcessor (2 minutes)

**Windows:**
```bash
# Backup original file
copy utils\PdfQAProcessor.py utils\PdfQAProcessor_OLD.py

# Replace with new version
copy utils\PdfQAProcessor_new.py utils\PdfQAProcessor.py
```

**Linux/Mac:**
```bash
# Backup original file
cp utils/PdfQAProcessor.py utils/PdfQAProcessor_OLD.py

# Replace with new version
cp utils/PdfQAProcessor_new.py utils/PdfQAProcessor.py
```

**Verify:**
```bash
python -c "from utils.PdfQAProcessor import PdfQAProcessor; print('✅ File replaced successfully!')"
```

---

### Step 5: Delete Old Embeddings (1 minute)

**IMPORTANT:** Old embeddings are 1536-dim, new ones are 768-dim. They're incompatible!

```bash
# Delete old embeddings (they'll be regenerated)
del embeddings\*.pkl  # Windows
# rm embeddings/*.pkl  # Linux/Mac

# Verify deletion
dir embeddings  # Should be empty or only have README
```

**Why Delete?**
- Old embeddings: 1536 dimensions (OpenAI)
- New embeddings: 768 dimensions (MPA/sambert)
- Incompatible formats!

---

### Step 6: Test Embedding Generation (10 minutes)

**Test Script:**

Create `test_migration.py`:

```python
from utils.PdfQAProcessor import PdfQAProcessor

print("🔄 Initializing PdfQAProcessor...")
processor = PdfQAProcessor()

print("\n🔄 Testing embedding generation...")
test_text = "שלום עולם - בדיקת מערכת"
embedding = processor.create_embedding(test_text)

print(f"✅ Embedding generated!")
print(f"📊 Dimensions: {len(embedding)}")
print(f"📊 First 5 values: {embedding[:5]}")

# Expected: 768 dimensions
assert len(embedding) == 768, f"❌ Wrong dimensions: {len(embedding)}"
print("\n✅ All tests passed!")
```

**Run Test:**
```bash
python test_migration.py
```

**Expected Output:**
```
🔄 Initializing PdfQAProcessor...
🔄 Loading MPA/sambert model locally (Hebrew-optimized)...
✅ MPA/sambert model loaded successfully!
📊 Embedding dimensions: 768 (optimized for Hebrew)

🔄 Testing embedding generation...
✅ Embedding generated!
📊 Dimensions: 768
📊 First 5 values: [0.123, -0.456, 0.789, ...]

✅ All tests passed!
```

**On First Run:**
- Model download: ~420MB (one-time)
- Download time: 2-5 minutes
- Model is cached for future use

---

### Step 7: Test with Actual PDF (10 minutes)

**Test Script:**

```python
from utils.PdfQAProcessor import PdfQAProcessor

# Initialize
processor = PdfQAProcessor()

# System prompt (Hebrew)
system_prompt = """
אתה עוזר חכם שתמיד מתנהג כמו נציג שירות מקצועי, אמפתי ומבין.
עליך לספק תשובות ברורות, מדויקות ומכבדות.
"""

# Test with pool.pdf
pdf_name = "pool.pdf"
question = "מה שעות הפתיחה של הבריכה?"

print(f"🔄 Processing PDF: {pdf_name}")
print(f"❓ Question: {question}\n")

answer = processor.process_pdf_and_answer(pdf_name, question, system_prompt)

print(f"\n🤖 Answer: {answer}")
```

**Run Test:**
```bash
python test_pdf.py
```

**Expected Output:**
```
🔄 Processing PDF: pool.pdf
🔄 Processing and embedding PDF: pool.pdf...
📄 Split into 5 chunks (2000 chars each)
🔄 Generating embeddings using local method...
✅ Generated 5 embeddings (768 dimensions each)
💾 Embeddings saved to: embeddings/pool_embeddings.pkl
❓ Question: מה שעות הפתיחה של הבריכה?

🤖 Answer: שעות הפתיחה של הבריכה הם ראשון-חמישי: 06:00-22:00, שישי: 08:00-16:00.
```

---

### Step 8: Regenerate All Embeddings (5 minutes)

**Option A: Via Admin Panel (Recommended)**

1. Start the app: `streamlit run main.py`
2. Visit each dialog in the public app:
   - http://localhost:8501/ → Click "בריכה"
   - http://localhost:8501/ → Click "אירועים והופעות"
   - http://localhost:8501/ → Click "מידע כללי"
   - http://localhost:8501/ → Click "אינדקס עסקים"
3. Embeddings will regenerate automatically on first visit

**Option B: Command Line Script**

```python
from utils.PdfQAProcessor import PdfQAProcessor

processor = PdfQAProcessor()
pdfs = ["pool.pdf", "events.pdf", "general_info.pdf", "business_index.pdf"]
system_prompt = "אתה עוזר חכם."

for pdf in pdfs:
    print(f"\n🔄 Processing: {pdf}")
    try:
        answer = processor.process_pdf_and_answer(pdf, "בדיקה", system_prompt)
        print(f"✅ {pdf} embedded successfully!")
    except Exception as e:
        print(f"❌ Error with {pdf}: {e}")

print("\n✅ All PDFs processed!")
```

**Verify Embeddings Created:**
```bash
dir embeddings\*.pkl

# Expected output:
# pool_embeddings.pkl
# events_embeddings.pkl
# general_info_embeddings.pkl
# business_index_embeddings.pkl
```

---

## ✅ Verification Checklist

After migration, verify:

- [ ] **Embeddings Created**: All 4 `.pkl` files exist in `embeddings/` folder
- [ ] **Model Loaded**: Console shows "✅ MPA/sambert model loaded successfully!"
- [ ] **Correct Dimensions**: Embeddings are 768-dim (not 1536)
- [ ] **Chat Works**: Public app chat returns answers
- [ ] **Hebrew Quality**: Answers are relevant and accurate
- [ ] **No Errors**: No API errors or crashes
- [ ] **Performance**: Response time <500ms for embeddings

**Quick Verification Script:**
```python
import os
import pickle

embeddings_folder = "embeddings"
pkl_files = [f for f in os.listdir(embeddings_folder) if f.endswith('.pkl')]

print(f"📊 Found {len(pkl_files)} embedding files:")
for file in pkl_files:
    path = os.path.join(embeddings_folder, file)
    with open(path, 'rb') as f:
        embeddings, chunks = pickle.load(f)
    print(f"✅ {file}: {len(embeddings)} embeddings x {len(embeddings[0])} dims")

# Expected: 768 dims for all files
```

---

## 🐛 Troubleshooting

### Issue 1: Model Download Fails

**Error:**
```
❌ Error loading local model: HTTP Error 403
```

**Solution:**
```python
# Try with explicit trust_remote_code
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('MPA/sambert', trust_remote_code=True)
```

---

### Issue 2: Out of Memory

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
Use CPU instead (slower but works):
```python
# In PdfQAProcessor_new.py, modify:
self.embedding_model = SentenceTransformer('MPA/sambert', device='cpu')
```

---

### Issue 3: Slow Embedding Generation

**Symptoms:**
- Embeddings take >5 seconds each

**Solutions:**

**A. Use GPU (if available):**
```bash
# Check GPU
python -c "import torch; print(torch.cuda.is_available())"

# If True, model will auto-use GPU
```

**B. Use Hugging Face API instead:**
```env
# In .env file
EMBEDDING_METHOD="huggingface"
HUGGINGFACE_API_KEY="hf_xxxxx"
```

---

### Issue 4: Wrong Embedding Dimensions

**Error:**
```
AssertionError: shapes (1536,) and (768,) not aligned
```

**Cause:** Old embeddings (1536-dim) mixed with new embeddings (768-dim)

**Solution:**
```bash
# Delete ALL old embeddings
del embeddings\*.pkl
# Then restart app to regenerate
```

---

### Issue 5: Hebrew Text Garbled

**Symptoms:**
- Hebrew appears as "??????"

**Solution:**
```python
# Ensure UTF-8 encoding when reading PDFs
# Already handled in PdfQAProcessor_new.py
```

---

## 🔄 Rollback Procedure

If you need to revert to OpenAI embeddings:

### Step 1: Restore Original File

```bash
# Windows
copy utils\PdfQAProcessor_OLD.py utils\PdfQAProcessor.py

# Linux/Mac
cp utils/PdfQAProcessor_OLD.py utils/PdfQAProcessor.py
```

### Step 2: Restore .env

```bash
copy .env.backup .env
```

### Step 3: Restore Old Embeddings

```bash
# Delete new embeddings
del embeddings\*.pkl

# Restore old embeddings
copy embeddings_backup\*.pkl embeddings\
```

### Step 4: Restart App

```bash
streamlit run main.py
```

**Verification:**
- Chat should work with OpenAI embeddings again

---

## 📊 Performance Comparison

### Before (OpenAI):
- **Embedding Time**: ~100-300ms per query (network latency)
- **First Load**: Instant (no model download)
- **Memory Usage**: Minimal
- **Cost**: ~$0.0004/month

### After (MPA/sambert Local):
- **Embedding Time**: ~50-150ms per query (local, no network)
- **First Load**: ~3 minutes (model download, one-time)
- **Memory Usage**: ~2GB RAM
- **Cost**: **$0** (free!)

### After (MPA/sambert HF API):
- **Embedding Time**: ~200-500ms per query (network + cold start)
- **First Load**: Instant
- **Memory Usage**: Minimal
- **Cost**: Free tier available

---

## 🎯 Success Metrics

**Migration is successful if:**

- ✅ All 4 PDF embeddings regenerated (768-dim)
- ✅ Chat returns relevant answers to Hebrew queries
- ✅ No errors in console or logs
- ✅ Response time <500ms for embeddings
- ✅ Hebrew text displays correctly
- ✅ Answer quality equal or better than before

**To Measure Quality:**

Test these questions manually:

| PDF | Question | Expected Answer Includes |
|-----|----------|-------------------------|
| pool.pdf | "מה שעות הפתיחה?" | "06:00-22:00" or hours |
| events.pdf | "מתי האירוע הבא?" | Date/time or event info |
| general_info.pdf | "מה המספר טלפון?" | Phone number |
| business_index.pdf | "איפה העסק?" | Address or location |

---

## 📝 Post-Migration Tasks

After successful migration:

1. **Delete Backup Files** (optional):
   ```bash
   rmdir /s embeddings_backup
   del .env.backup
   ```

2. **Update Documentation**:
   - Update README.md with new embedding info
   - Update CLAUDE.md if needed

3. **Monitor Performance**:
   - Track response times for 1 week
   - Collect user feedback on answer quality

4. **Optimize** (optional):
   - If slow, consider GPU installation
   - If quality issues, adjust chunking strategy

---

## 💡 Tips & Best Practices

### For Better Performance:

1. **Use GPU if available**:
   ```bash
   # Check GPU
   nvidia-smi  # Windows/Linux
   ```

2. **Increase chunk overlap** (optional):
   ```python
   # In process_pdf_and_answer(), modify:
   chunk_size = 2000
   overlap = 200
   chunks = [
       pdf_text[i:i+chunk_size]
       for i in range(0, len(pdf_text), chunk_size-overlap)
   ]
   ```

3. **Cache model in Docker** (if using Docker):
   ```dockerfile
   # Pre-download model in Dockerfile
   RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('MPA/sambert')"
   ```

### For Better Quality:

1. **Test with real user queries**:
   - Ask actual users to test
   - Compare with OpenAI responses

2. **Monitor similarity scores**:
   ```python
   # Add logging in get_top_relevant_chunks()
   print(f"Top similarity: {max(similarities):.3f}")
   ```
   - Good: >0.5
   - Okay: 0.3-0.5
   - Poor: <0.3

3. **Adjust top_n if needed**:
   ```python
   # In process_pdf_and_answer(), try:
   relevant_chunk = self.get_top_relevant_chunks(question, embeddings, chunks, top_n=5)  # Was 3
   ```

---

## 📞 Support

**If you encounter issues:**

1. Check this guide's Troubleshooting section
2. Review [EMBEDDING_MIGRATION_ANALYSIS.md](EMBEDDING_MIGRATION_ANALYSIS.md)
3. Contact: sagi.baron76@gmail.com
4. WhatsApp: +972-54-999-5050

**Include in your report:**
- Error message (full text)
- Console output
- Which step you're on
- Python version: `python --version`
- Installed packages: `pip list`

---

## ✅ Migration Complete!

Congratulations! You've successfully migrated to MPA/sambert embeddings.

**Benefits You Now Have:**
- ✅ Hebrew-optimized embeddings
- ✅ Better accuracy for Hebrew queries
- ✅ Free embedding generation (no API costs)
- ✅ Faster local inference (no network latency)
- ✅ Smaller embedding files (50% reduction)

**Next Steps:**
- Monitor performance for 1 week
- Collect user feedback
- Consider Phase 5 features (content editor, analytics)

---

**End of Migration Guide**

*Last Updated: November 3, 2025*
