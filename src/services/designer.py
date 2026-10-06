import logging
import httpx
from typing import Dict, Any
from anthropic import AsyncAnthropic
from src.models import DesignBrief
from src.services.fal_service import FalService
from src.services.cloudinary_service import upload_image

logger = logging.getLogger(__name__)

DESIGN_LANGUAGE_PROMPTS = {
    "dark-glass": "Dark mode glassmorphism with neon accents and frosted glass panels.",
    "blueprint": "Technical blueprint style, monospaced fonts, grid backgrounds, cyan/white on dark blue.",
    "naturalist-plate": "Vintage botanical illustration style, warm cream backgrounds, serif fonts.",
    "editorial": "High-end magazine editorial layout, bold typography, stark black and white with one accent color."
}

class InfographicDesigner:
    def __init__(self, anthropic_api_key: str, fal_api_key: str, puppeteer_url: str):
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.fal_service = FalService(api_key=fal_api_key)
        self.puppeteer_url = puppeteer_url

    async def generate_infographic(self, brief: DesignBrief) -> Dict[str, Any]:
        logger.info(f"Generating infographic for {brief.topic}")
        
        # a. Generate hero image
        hero_prompt = f"{brief.visual_metaphor} for {brief.topic}"
        style_prompt = DESIGN_LANGUAGE_PROMPTS.get(brief.design_language, "Modern clean style")
        hero_url = await self.fal_service.generate_illustration(hero_prompt, style_prompt, brief.canvas_format)
        
        # Generate HTML with Claude
        html_content = await self._generate_html(brief, style_prompt, hero_url)
        
        # d. Render PNG via Puppeteer service
        png_path = await self._render_png(html_content, brief.canvas_format)
        
        # e, f. Review and Regenerate (stubbed)
        review_passed = await self._review_png(png_path)
        if not review_passed:
            logger.warning("PNG review failed, ideally regenerate here.")
        
        # g. Upload to Cloudinary
        final_image_url = upload_image(png_path)
        
        # h. Generate caption
        caption_data = await self._generate_caption(brief)
        
        return {
            "html_path": "local_path_or_str",
            "image_url": final_image_url,
            "caption": caption_data.get("caption", ""),
            "hashtags": caption_data.get("hashtags", [])
        }

    async def _generate_html(self, brief: DesignBrief, style_prompt: str, hero_url: str) -> str:
        prompt = f"""
        Create a self-contained HTML infographic.
        Topic: {brief.topic}
        Headline: {brief.headline}
        Facts: {brief.key_facts}
        Hero Image URL: {hero_url}
        Design Language: {style_prompt}
        
        RULES:
        - Canvas is a PLACE not a page (scene-building).
        - Data objects carry the data (not generic charts).
        - All colors/fonts from the design language.
        - @infographycs branding in bottom-right.
        - Source/credit small but present.
        - Inline CSS, embedded SVG, @import fonts.
        """
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _render_png(self, html: str, canvas_format: str) -> str:
        dims = {"1:1": (1080, 1080), "9:16": (1080, 1920), "16:9": (1920, 1080)}
        width, height = dims.get(canvas_format, (1080, 1920))
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.puppeteer_url}/render", 
                    json={"html": html, "width": width, "height": height}
                )
                response.raise_for_status()
                return response.json().get("path", "/tmp/rendered.png")
            except Exception as e:
                logger.error(f"Puppeteer render failed: {e}")
                return "/tmp/fallback.png"

    async def _review_png(self, png_path: str) -> bool:
        return True

    async def _generate_caption(self, brief: DesignBrief) -> Dict[str, Any]:
        prompt = f"Generate an engaging Instagram caption and hashtags for an infographic about {brief.topic}."
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"caption": response.content[0].text, "hashtags": ["#infographic", "#data", "#tech"]}
