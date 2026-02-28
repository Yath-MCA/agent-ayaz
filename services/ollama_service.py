import httpx
import json


async def call_ollama(prompt: str, model: str, base_url: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{base_url}/api/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "")


async def stream_ollama(prompt: str, model: str, base_url: str):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{base_url}/api/generate", json=payload) as response:
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
