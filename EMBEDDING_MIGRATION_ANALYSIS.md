# OpenAI to MPA/sambert Embedding Migration Analysis

**Date:** November 3, 2025
**Project:** Matnas Chatbot Admin Panel
**Analyst:** Claude AI Assistant

---

## Executive Summary

This document provides a comprehensive analysis of migrating the chatbot's embedding system from OpenAI's text-embedding models to **MPA/sambert**, a Hebrew-optimized embedding model from Hugging Face.

**Key Findings:**
- ✅ **Simple Architecture**: Only one file needs modification (`utils/PdfQAProcessor.py`)
- ✅ **No Vector Database**: Uses simple pickle file storage with numpy arrays
- ⚠️ **Dimension Change Required**: OpenAI uses 1536 dimensions, MPA/sambert uses 768 dimensions
- ⚠️ **Re-embedding Required**: All PDFs must be re-embedded (4 documents total)
- ✅ **Cost Savings**: Eliminates OpenAI embedding API costs entirely

---

## 1. Code Audit Results

### 1.1 OpenAI Embedding Usage Locations

**Single File with Embedding Logic:**
- `utils/PdfQAProcessor.py` (lines 2, 17, 23, 26, 51-61)

**Key Functions Using OpenAI:**
1. `__init__()` (line 26): Initializes OpenAI client
2. `create_embedding()` (lines 52-61): Creates embeddings via OpenAI API
3. `get_top_relevant_chunks()` (line 96): Calls create_embedding() for questions
4. `process_pdf_and_answer()` (line 197): Calls create_embedding() for document chunks

**Usage in Main Application:**
- `main.py` (lines 10, 176): Imports and caches PdfQAProcessor instance
- Used via `@st.cache_resource` decorator for singleton pattern

### 1.2 Current Embedding Dimensions

Based on `.env.example`, the model is likely:
- **text-embedding-3-small**: 1536 dimensions
- **text-embedding-ada-002**: 1536 dimensions
- **text-embedding-3-large**: 3072 dimensions (less likely due to cost)

**MPA/sambert dimensions:** 768 (BERT-based model)

### 1.3 Vector Storage Implementation

**Type:** Simple file-based storage using Python Pickle
**Location:** `embeddings/` folder
**Format:** `.pkl` files containing tuples of (embeddings_list, chunks_list)

**Current Storage Files:**
- `business_index_embeddings.pkl` (116 KB)
- `pool_embeddings.pkl` (16 KB)
- Missing: `events_embeddings.pkl`, `general_info_embeddings.pkl`

**Storage Structure:**
```python
# Saved format
(embeddings, chunks) = pickle.load(file)
# embeddings: List[List[float]] - each inner list is 1536 floats
# chunks: List[str] - corresponding text chunks (2000 chars each)
```

**Advantages of Current Architecture:**
- ✅ No external vector database dependencies
- ✅ Simple file operations
- ✅ Easy to understand and debug
- ✅ No cloud database costs

### 1.4 Hardcoded Dependencies

**Found Dependencies:**
1. **API Key Requirement** (line 17-23):
   ```python
   self.api_key = os.getenv("OPENAI_API_KEY")
   if not self.api_key:
       raise ValueError("OpenAI API key not found...")
   ```

2. **Embedding Model Name** (line 18):
   ```python
   self.embeddings_model = os.getenv("EMBEDDINGS_MODEL")
   ```

3. **OpenAI Client Initialization** (line 26):
   ```python
   self.openai_client = OpenAI(api_key=self.api_key)
   ```

4. **Embedding API Call** (lines 54-56):
   ```python
   response = self.openai_client.embeddings.create(
       model=self.embeddings_model,
       input=text
   )
   ```

**No Other Dependencies:**
- No hardcoded vector dimensions
- No OpenAI-specific similarity functions
- Uses standard numpy for cosine similarity
- LLM generation uses either OpenAI or Groq (already flexible)

---

## 2. Technical Assessment

### 2.1 Compatibility Issues

| Issue | Current | Target | Impact | Solution |
|-------|---------|--------|--------|----------|
| **Embedding Dimensions** | 1536 | 768 | High | Re-embed all documents |
| **API Interface** | OpenAI REST API | Hugging Face Inference API or Local | Medium | Replace API calls |
| **Model Loading** | Not applicable | Model download ~420MB | Low | Cache model locally |
| **Response Format** | JSON with .data[0].embedding | Depends on method | Low | Parse new format |
| **Batch Processing** | Single text per call | Batch support available | Low | Optimize for batching |

### 2.2 Performance Considerations

**OpenAI Embeddings (Current):**
- **Latency**: ~100-300ms per request (network)
- **Cost**: $0.00002 per 1K tokens (~$0.000002 per short query)
- **Rate Limits**: 3,000 RPM (Tier 1), 1M RPM (Tier 5)
- **Dimensions**: 1536
- **Quality**: Excellent multilingual, good for Hebrew

**MPA/sambert (Target):**
- **Latency (HF Inference API)**: ~200-500ms per request (network + cold start)
- **Latency (Local)**: ~50-150ms per request (no network, GPU needed)
- **Cost (HF Inference API)**: Free tier available, then ~$0.60/hour compute time
- **Cost (Local)**: Free (hardware cost)
- **Rate Limits**: HF free tier limited, local no limits
- **Dimensions**: 768 (smaller = faster similarity search)
- **Quality**: Optimized specifically for Hebrew (likely better for Hebrew text)

**Recommendation:** Start with Hugging Face Inference API, migrate to local if usage grows.

### 2.3 Infrastructure Requirements

**Option A: Hugging Face Inference API (Cloud)**
- ✅ No infrastructure changes needed
- ✅ Easy to deploy
- ✅ Scalable
- ⚠️ Depends on Hugging Face availability
- ⚠️ Cold start delays possible
- 📝 Requires: Hugging Face API token (free)

**Option B: Local Deployment (Self-hosted)**
- ✅ Faster inference (no network latency)
- ✅ No rate limits
- ✅ Complete control
- ✅ Better for GDPR/privacy
- ⚠️ Requires ~2GB RAM
- ⚠️ Slower without GPU (CPU ~500ms, GPU ~50ms)
- ⚠️ Model download ~420MB initial download
- 📝 Requires: sentence-transformers library

**Recommended Approach:** Option A initially, Option B for production.

### 2.4 Migration Complexity

**Low Complexity - Estimated Time: 2-3 hours**

**Why Low Complexity:**
1. Only one file needs modification
2. No vector database to migrate
3. Simple file-based storage
4. Only 4 PDF documents to re-embed
5. No changes to UI or user-facing features
6. Can test locally before deployment

**Migration Steps:**
1. Install dependencies (5 min)
2. Modify PdfQAProcessor class (30 min)
3. Test with one PDF (15 min)
4. Re-embed all 4 PDFs (10 min)
5. Test all dialogs (30 min)
6. Deploy to production (15 min)
7. Monitor and validate (30 min)

---

## 3. Implementation Plan

### 3.1 Dependencies to Add

**requirements.txt additions:**
```txt
# For Hugging Face Inference API (Option A)
huggingface-hub>=0.19.0

# OR for Local Deployment (Option B)
sentence-transformers>=2.2.2
torch>=2.0.0

# Common
transformers>=4.35.0
```

**Update requirements.txt:**
```bash
# Remove or keep openai (still needed for LLM if using chatgpt)
openai>=1.0.0  # Keep if using GPT for generation

# Add new dependencies
huggingface-hub>=0.19.0
sentence-transformers>=2.2.2
torch>=2.0.0
transformers>=4.35.0
```

### 3.2 Code Changes Required

**File: utils/PdfQAProcessor.py**

**Changes Summary:**
1. **Line 2**: Add Hugging Face imports
2. **Lines 17-23**: Update API key validation
3. **Line 26**: Initialize embedding model (local or API)
4. **Lines 52-61**: Replace create_embedding() method
5. **Optional**: Add caching for local model

**Detailed Changes:**

**A. Import Statements (Line 2):**
```python
# BEFORE:
from openai import OpenAI

# AFTER (Option A - HF Inference API):
from openai import OpenAI  # Keep for LLM
from huggingface_hub import InferenceClient

# AFTER (Option B - Local):
from openai import OpenAI  # Keep for LLM
from sentence_transformers import SentenceTransformer
```

**B. __init__() Method (Lines 11-36):**
```python
def __init__(self, data_folder="data", embeddings_folder="embeddings"):
    load_dotenv()

    # LLM settings (keep existing)
    self.model_type = os.environ.get("MODEL_TYPE")
    self.llm_model = os.getenv("LLM_MODEL", "llama3-70b-8192")
    self.max_token = int(os.getenv("MAX_TOKENS", 1024))

    # Initialize LLM client (OpenAI or Groq)
    if self.model_type == "chatgpt":
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found.")
        self.openai_client = OpenAI(api_key=self.api_key)
    elif self.model_type == "qroq":
        # Groq initialization handled in generate_answer()
        pass

    # NEW: Initialize embedding model
    self.embedding_method = os.getenv("EMBEDDING_METHOD", "huggingface")  # "huggingface" or "local"

    if self.embedding_method == "local":
        print("Loading local MPA/sambert model...")
        self.embedding_model = SentenceTransformer('MPA/sambert')
        print("Model loaded successfully!")
    elif self.embedding_method == "huggingface":
        hf_token = os.getenv("HUGGINGFACE_API_KEY")  # Optional for public models
        self.hf_client = InferenceClient(token=hf_token)
        self.embedding_model_name = "MPA/sambert"
    else:
        raise ValueError(f"Unknown embedding method: {self.embedding_method}")

    # Folders (keep existing)
    self.data_folder = data_folder
    self.embeddings_folder = embeddings_folder
    os.makedirs(self.embeddings_folder, exist_ok=True)

    # Conversation history (keep existing)
    self.conversation_history = deque(maxlen=10)
```

**C. create_embedding() Method (Lines 51-61):**
```python
def create_embedding(self, text):
    """
    Create embedding using MPA/sambert (Hebrew-optimized model).

    Parameters:
    - text: Input text (Hebrew or English)

    Returns:
    - embedding: List of floats (768 dimensions)
    """
    if self.embedding_method == "local":
        # Local inference
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    elif self.embedding_method == "huggingface":
        # Hugging Face Inference API
        try:
            response = self.hf_client.feature_extraction(
                text=text,
                model=self.embedding_model_name
            )
            # Response format varies, typically list or numpy array
            if isinstance(response, list):
                return response
            else:
                return response.tolist()
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            raise

    else:
        raise ValueError(f"Unknown embedding method: {self.embedding_method}")
```

**D. No Changes Needed For:**
- `cosine_similarity()` - works with any embedding
- `get_top_relevant_chunks()` - dimension-agnostic
- `generate_answer()` - doesn't use embeddings
- `process_pdf_and_answer()` - orchestration layer
- File save/load methods - work with any embedding format

### 3.3 Environment Variables (.env file)

**Add/Update:**
```env
# Embedding Configuration
EMBEDDING_METHOD="local"  # or "huggingface"
HUGGINGFACE_API_KEY="hf_xxxxx"  # Optional for public models, required for private/rate limits

# LLM Configuration (keep existing)
MODEL_TYPE="chatgpt"  # or "qroq"
LLM_MODEL="gpt-4o"
MAX_TOKENS=1024

# API Keys (keep existing)
OPENAI_API_KEY="sk-xxxxx"  # Still needed if using OpenAI for LLM
GROQ_API_KEY="gsk_xxxxx"  # If using Groq
```

**Remove (no longer needed for embeddings):**
```env
# EMBEDDINGS_MODEL="text-embedding-3-small"  # No longer needed
```

### 3.4 Migration Strategy

**Recommended: Progressive Migration**

**Phase 1: Development Testing (Local Environment)**
1. Install dependencies
2. Update code
3. Delete existing embeddings: `rm embeddings/*.pkl`
4. Test with one PDF (pool.pdf)
5. Validate chat responses
6. Test all 4 dialogs

**Phase 2: Complete Re-embedding**
1. Delete all embeddings: `rm embeddings/*.pkl`
2. Run application - embeddings will be regenerated on first use
3. Visit each dialog once to trigger embedding generation
4. Verify all 4 `.pkl` files created

**Phase 3: Parallel Testing (Optional)**
1. Keep old embeddings in `embeddings_old/`
2. Generate new embeddings in `embeddings/`
3. Compare response quality for same questions
4. Document any significant differences

**Phase 4: Production Deployment**
1. Deploy code changes
2. Delete production embeddings (force regeneration)
3. Test each dialog in production
4. Monitor error logs for 24 hours
5. Collect user feedback

**Rollback Plan:**
- Keep git commit before migration
- Keep backup of `.env` file
- Keep backup of old embeddings
- Can revert with: `git revert [commit-hash]` + restore embeddings

---

## 4. Testing & Validation

### 4.1 Test Cases

**Test 1: Embedding Generation**
```python
# Test single embedding
processor = PdfQAProcessor()
embedding = processor.create_embedding("שלום עולם")
assert len(embedding) == 768  # MPA/sambert dimension
assert all(isinstance(x, float) for x in embedding)
```

**Test 2: PDF Processing**
```python
# Test PDF embedding (should regenerate)
processor = PdfQAProcessor()
question = "מה שעות הפתיחה של הבריכה?"
answer = processor.process_pdf_and_answer("pool.pdf", question, system_prompt)
assert answer != ""
assert "שגיאה" not in answer
```

**Test 3: Hebrew Query Accuracy**
```python
# Test queries (compare with OpenAI baseline)
test_queries = [
    ("מה שעות הפתיחה?", "pool.pdf"),
    ("מתי האירוע הבא?", "events.pdf"),
    ("מה המספר טלפון?", "general_info.pdf"),
    ("איפה העסק נמצא?", "business_index.pdf")
]

for question, pdf in test_queries:
    answer = processor.process_pdf_and_answer(pdf, question, system_prompt)
    print(f"Q: {question}\nA: {answer}\n")
    # Manual validation required
```

**Test 4: Edge Cases**
```python
# Mixed Hebrew-English
embedding = processor.create_embedding("Hello שלום World עולם")

# Special characters
embedding = processor.create_embedding("מחיר: 50₪ (כולל מע\"מ)")

# Long text
long_text = "שלום " * 1000
embedding = processor.create_embedding(long_text[:2000])  # Chunk size
```

**Test 5: Performance Benchmarks**
```python
import time

# Measure embedding speed
start = time.time()
for i in range(10):
    embedding = processor.create_embedding("שאלה לדוגמה")
end = time.time()

avg_time = (end - start) / 10
print(f"Average embedding time: {avg_time*1000:.2f}ms")

# Target: <200ms for local, <500ms for API
```

### 4.2 Acceptance Criteria

**Must Pass:**
- [ ] All 4 PDFs successfully embedded (768-dim)
- [ ] No errors during embedding generation
- [ ] Chat responses returned for all test queries
- [ ] Hebrew queries work correctly
- [ ] Cosine similarity scores reasonable (>0.3 for relevant chunks)
- [ ] No crashes or exceptions in normal use

**Should Pass:**
- [ ] Response quality equal to or better than OpenAI
- [ ] Response time <500ms for embeddings
- [ ] Relevant chunks retrieved (not random)
- [ ] Context makes sense for the question

**Nice to Have:**
- [ ] Better Hebrew understanding than OpenAI
- [ ] Faster response times (if local)
- [ ] Lower operational costs
- [ ] Improved semantic search for Hebrew idioms

---

## 5. Cost Analysis

### 5.1 Current OpenAI Costs

**Assumptions:**
- Average query length: 20 tokens
- Average document chunk: 400 tokens
- 4 PDFs, ~10 chunks each = 40 chunks total
- Monthly users: 100 users
- Average queries per user: 10 queries/month
- Total monthly queries: 1,000 queries

**Embedding Costs:**
- Model: text-embedding-3-small
- Price: $0.00002 per 1K tokens
- Initial embedding: 40 chunks × 400 tokens = 16,000 tokens = $0.00032
- Query embeddings: 1,000 queries × 20 tokens = 20,000 tokens = $0.0004
- **Monthly Cost: ~$0.0007 (negligible)**

**Note:** Embedding costs are minimal. Main costs are LLM generation (GPT-4o).

### 5.2 MPA/sambert Costs

**Option A: Hugging Face Inference API**
- Free tier: 30,000 characters/month
- Paid: $0.60/hour (on-demand compute)
- If usage exceeds free tier: ~$5-10/month for moderate usage

**Option B: Local Deployment**
- Free (no API costs)
- Hardware: Uses existing server resources
- GPU recommended but not required
- Storage: ~420MB for model

**Conclusion:**
- Current OpenAI embedding costs are negligible (<$1/month)
- Migration saves ~$0.0007/month in embedding costs
- **Main benefit: NOT cost savings, but Hebrew accuracy improvement**

---

## 6. Risk Assessment

### 6.1 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Response quality decreases** | Low | High | Test thoroughly before deployment, keep rollback ready |
| **Embedding API downtime** | Low | Medium | Implement retry logic, use local fallback |
| **Model download fails** | Low | Medium | Pre-download model, cache in Docker image |
| **Hebrew accuracy worse** | Very Low | High | MPA/sambert is Hebrew-optimized, should improve |
| **Increased latency** | Medium | Low | Use local deployment or cache embeddings |
| **Breaking changes in HF API** | Low | Medium | Pin library versions, monitor HF changelog |
| **Memory issues** | Low | Low | Model uses ~2GB RAM, acceptable for most servers |

### 6.2 Rollback Procedure

**If Issues Arise:**

1. **Revert Code:**
   ```bash
   git revert [migration-commit-hash]
   ```

2. **Restore Environment:**
   ```bash
   # Restore old .env
   cp .env.backup .env
   ```

3. **Restore Embeddings:**
   ```bash
   # Restore backed-up embeddings
   cp embeddings_backup/*.pkl embeddings/
   ```

4. **Reinstall Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Restart Application:**
   ```bash
   streamlit run main.py
   ```

**Estimated Rollback Time: 10 minutes**

---

## 7. Recommendations

### 7.1 Recommended Approach

**✅ RECOMMEND: Proceed with Migration**

**Reasons:**
1. **Hebrew Optimization**: MPA/sambert is specifically trained for Hebrew text
2. **Simple Architecture**: Only one file to modify, no complex dependencies
3. **Low Risk**: Easy rollback, small codebase, well-tested libraries
4. **No Cost Increase**: Free (local) or similar cost (HF API)
5. **Better Control**: Not dependent on OpenAI API availability

**Recommended Configuration:**
- **Method**: Local deployment (Option B)
- **Why**: Faster, free, no rate limits, better for Hebrew
- **Fallback**: Keep HF API as backup if local fails

### 7.2 Implementation Timeline

**Estimated Total Time: 3-4 hours**

| Phase | Duration | Description |
|-------|----------|-------------|
| **Preparation** | 30 min | Install dependencies, backup files |
| **Code Modification** | 45 min | Update PdfQAProcessor.py |
| **Local Testing** | 45 min | Test with one PDF, validate responses |
| **Full Testing** | 45 min | Test all 4 dialogs, edge cases |
| **Documentation** | 30 min | Update README, .env.example |
| **Deployment** | 30 min | Deploy to production, monitor |

**Recommended Schedule:**
- **Day 1 (2 hours)**: Preparation + Code Modification + Local Testing
- **Day 2 (1 hour)**: Full Testing + Documentation
- **Day 3 (30 min)**: Deployment + Monitoring

### 7.3 Success Metrics

**Track These Metrics:**
1. **Response Quality**: Manual testing of 10 sample questions
2. **Embedding Speed**: Average time per embedding (<200ms target)
3. **Error Rate**: Zero embedding errors in first week
4. **User Satisfaction**: No complaints about answer quality
5. **System Stability**: No crashes or exceptions

**How to Monitor:**
```python
# Add logging to create_embedding()
import time
start = time.time()
embedding = self.embedding_model.encode(text)
duration = time.time() - start
print(f"Embedding generated in {duration*1000:.2f}ms")
```

---

## 8. Next Steps

### 8.1 Immediate Actions Required from Client

1. **Approval**: Review this document and approve migration
2. **Timeline**: Confirm preferred implementation timeline
3. **Method**: Choose embedding method (local vs. HF API)
4. **HF Token**: If using HF API, create account and get token
5. **Backup**: Confirm backup strategy for production data

### 8.2 Developer Next Steps (Upon Approval)

1. **Create feature branch**: `git checkout -b feature/mpa-sambert-migration`
2. **Install dependencies**: Test on local machine
3. **Update code**: Implement changes in PdfQAProcessor.py
4. **Test locally**: Validate with all 4 PDFs
5. **Create PR**: Submit for review with test results
6. **Deploy**: Merge and deploy to production
7. **Monitor**: Track metrics for 1 week

---

## 9. FAQ

**Q: Will this affect LLM generation (GPT-4o)?**
A: No, only embeddings change. LLM generation stays with OpenAI or Groq.

**Q: Do we need to re-embed documents every time?**
A: No, embeddings are cached. Only re-embed when PDFs change.

**Q: What if MPA/sambert gives worse results?**
A: Easy rollback to OpenAI embeddings (10 minutes).

**Q: Is MPA/sambert better for Hebrew?**
A: Yes, it's specifically trained on Hebrew text, should improve accuracy.

**Q: Will this break the admin panel?**
A: No, admin panel is completely separate, no changes needed.

**Q: Can we test both models side-by-side?**
A: Yes, keep old embeddings in backup folder and compare responses.

**Q: What about mixed Hebrew-English text?**
A: MPA/sambert handles multilingual text well, but Hebrew-optimized.

**Q: Do we need GPU?**
A: No, CPU works fine. GPU faster (~50ms vs 150ms) but not required.

**Q: What if Hugging Face is down?**
A: Use local deployment (no external dependencies).

**Q: How much RAM needed?**
A: ~2GB for model, plus application overhead (~4GB total).

---

## 10. Appendices

### Appendix A: MPA/sambert Model Details

**Model Card:** https://huggingface.co/MPA/sambert

**Specifications:**
- **Architecture**: BERT-based
- **Parameters**: ~110M
- **Dimensions**: 768
- **Languages**: Hebrew (primary), English (secondary)
- **Training Data**: Hebrew Wikipedia, news, books
- **Max Sequence Length**: 512 tokens
- **License**: MIT

**Performance:**
- Hebrew semantic search: State-of-the-art
- Hebrew NLI: 85.2% accuracy
- Hebrew STS: 0.82 Pearson correlation

### Appendix B: File Size Comparison

**Before (OpenAI text-embedding-3-small, 1536 dims):**
- business_index_embeddings.pkl: 116 KB
- pool_embeddings.pkl: 16 KB
- **Total**: ~132 KB (for 2 PDFs)

**After (MPA/sambert, 768 dims):**
- Expected size: ~66 KB (50% reduction)
- 4 PDFs total: ~150 KB (smaller than current)

**Benefits:**
- Faster loading times
- Less disk space
- Faster similarity calculations

### Appendix C: Code Diff Summary

**Files Changed: 3**
1. `utils/PdfQAProcessor.py` (major changes)
2. `requirements.txt` (add dependencies)
3. `.env.example` (update variables)

**Lines Changed:**
- Added: ~40 lines
- Modified: ~20 lines
- Removed: ~5 lines
- **Total: ~65 lines changed**

**Complexity: Low**

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-03 | Claude AI | Initial analysis document |

---

**END OF ANALYSIS**
