"""
LLM Provider Diagnostic Tool
Run this to check which LLM providers are available on your system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.llm_provider import get_llm_service, LLMProvider


async def main():
    """Check all LLM provider availability."""
    print("=" * 60)
    print("LLM Provider Diagnostic Tool")
    print("=" * 60)
    print()
    
    llm_service = get_llm_service()
    status = await llm_service.get_status()
    
    print("Provider Status:")
    print()
    
    # Display each provider
    for provider_name, info in status["providers"].items():
        icon = "[OK]" if info["available"] else "[FAIL]"
        print(f"{icon} {provider_name.upper()}")
        print(f"   Model: {info['model']}")
        print(f"   URL: {info['base_url']}")
        
        if info.get("has_api_key") is not None:
            key_status = "Configured" if info["has_api_key"] else "Not configured"
            print(f"   API Key: {key_status}")
        
        if info["error"]:
            print(f"   Error: {info['error']}")
        
        print()
    
    print("-" * 60)
    print(f"Current Provider: {status['current_provider'] or 'None (will auto-detect)'}")
    print()
    
    print("Fallback Order:")
    for i, provider in enumerate(status["fallback_order"], 1):
        print(f"   {i}. {provider}")
    print()
    
    # Test call
    print("-" * 60)
    print("Testing LLM call...")
    print()
    
    try:
        response = await llm_service.call_llm("Say 'Hello, I am working!' in one sentence.")
        print("Response:")
        print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")
        print()
        print(f"SUCCESS - Using {status['current_provider']}")
    except Exception as e:
        print(f"FAILED: {e}")
    
    print()
    print("=" * 60)
    print("Recommendations:")
    print()
    
    if not any(p["available"] for p in status["providers"].values() if p != "mock"):
        print("WARNING: No LLM providers available!")
        print()
        print("Quick setup options:")
        print()
        print("1. Ollama (Free, Local, Recommended)")
        print("   - Download: https://ollama.com/download")
        print("   - Install and run: ollama pull phi3")
        print()
        print("2. OpenAI (Paid, Cloud)")
        print("   - Get API key: https://platform.openai.com/api-keys")
        print("   - Add to .env: OPENAI_API_KEY=sk-...")
        print()
        print("3. OpenRouter (Free/Paid, Cloud)")
        print("   - Get API key: https://openrouter.ai/keys")
        print("   - Add to .env: OPENROUTER_API_KEY=sk-or-v1-...")
        print()
        print("4. LM Studio (Free, Local)")
        print("   - Download: https://lmstudio.ai")
        print("   - Start server on port 1234")
    else:
        available = [name for name, info in status["providers"].items() if info["available"]]
        print(f"SUCCESS: You have {len(available)} provider(s) available: {', '.join(available)}")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
