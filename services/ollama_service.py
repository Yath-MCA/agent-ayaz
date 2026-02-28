import httpx


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
