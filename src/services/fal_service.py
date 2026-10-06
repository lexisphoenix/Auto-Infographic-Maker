import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FalService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://fal.run"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _generate(self, model: str, prompt: str, image_size: str) -> Optional[str]:
        url = f"{self.base_url}/{model}"
        payload = {
            "prompt": prompt,
            "image_size": image_size,
            "num_images": 1,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "enable_safety_checker": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, headers=self._get_headers(), json=payload)
                    response.raise_for_status()
                    data = response.json()
                    images = data.get("images", [])
                    if images and len(images) > 0:
                        return images[0].get("url")
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for Fal.ai generation: {e}")
            return None

    async def generate_illustration(self, prompt: str, style: str, aspect_ratio: str = '9:16') -> str:
        """
        Uses fal-ai/flux-2 model.
        Aspect ratios supported: square (1:1), portrait (9:16), landscape (16:9)
        """
        size_map = {
            "1:1": "square",
            "9:16": "portrait_9_16",
            "16:9": "landscape_16_9"
        }
        image_size = size_map.get(aspect_ratio, "portrait_9_16")
        
        full_prompt = f"{prompt}. Style: {style}"
        
        # Primary attempt with flux-2
        result = await self._generate("fal-ai/flux-2", full_prompt, image_size)
        if result:
            return result
            
        # Fallback to flux-pro
        logger.info("Falling back to fal-ai/flux-pro")
        result = await self._generate("fal-ai/flux-pro", full_prompt, image_size)
        return result or ""

    async def generate_background(self, prompt: str, style: str, size: str = 'portrait_16_9') -> str:
        full_prompt = f"{prompt}. Style: {style}. Background only, no text."
        result = await self._generate("fal-ai/flux-2", full_prompt, size)
        if not result:
            result = await self._generate("fal-ai/flux-pro", full_prompt, size)
        return result or ""
