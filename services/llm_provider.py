"""
LLM Provider Abstraction Layer
Multi-provider support with automatic fallback chain:
1. Ollama (local, preferred)
2. OpenAI API (if API key available)
3. OpenRouter (if API key available)
4. LM Studio (local alternative)
5. GitHub Copilot CLI (if gh CLI authenticated)
6. Mock mode (for testing/demos)
"""

import os
import asyncio
import httpx
import json
import logging
import shutil
import subprocess
from typing import Optional, Dict, Any, AsyncGenerator
from enum import Enum
from dataclasses import dataclass

log = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    LM_STUDIO = "lm_studio"
    GITHUB_COPILOT = "github_copilot"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model: str
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 120
    available: bool = False
    error: Optional[str] = None


class LLMProviderService:
    """
    Multi-provider LLM service with automatic fallback.
    
    Priority order:
    1. Ollama (local, free, private)
    2. OpenAI (cloud, requires API key)
    3. OpenRouter (cloud, requires API key)
    4. LM Studio (local alternative to Ollama)
    5. GitHub Copilot CLI (uses gh copilot suggest, requires gh CLI authenticated)
    6. Mock (fallback for testing)
    """
    
    def __init__(self):
        self.providers: Dict[LLMProvider, LLMConfig] = {}
        self._initialize_providers()
        self._current_provider: Optional[LLMProvider] = None
    
    def _initialize_providers(self):
        """Detect and configure all available providers."""
        
        # 1. Ollama (preferred)
        self.providers[LLMProvider.OLLAMA] = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model=os.getenv("OLLAMA_MODEL", "phi3"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            available=False
        )
        
        # 2. OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        self.providers[LLMProvider.OPENAI] = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url="https://api.openai.com/v1",
            api_key=openai_key if openai_key else None,
            available=bool(openai_key)
        )
        
        # 3. OpenRouter (multi-model proxy)
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.providers[LLMProvider.OPENROUTER] = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key if openrouter_key else None,
            available=bool(openrouter_key)
        )
        
        # 4. LM Studio (local alternative)
        self.providers[LLMProvider.LM_STUDIO] = LLMConfig(
            provider=LLMProvider.LM_STUDIO,
            model=os.getenv("LM_STUDIO_MODEL", "local-model"),
            base_url=os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1"),
            available=False
        )
        
        # 5. GitHub Copilot CLI (uses gh copilot suggest)
        gh_available = shutil.which("gh") is not None
        self.providers[LLMProvider.GITHUB_COPILOT] = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model=os.getenv("GITHUB_COPILOT_MODEL", "copilot"),
            base_url="gh://copilot/suggest",
            available=gh_available,
            error=None if gh_available else "gh CLI not found in PATH",
        )
        
        # 6. Mock (always available as last resort)
        self.providers[LLMProvider.MOCK] = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
            base_url="",
            available=True
        )
    
    async def check_provider_health(self, provider: LLMProvider) -> bool:
        """Check if a provider is healthy and available."""
        config = self.providers[provider]
        
        if provider == LLMProvider.MOCK:
            return True
        
        if provider == LLMProvider.GITHUB_COPILOT:
            # Check gh CLI is installed and authenticated
            if shutil.which("gh") is None:
                config.available = False
                config.error = "gh CLI not found in PATH"
                return False
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["gh", "auth", "status"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    ),
                )
                available = result.returncode == 0
                config.available = available
                config.error = None if available else "gh CLI not authenticated (run: gh auth login)"
                return available
            except Exception as e:
                config.available = False
                config.error = str(e)
                return False
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                if provider == LLMProvider.OLLAMA:
                    # Check Ollama /api/tags endpoint
                    response = await client.get(f"{config.base_url}/api/tags")
                    available = response.status_code == 200
                    config.available = available
                    config.error = None if available else f"HTTP {response.status_code}"
                    return available
                
                elif provider in [LLMProvider.OPENAI, LLMProvider.OPENROUTER]:
                    # Check OpenAI-compatible API
                    if not config.api_key:
                        config.available = False
                        config.error = "No API key configured"
                        return False
                    
                    headers = {"Authorization": f"Bearer {config.api_key}"}
                    response = await client.get(f"{config.base_url}/models", headers=headers)
                    available = response.status_code == 200
                    config.available = available
                    config.error = None if available else f"HTTP {response.status_code}"
                    return available
                
                elif provider == LLMProvider.LM_STUDIO:
                    # Check LM Studio /v1/models endpoint
                    response = await client.get(f"{config.base_url}/models")
                    available = response.status_code == 200
                    config.available = available
                    config.error = None if available else f"HTTP {response.status_code}"
                    return available
        
        except Exception as e:
            config.available = False
            config.error = str(e)
            log.debug(f"{provider} health check failed: {e}")
            return False
        
        return False
    
    async def get_available_provider(self) -> Optional[LLMProvider]:
        """Get first available provider from priority list."""
        priority_order = [
            LLMProvider.OLLAMA,
            LLMProvider.OPENAI,
            LLMProvider.OPENROUTER,
            LLMProvider.LM_STUDIO,
            LLMProvider.GITHUB_COPILOT,
            LLMProvider.MOCK,
        ]
        
        for provider in priority_order:
            if await self.check_provider_health(provider):
                log.info(f"✅ Using LLM provider: {provider}")
                self._current_provider = provider
                return provider
        
        # Fallback to mock
        log.warning("⚠️ All providers failed, using MOCK mode")
        self._current_provider = LLMProvider.MOCK
        return LLMProvider.MOCK
    
    async def call_llm(self, prompt: str, provider: Optional[LLMProvider] = None) -> str:
        """
        Call LLM with automatic provider selection/fallback.
        
        Args:
            prompt: User prompt
            provider: Specific provider to use (optional, auto-selects if None)
        
        Returns:
            LLM response text
        """
        if provider is None:
            provider = await self.get_available_provider()
        
        if not provider:
            return self._mock_response(prompt)
        
        config = self.providers[provider]
        
        try:
            if provider == LLMProvider.OLLAMA:
                return await self._call_ollama(prompt, config)
            
            elif provider in [LLMProvider.OPENAI, LLMProvider.OPENROUTER]:
                return await self._call_openai_compatible(prompt, config)
            
            elif provider == LLMProvider.LM_STUDIO:
                return await self._call_lm_studio(prompt, config)
            
            elif provider == LLMProvider.GITHUB_COPILOT:
                return await self._call_github_copilot(prompt, config)
            
            elif provider == LLMProvider.MOCK:
                return self._mock_response(prompt)
        
        except Exception as e:
            log.error(f"❌ {provider} failed: {e}")
            
            # Try fallback to next provider
            if provider != LLMProvider.MOCK:
                log.info("🔄 Trying fallback provider...")
                next_provider = await self.get_available_provider()
                if next_provider and next_provider != provider:
                    return await self.call_llm(prompt, next_provider)
            
            # Final fallback to mock
            return self._mock_response(prompt)
    
    async def stream_llm(
        self, 
        prompt: str, 
        provider: Optional[LLMProvider] = None
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response."""
        if provider is None:
            provider = await self.get_available_provider()
        
        if not provider:
            yield self._mock_response(prompt)
            return
        
        config = self.providers[provider]
        
        try:
            if provider == LLMProvider.OLLAMA:
                async for chunk in self._stream_ollama(prompt, config):
                    yield chunk
            
            elif provider in [LLMProvider.OPENAI, LLMProvider.OPENROUTER]:
                async for chunk in self._stream_openai_compatible(prompt, config):
                    yield chunk
            
            elif provider == LLMProvider.LM_STUDIO:
                async for chunk in self._stream_lm_studio(prompt, config):
                    yield chunk
            
            elif provider == LLMProvider.GITHUB_COPILOT:
                result = await self._call_github_copilot(prompt, config)
                yield result
            
            elif provider == LLMProvider.MOCK:
                yield self._mock_response(prompt)
        
        except Exception as e:
            log.error(f"❌ {provider} stream failed: {e}")
            yield self._mock_response(prompt)
    
    # ─── Provider-specific implementations ───────────────────────────
    
    async def _call_ollama(self, prompt: str, config: LLMConfig) -> str:
        """Call Ollama API."""
        payload = {
            "model": config.model,
            "prompt": prompt,
            "stream": False,
        }
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(f"{config.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
    
    async def _stream_ollama(self, prompt: str, config: LLMConfig) -> AsyncGenerator[str, None]:
        """Stream Ollama response."""
        payload = {
            "model": config.model,
            "prompt": prompt,
            "stream": True,
        }
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            async with client.stream("POST", f"{config.base_url}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
    
    async def _call_openai_compatible(self, prompt: str, config: LLMConfig) -> str:
        """Call OpenAI-compatible API (OpenAI, OpenRouter)."""
        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.base_url}/chat/completions", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _stream_openai_compatible(
        self, 
        prompt: str, 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream OpenAI-compatible response."""
        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            async with client.stream(
                "POST", 
                f"{config.base_url}/chat/completions", 
                json=payload, 
                headers=headers
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    async def _call_lm_studio(self, prompt: str, config: LLMConfig) -> str:
        """Call LM Studio API (OpenAI-compatible)."""
        return await self._call_openai_compatible(prompt, config)
    
    async def _stream_lm_studio(
        self, 
        prompt: str, 
        config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        """Stream LM Studio response."""
        async for chunk in self._stream_openai_compatible(prompt, config):
            yield chunk
    
    async def _call_github_copilot(self, prompt: str, config: LLMConfig) -> str:
        """
        Call GitHub Copilot CLI via `gh copilot suggest`.
        
        Each call is isolated (no accumulated context), preventing LLM context rot.
        Requires: gh CLI installed and authenticated (`gh auth login`).
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["gh", "copilot", "suggest", "-t", "shell", prompt],
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                ),
            )            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                # Extract suggestion lines (skip blank lines from gh copilot output)
                lines = [line for line in output.splitlines() if line.strip()]
                return "\n".join(lines)
            
            stderr = result.stderr.strip()
            raise RuntimeError(f"gh copilot suggest failed (exit {result.returncode}): {stderr}")
        
        except FileNotFoundError:
            raise RuntimeError("gh CLI not found. Install from https://cli.github.com/")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"gh copilot suggest timed out after {config.timeout}s")
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response for testing/fallback."""
        return (
            f"[MOCK RESPONSE - No LLM available]\n\n"
            f"Received prompt: {prompt[:100]}...\n\n"
            f"To enable real LLM responses:\n"
            f"1. Install Ollama: https://ollama.com/download\n"
            f"2. Or set OPENAI_API_KEY in .env\n"
            f"3. Or set OPENROUTER_API_KEY in .env\n"
            f"4. Or run LM Studio: https://lmstudio.ai"
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        
        for provider_type, config in self.providers.items():
            await self.check_provider_health(provider_type)
            status[provider_type] = {
                "available": config.available,
                "model": config.model,
                "base_url": config.base_url,
                "error": config.error,
                "has_api_key": bool(config.api_key) if config.api_key is not None else None
            }
        
        return {
            "current_provider": self._current_provider,
            "providers": status,
            "fallback_order": [
                LLMProvider.OLLAMA,
                LLMProvider.OPENAI,
                LLMProvider.OPENROUTER,
                LLMProvider.LM_STUDIO,
                LLMProvider.GITHUB_COPILOT,
                LLMProvider.MOCK,
            ]
        }


# Global singleton instance
_llm_service: Optional[LLMProviderService] = None


def get_llm_service() -> LLMProviderService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMProviderService()
    return _llm_service
