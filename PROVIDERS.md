# API Provider Configuration

Flow Guardian uses two external services by default, but **both are configurable**:

1. **LLM (Cerebras)** - For extracting insights and generating summaries
2. **Embeddings (Gemini)** - For semantic vector search

---

## 🔑 Default Setup (Cerebras + Gemini)

### Why These Providers?

- **Cerebras**: Fast inference (1,500+ tokens/sec), generous free tier
- **Gemini**: Free embeddings API, 768-dimensional vectors

### Getting API Keys

#### Cerebras API Key (for LLM inference)

1. Visit: https://cloud.cerebras.ai/
2. Sign up (free tier available)
3. Go to: API Keys → Create new key
4. Copy key (starts with `csk-...`)

**Free Tier:**
- Generous limits for personal use
- Llama 3.3 70B model included

#### Gemini API Key (for embeddings)

1. Visit: https://ai.google.dev/
2. Click "Get API Key" → Create API key
3. Copy key

**Free Tier:**
- 1,500 requests/day
- text-embedding-004 model (768 dimensions)

### Configure in .env

```bash
# Required for default setup
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxx

# Optional
FLOW_GUARDIAN_USER=yourname
```

---

## 🔄 Using Alternative Providers

### Option 1: Different LLM Provider

Flow Guardian uses `cerebras_client.py` for LLM calls. You can modify this to use:

- **OpenAI GPT-4**
- **Anthropic Claude**
- **Local LLaMA via Ollama**
- **Any OpenAI-compatible API**

#### Example: Switch to OpenAI

**1. Update cerebras_client.py:**

```python
# cerebras_client.py
import openai

class CerebrasClient:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def extract_session_info(self, messages: list) -> dict:
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",  # or gpt-3.5-turbo
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
```

**2. Update .env:**

```bash
# Use CEREBRAS_API_KEY variable (code still reads this)
# But actual key is OpenAI key
CEREBRAS_API_KEY=sk-xxxxxxxxxxxxx  # OpenAI key
GEMINI_API_KEY=xxxxxxxxxxxxx
```

**3. Update requirements.txt:**

```bash
# Remove:
cerebras-cloud-sdk>=1.0.0

# Add:
openai>=1.0.0
```

#### Example: Use Local Ollama

**1. Install Ollama:**

```bash
# macOS
brew install ollama

# Start Ollama
ollama serve

# Pull model
ollama pull llama3
```

**2. Update cerebras_client.py:**

```python
import httpx

class CerebrasClient:
    def __init__(self, api_key: str = None):
        self.base_url = "http://localhost:11434"

    def extract_session_info(self, messages: list) -> dict:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": "llama3",
                "messages": messages,
                "stream": False
            }
        )
        return response.json()["message"]["content"]
```

**3. Update .env:**

```bash
# No API key needed for local Ollama
CEREBRAS_API_KEY=none  # Code still checks, set to dummy value
GEMINI_API_KEY=xxxxxxxxxxxxx
```

---

### Option 2: Different Embedding Provider

Flow Guardian uses Gemini for embeddings. You can switch to:

- **OpenAI embeddings** (text-embedding-3-small, text-embedding-3-large)
- **Local embeddings** (sentence-transformers)
- **Cohere embeddings**

#### Example: Switch to OpenAI Embeddings

**1. Update local_memory.py:**

Find the embedding generation code (search for `google.generativeai`):

```python
# Replace Gemini embedding code with:
import openai

def generate_embedding(text: str) -> list[float]:
    client = openai.OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

**2. Update requirements.txt:**

```bash
# Remove:
google-genai>=1.0.0

# Add:
openai>=1.0.0
```

**3. Update .env:**

```bash
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxx
GEMINI_API_KEY=sk-xxxxxxxxxxxxx  # Now OpenAI key

# Optional: Specify embedding dimension
EMBEDDING_DIM=1536  # OpenAI text-embedding-3-small
```

**4. Update SQLite vector table:**

OpenAI embeddings are 1536 dimensions (vs Gemini's 768). Update `local_memory.py`:

```python
# Change vector dimension
db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS memory_embeddings
    USING vec0(
        id TEXT PRIMARY KEY,
        embedding FLOAT[1536]  -- Changed from 768
    )
""")
```

#### Example: Use Local Embeddings (Free, No API)

**1. Install sentence-transformers:**

```bash
pip install sentence-transformers
```

**2. Update local_memory.py:**

```python
from sentence_transformers import SentenceTransformer

class LocalMemoryService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dim

    def generate_embedding(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
```

**3. Update .env:**

```bash
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxx
# No GEMINI_API_KEY needed!

EMBEDDING_DIM=384  # all-MiniLM-L6-v2 dimensions
```

**4. Update vector table:**

```python
db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS memory_embeddings
    USING vec0(
        id TEXT PRIMARY KEY,
        embedding FLOAT[384]  -- Changed from 768
    )
""")
```

---

## 🆓 Fully Free Setup (No API Keys Required)

You can run Flow Guardian with **zero external API costs**:

### LLM: Local Ollama

```bash
# Install Ollama
brew install ollama  # macOS
ollama serve
ollama pull llama3
```

**Update cerebras_client.py** (see example above)

### Embeddings: Local sentence-transformers

```bash
pip install sentence-transformers
```

**Update local_memory.py** (see example above)

### Result

- ✅ No API keys needed
- ✅ No internet dependency (after initial model download)
- ✅ Completely local and private
- ⚠️ Slower inference than cloud APIs
- ⚠️ Requires ~8GB RAM for LLaMA 3

---

## 📊 Provider Comparison

| Provider | Cost | Speed | Quality | Setup |
|----------|------|-------|---------|-------|
| **Cerebras (default)** | Free tier | Very Fast | High | Easy |
| **Gemini (default)** | Free | Fast | High | Easy |
| **OpenAI GPT-4** | $0.01/1K tokens | Fast | Highest | Easy |
| **OpenAI Embeddings** | $0.0001/1K tokens | Fast | High | Easy |
| **Local Ollama** | Free | Medium | Good | Medium |
| **Local Embeddings** | Free | Fast | Good | Easy |

---

## 🔧 Configuration Files to Modify

### For LLM Provider Changes:

1. **cerebras_client.py** - Main LLM client
   - Lines to change: API initialization, model calls
   - Search for: `cerebras_cloud_sdk`, `llama3.3-70b`

2. **requirements.txt** - Dependencies
   - Remove: `cerebras-cloud-sdk`
   - Add: Your provider's SDK

3. **.env** - API keys
   - Keep variable name `CEREBRAS_API_KEY` (code reads this)
   - Put your actual provider's key as the value

### For Embedding Provider Changes:

1. **local_memory.py** - Embedding generation
   - Search for: `google.generativeai`, `text-embedding-004`
   - Replace with your embedding code

2. **requirements.txt** - Dependencies
   - Remove: `google-genai`
   - Add: Your provider's SDK

3. **.env** - API keys and config
   - Keep variable name `GEMINI_API_KEY` (code reads this)
   - Add `EMBEDDING_DIM=XXX` if dimensions change

4. **local_memory.py** - Vector table schema
   - Update: `FLOAT[768]` to match new embedding dimensions

---

## 🚀 Quick Swap Examples

### Swap to OpenAI for Everything

```bash
# 1. Update dependencies
pip uninstall cerebras-cloud-sdk google-genai
pip install openai

# 2. Update .env
CEREBRAS_API_KEY=sk-xxxxxxxxxxxxx  # OpenAI key
GEMINI_API_KEY=sk-xxxxxxxxxxxxx    # Same OpenAI key
EMBEDDING_DIM=1536

# 3. Modify code (see examples above)
# - cerebras_client.py → use openai.OpenAI()
# - local_memory.py → use openai.embeddings.create()
```

### Swap to Fully Local

```bash
# 1. Install tools
brew install ollama
ollama serve
ollama pull llama3
pip install sentence-transformers

# 2. Update .env
CEREBRAS_API_KEY=none  # Dummy value
GEMINI_API_KEY=none    # Not used
EMBEDDING_DIM=384

# 3. Modify code (see examples above)
# - cerebras_client.py → use ollama API
# - local_memory.py → use SentenceTransformer
```

---

## 💡 Tips

1. **Keep variable names**: Even when switching providers, keep `CEREBRAS_API_KEY` and `GEMINI_API_KEY` variable names. The code reads these - just put your new provider's key as the value.

2. **Match embedding dimensions**: If you change embedding providers, update:
   - Vector table schema in `local_memory.py`
   - `EMBEDDING_DIM` in `.env`

3. **Test after changes**: After swapping providers, test:
   ```bash
   # Test LLM
   python -c "from cerebras_client import CerebrasClient; print('LLM OK')"

   # Test embeddings
   python -c "from local_memory import LocalMemoryService; print('Embeddings OK')"
   ```

4. **Backup memory.db**: Before changing embedding dimensions, backup your database:
   ```bash
   cp ~/.flow-guardian/memory.db ~/.flow-guardian/memory.db.backup
   ```

---

## 🆘 Troubleshooting Provider Changes

### "Import error after changing provider"

**Fix:** Make sure you updated `requirements.txt` and ran:
```bash
pip install -r requirements.txt
```

### "Embedding dimensions don't match"

**Fix:** You need to recreate the vector table:
```bash
rm ~/.flow-guardian/memory.db
python server.py all --foreground  # Recreates with new dimensions
```

### "LLM responses are slow/low quality"

**Fix:** Different models have different performance:
- Cerebras: Very fast, good quality
- GPT-4: Slower, highest quality
- Local Ollama: Medium speed, good quality
- Try different models for your use case

---

## 📚 Related Documentation

- **SETUP.md** - Initial setup guide
- **README.md** - Project overview
- **INTEGRATION_GUIDE.md** - How components connect

---

## ❓ FAQ

**Q: Can I use multiple LLM providers?**

A: Not out of the box, but you could add a configuration flag to switch between them.

**Q: Do I need both API keys?**

A: Yes, unless you modify the code to use local alternatives (see "Fully Free Setup" section).

**Q: Will my old embeddings work after changing providers?**

A: No, different embedding models produce different vector dimensions. You'll need to re-embed your data.

**Q: Can I use Azure OpenAI?**

A: Yes! Azure OpenAI is OpenAI-compatible. Update the `base_url` in the OpenAI client:
```python
client = openai.OpenAI(
    api_key="...",
    base_url="https://your-resource.openai.azure.com/"
)
```

---

**Need help with a specific provider?** Open an issue on GitHub!
