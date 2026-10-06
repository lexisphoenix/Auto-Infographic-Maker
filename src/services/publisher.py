import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class InstagramPublisher:
    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://graph.facebook.com/v21.0"

    async def publish_image(self, image_url: str, caption: str) -> str:
        async with httpx.AsyncClient() as client:
            create_url = f"{self.base_url}/{self.user_id}/media"
            create_payload = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            try:
                logger.info("Creating media container...")
                create_res = await client.post(create_url, data=create_payload)
                create_res.raise_for_status()
                creation_id = create_res.json().get("id")
                
                await asyncio.sleep(5)
                
                publish_url = f"{self.base_url}/{self.user_id}/media_publish"
                publish_payload = {
                    "creation_id": creation_id,
                    "access_token": self.access_token
                }
                logger.info("Publishing media container...")
                publish_res = await client.post(publish_url, data=publish_payload)
                publish_res.raise_for_status()
                
                post_id = publish_res.json().get("id")
                return post_id
            except Exception as e:
                logger.error(f"Error publishing to Instagram: {e}")
                return ""

    async def publish_video(self, video_url: str, caption: str) -> str:
        pass
