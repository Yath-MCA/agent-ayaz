# LLM Provider Fallback System - Implementation Summary

## Problem Statement
User requested: "if ollama was not installed or not found path, can check chatgpt local version worst case what could be best solution"

## Solution Implemented
Multi-provider LLM abstraction layer with automatic fallback chain supporting 5 providers.

---

## Provider Priority Chain

The system tries providers in this order:

1. **Ollama** (Local, Free, Preferred)
   - Local inference, private, no API cost
   - Requires: Ollama installed + model pulled
   - Config: `OLLAMA_URL`, `OLLAMA_MODEL`

2. **OpenAI** (Cloud, Paid)
   - GPT-4o-mini, GPT-4, etc.
   - Requires: API key ($)
   - Config: `OPENAI_API_KEY`, `OPENAI_MODEL`

3. **OpenRouter** (Cloud, Free/Paid)
   - Access to 100+ models (many free)
   - Requires: API key (free tier available)
   - Config: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`

4. **LM Studio** (Local, Free)
   - Alternative to Ollama
   - Requires: LM Studio running on port 1234
   - Config: `LM_STUDIO_URL`, `LM_STUDIO_MODEL`

5. **Mock** (Fallback, Always Available)
   - Returns instructional message
   - No real LLM calls
   - Used when all providers fail

---

## Key Features

### 1. Zero Configuration
- System auto-detects available providers
- No changes needed if Ollama unavailable
- Falls back to next available provider

### 2. Health Checks
- Each provider tested before use
- 5-second timeout for health checks
- Errors logged but don't crash system

### 3. Automatic Failover
- If Ollama call fails → tries OpenAI
- If OpenAI fails → tries OpenRouter
- If all fail → uses Mock mode with instructions

### 4. Unified API
- Single `call_llm()` function for all providers
- Same interface regardless of backend
- Streaming support for all providers

---

## Files Created

### 1. `services/llm_provider.py` (450 lines)
Core implementation:
```python
from services.llm_provider import get_llm_service

llm_service = get_llm_service()

# Auto-selects best provider
response = await llm_service.call_llm("Your prompt")

# Stream response
async for chunk in llm_service.stream_llm("Your prompt"):
    print(chunk)

# Check status
status = await llm_service.get_status()
```

### 2. `tools/check_llm.py` + `check_llm.bat`
Diagnostic tool:
- Shows which providers are available
- Explains configuration for each
- Tests actual LLM call
- Provides setup instructions

### 3. Updated `.env.example`
```env
# 1. Ollama (Local, Free, Preferred)
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434

# 2. OpenAI (Cloud, Paid)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# 3. OpenRouter (Cloud, Free/Paid)
# OPENROUTER_API_KEY=sk-or-v1-...
# OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# 4. LM Studio (Local alternative)
# LM_STUDIO_URL=http://localhost:1234/v1
# LM_STUDIO_MODEL=local-model
```

---

## API Endpoints

### New Endpoint
**GET /llm-providers**
- Detailed status of all providers
- Shows which are available/failed
- Error messages for failed providers
- Current active provider

Response:
```json
{
  "current_provider": "ollama",
  "providers": {
    "ollama": {"available": true, "model": "phi3", "error": null},
    "openai": {"available": false, "error": "No API key configured"},
    "openrouter": {"available": false, "error": "No API key configured"},
    "lm_studio": {"available": false, "error": "Connection refused"},
    "mock": {"available": true, "model": "mock", "error": null}
  },
  "fallback_order": ["ollama", "openai", "openrouter", "lm_studio", "mock"]
}
```

### Updated Endpoints
- **GET /status** - now shows `llm_provider` field
- **GET /health** - now shows `llm_providers` object with all statuses

---

## Usage Examples

### Scenario 1: Ollama Not Installed
**Before:**
```
❌ Error: Ollama not running
   Application crashes or fails
```

**After:**
```
⚠️ Ollama failed: Connection refused
🔄 Trying OpenAI...
✅ Using OpenAI (gpt-4o-mini)
```

### Scenario 2: All Providers Failed
**Before:**
```
❌ Fatal error: No LLM available
```

**After:**
```
⚠️ No providers available, using MOCK mode
📝 Response includes setup instructions:
   1. Install Ollama: https://ollama.com/download
   2. Or set OPENAI_API_KEY in .env
   3. Or set OPENROUTER_API_KEY in .env
   4. Or run LM Studio
```

### Scenario 3: Ollama Temporarily Down
**Before:**
```
❌ Service unavailable
```

**After:**
```
⚠️ Ollama temporarily unavailable
✅ Auto-failed over to OpenAI
   User doesn't notice interruption
```

---

## Configuration Options

### Option A: Keep Ollama Only (Default)
```env
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
```

### Option B: OpenAI as Backup
```env
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

### Option C: OpenAI Only (No Ollama)
```env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

### Option D: OpenRouter Free Tier
```env
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

---

## Testing

### 1. Check Available Providers
```bash
check_llm.bat
```

Output:
```
============================================================
LLM Provider Diagnostic Tool
============================================================

Provider Status:

[FAIL] OLLAMA
   Model: phi3
   URL: http://localhost:11434
   Error: Connection refused

[OK] OPENAI
   Model: gpt-4o-mini
   URL: https://api.openai.com/v1
   API Key: Configured

...

Current Provider: openai
Fallback Order:
   1. ollama
   2. openai
   3. openrouter
   4. lm_studio
   5. mock

------------------------------------------------------------
Testing LLM call...
Response: Hello, I am working!
SUCCESS - Using openai
```

### 2. Test via API
```bash
curl http://localhost:8000/llm-providers
```

### 3. Test Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test message"}'
```

---

## Benefits

1. **Resilience**
   - System never crashes due to missing LLM
   - Automatic failover to working providers
   - Mock mode provides useful error messages

2. **Flexibility**
   - Use local (Ollama/LM Studio) or cloud (OpenAI/OpenRouter)
   - Mix providers for cost optimization
   - Easy provider switching

3. **Cost Control**
   - Prefer free local models (Ollama)
   - Fall back to paid only when needed
   - OpenRouter has free tier models

4. **Zero Downtime**
   - Providers tested before each call
   - Automatic retry with next provider
   - Transparent to end users

5. **Easy Testing**
   - Mock mode for development
   - No LLM needed for CI/CD
   - Diagnostic tool shows exact status

---

## Recommendations

### For Production
```env
# Primary: Ollama (local, fast, free)
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434

# Backup: OpenAI (reliable cloud fallback)
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

### For Development
```env
# Use mock mode or free tier
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

### For Cost Optimization
```env
# Try free providers first, paid last
OLLAMA_MODEL=phi3
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENAI_MODEL=gpt-4o-mini  # Only if free providers fail
```

---

## Migration Notes

### Existing Code
No changes needed! Old code using `call_ollama()` still works:
```python
response = await call_ollama("Your prompt")
```

This now internally uses the multi-provider system.

### New Code
Can explicitly use provider service:
```python
from services.llm_provider import get_llm_service, LLMProvider

llm_service = get_llm_service()

# Auto-select
response = await llm_service.call_llm("prompt")

# Force specific provider
response = await llm_service.call_llm("prompt", LLMProvider.OPENAI)
```

---

## Next Steps

1. **Test the diagnostic tool**
   ```bash
   check_llm.bat
   ```

2. **Configure your preferred provider**
   - Add API keys to `.env` if using cloud providers
   - Or install Ollama for local inference

3. **Verify it works**
   ```bash
   python main.py
   # Visit http://localhost:8000/llm-providers
   ```

4. **Use the system**
   - Everything works the same
   - Provider selection is automatic
   - Check logs to see which provider is used

---

## Troubleshooting

### All Providers Show FAIL
- No providers configured
- Use mock mode or configure at least one
- Run `check_llm.bat` for instructions

### Ollama Shows FAIL
- Not installed: Download from https://ollama.com/download
- Not running: Run `ollama serve`
- Wrong URL: Check `OLLAMA_URL` in .env

### OpenAI Shows FAIL
- No API key: Get from https://platform.openai.com/api-keys
- Invalid key: Check `OPENAI_API_KEY` in .env
- Quota exceeded: Check billing at platform.openai.com

### Want Free Cloud Option
- Use OpenRouter free models:
  ```env
  OPENROUTER_API_KEY=sk-or-v1-your-key
  OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
  ```

---

## Summary

✅ **System now supports 5 LLM providers**
✅ **Automatic fallback if Ollama not available**
✅ **Zero configuration needed (uses mock mode)**
✅ **Diagnostic tool to check provider status**
✅ **Backward compatible with existing code**
✅ **Cloud backup options (OpenAI, OpenRouter)**
✅ **Free tier available (OpenRouter, LM Studio, Ollama)**

**No more "Ollama not found" errors!**
