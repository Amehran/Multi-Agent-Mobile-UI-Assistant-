# LLM Setup Guide

This guide helps you set up and configure the LLM provider for the Multi-Agent Mobile UI Assistant.

## Overview

The system supports two LLM providers:
- **Ollama**: Local, free, private
- **OpenAI**: Cloud-based, paid, high-quality

## Option 1: Ollama (Recommended for Development)

### Why Ollama?
- ✅ **Free**: No API costs
- ✅ **Private**: All processing happens locally
- ✅ **Fast**: No network latency
- ✅ **Offline**: Works without internet
- ⚠️ **Hardware**: Requires decent CPU/GPU

### Setup Steps

1. **Install Ollama**

   **macOS**:
   ```bash
   brew install ollama
   ```
   
   **Linux**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
   
   **Windows**:
   Download from [ollama.com/download](https://ollama.com/download)

2. **Start Ollama Server**
   ```bash
   ollama serve
   ```
   (This runs in the background on macOS/Linux after first install)

3. **Pull a Model**
   
   **Recommended models**:
   ```bash
   # Small, fast (1.3B parameters)
   ollama pull llama3.2

   # Larger, better quality (8B parameters) 
   ollama pull llama3.1
   
   # Code-focused
   ollama pull codellama
   
   # Fast and capable
   ollama pull mistral
   ```

4. **Configure Project**
   
   Create `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   ```

5. **Test**
   ```bash
   uv run main.py
   ```

### Troubleshooting Ollama

**Server not running**:
```bash
ollama serve
```

**Model not found**:
```bash
ollama list  # Check installed models
ollama pull llama3.2  # Pull missing model
```

**Connection error**:
- Check if Ollama is running: `curl http://localhost:11434`
- Verify OLLAMA_BASE_URL in `.env`

## Option 2: OpenAI

### Why OpenAI?
- ✅ **Quality**: Best-in-class performance
- ✅ **Speed**: Fast API responses
- ✅ **Reliability**: Managed service
- ⚠️ **Cost**: Pay-per-use (affordable for dev)
- ⚠️ **Privacy**: Data sent to OpenAI
- ⚠️ **Internet**: Requires connection

### Setup Steps

1. **Get API Key**
   
   - Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Sign up / Log in
   - Click "Create new secret key"
   - Copy the key (starts with `sk-...`)

2. **Configure Project**
   
   Create `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Choose Model**
   
   **Recommended models**:
   - `gpt-4o-mini`: Best balance (cheap, fast, good)
   - `gpt-4o`: Latest, most capable
   - `gpt-4-turbo`: High quality, fast
   - `gpt-3.5-turbo`: Cheapest, still good

4. **Test**
   ```bash
   uv run main.py
   ```

### OpenAI Pricing (as of 2024)

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o-mini | $0.15/1M tokens | $0.60/1M tokens |
| gpt-4o | $5/1M tokens | $15/1M tokens |
| gpt-3.5-turbo | $0.50/1M tokens | $1.50/1M tokens |

**Estimated costs for this project**:
- Single UI generation: ~$0.001 - $0.01
- 100 generations: ~$0.10 - $1.00 (depending on model)

### Troubleshooting OpenAI

**Authentication error**:
- Check API key in `.env`
- Verify key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Ensure no extra spaces/quotes

**Rate limit error**:
- You've hit API limits
- Upgrade your OpenAI account
- Wait and retry

**Model not found**:
- Check model name spelling
- See available models: [platform.openai.com/docs/models](https://platform.openai.com/docs/models)

## Configuration Options

### Environment Variables

All options can be set in `.env`:

```env
# Required
LLM_PROVIDER=ollama|openai

# Optional (auto-set based on provider if not specified)
LLM_MODEL=llama3.2|gpt-4o-mini|...
LLM_TEMPERATURE=0.7

# OpenAI specific
OPENAI_API_KEY=sk-...

# Ollama specific
OLLAMA_BASE_URL=http://localhost:11434
```

### Temperature

Controls randomness (0.0 to 1.0):
- `0.0`: Deterministic, same output
- `0.7`: Balanced (default)
- `1.0`: Creative, varied output

For UI generation, **0.7 is recommended**.

## Switching Providers

To switch between providers, just change `.env`:

```env
# Use Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Or use OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

No code changes needed!

## Performance Comparison

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| Ollama | llama3.2 | Fast | Good | Free |
| Ollama | llama3.1 | Medium | Very Good | Free |
| OpenAI | gpt-4o-mini | Fast | Excellent | $0.001/gen |
| OpenAI | gpt-4o | Fast | Best | $0.01/gen |

## Recommendations

**For Development**:
- Use **Ollama** with `llama3.2`
- Free, fast, private

**For Production**:
- Use **OpenAI** with `gpt-4o-mini`
- Better quality, reliable, affordable

**For Best Results**:
- Use **OpenAI** with `gpt-4o`
- Highest quality output

## Testing

Run tests with mocked LLM (no API/Ollama needed):
```bash
uv run pytest
```

Tests automatically mock LLM calls to avoid:
- API charges (OpenAI)
- Ollama dependency
- Network calls
- Non-deterministic behavior

## Security

### .env File
- **Never commit** `.env` to git
- Already in `.gitignore`
- Use `.env.example` for templates

### API Keys
- Keep OpenAI keys secret
- Rotate keys if exposed
- Use environment-specific keys

### Ollama
- Runs locally, no external calls
- Private by default
- Data never leaves your machine

## Next Steps

1. Choose provider (Ollama or OpenAI)
2. Follow setup steps above
3. Create `.env` file
4. Run `uv run main.py`
5. Start generating UIs!

## Need Help?

- Ollama docs: [ollama.com/docs](https://ollama.com/docs)
- OpenAI docs: [platform.openai.com/docs](https://platform.openai.com/docs)
- LangChain docs: [python.langchain.com](https://python.langchain.com)
