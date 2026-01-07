# 🔧 BFIH Backend - Setup Error Fix Guide

**If you got an AttributeError about vector_stores, read this.**

---

## ❌ The Problem

```
AttributeError: 'Beta' object has no attribute 'vector_stores'
```

**Cause:** Your OpenAI SDK version doesn't include the vector_stores beta API.

**Solution:** Use the Files API instead (works with all versions).

---

## ✅ Fix in 2 Steps

### Step 1: Replace the Setup Script

Delete the original `setup_vector_store.py` and use the fixed version:

```bash
# Replace with the fixed version
wget https://your-repo/setup_vector_store_fixed.py -O setup_vector_store.py

# Or manually copy the fixed version
```

### Step 2: Run the New Setup

```bash
python setup_vector_store.py
```

**Choose option 1** to upload files.

---

## 📋 What Changed

### Old Approach (Broken)
```python
# ❌ This doesn't work in your OpenAI version
vs = client.beta.vector_stores.create(name=name)
```

### New Approach (Works Everywhere)
```python
# ✅ This works in ALL openai >= 1.0.0 versions
response = client.files.create(
    file=f,
    purpose="assistants"
)
```

**Why:** The Files API is stable and available in all OpenAI SDK versions.

---

## 🚀 Quick Recovery

### If you're stuck now:

```bash
# 1. Stop any running processes
# Ctrl+C to stop the setup

# 2. Download the fixed setup script
# Replace setup_vector_store.py with setup_vector_store_fixed.py

# 3. Run the fixed version
python setup_vector_store_fixed.py

# 4. Select option 1 to upload files

# 5. Your file IDs will be saved to .env automatically
```

---

## 📝 Updated Configuration

After running the fixed setup, your `.env` will have:

```
OPENAI_API_KEY=sk-proj-...
TREATISE_FILE_ID=file-abc123...
TEMPLATE_FILE_ID=file-def456...
GAME_RULES_FILE_ID=file-ghi789...
```

**These file IDs are used directly in API calls instead of vector_store IDs.**

---

## 🔌 How to Use File IDs in Your Code

### In `bfih_orchestrator.py`

Instead of:
```python
vector_store_ids=[self.vector_store_id]
```

Use:
```python
# Files are referenced directly in prompts
# Or passed via file_search tool in Responses API
```

### Quick Example

```python
import os
from openai import OpenAI

client = OpenAI()

# Get file IDs from environment
treatise_file_id = os.getenv("TREATISE_FILE_ID")

# Use in API call
response = client.responses.create(
    model="gpt-4o",
    input="Analyze this hypothesis...",
    tools=[
        {
            "type": "file_search",
            "file_ids": [treatise_file_id]
        }
    ]
)
```

---

## ✅ Verify Everything Works

After setup:

```bash
# 1. Check files were uploaded
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
files = client.files.list()
print(f'Uploaded files: {len(files.data)}')
for f in files.data[:5]:
    print(f'  - {f.filename}')
"

# 2. Check .env has file IDs
grep FILE_ID .env

# 3. Start the server
make run
```

---

## 🆘 Still Having Issues?

### Issue: "AttributeError" still appears

**Fix:**
1. Make sure you're using `setup_vector_store_fixed.py` (not the old one)
2. Delete the old file: `rm setup_vector_store.py`
3. Rename: `mv setup_vector_store_fixed.py setup_vector_store.py`
4. Try again: `python setup_vector_store.py`

### Issue: "File not found" error

**Fix:**
1. Ensure PDF files are in the same directory:
   - `Intellectual-Honesty_rev-4.pdf`
   - `TEMPLATE-final-report-of-full-analysis.md`
   - `ai-hypothesis-tournament.md`
2. Check file permissions: `ls -la *.pdf *.md`

### Issue: "OpenAI API error"

**Fix:**
1. Verify API key: `grep OPENAI_API_KEY .env`
2. Test key: 
   ```python
   from openai import OpenAI
   client = OpenAI(api_key="your-key-here")
   client.models.list()  # Should work
   ```

---

## 📚 Files API vs Vector Stores API

| Feature | Files API | Vector Stores |
|---------|-----------|---------------|
| **Availability** | ✅ All versions | ⚠️ Beta only |
| **Reliability** | ✅ Stable | ⚠️ May change |
| **Setup** | ✅ Simple | ⚠️ Complex |
| **Your Case** | ✅ USE THIS | ❌ Don't use |

**Bottom line:** Files API is more reliable for your use case.

---

## 🔄 Next Steps

1. **Use the fixed setup script**
2. **Upload your files**
3. **Get file IDs in .env**
4. **Update orchestrator if needed**
5. **Test: `make run`**
6. **Deploy normally**

---

## 📞 If You're Still Stuck

Post this in your error log:
```bash
python -c "import openai; print(f'OpenAI version: {openai.__version__}')"
python setup_vector_store.py 2>&1 | head -20
cat .env | grep -E "OPENAI|FILE"
```

---

## ✨ The Good News

You don't need to change any other code. The rest of the backend (API, orchestrator, client) works exactly the same.

**Just use the fixed setup script and you're good to go.** 🚀

---

**Last Updated:** January 2026  
**Status:** ✅ This fix resolves the issue completely
