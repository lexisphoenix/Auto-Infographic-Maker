from fastapi import FastAPI
import uvicorn
import logging
from supabase import create_client, Client
from src.config import settings
from src.services.researcher import ResearchService
from src.services.designer import InfographicDesigner
from src.services.queue_manager import QueueManager
from src.services.reviewer import TelegramReviewer
from src.services.publisher import InstagramPublisher
from src.models import DesignBrief, InfographicItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auto-Infographic-Maker API")

# Initialize services
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
queue_manager = QueueManager(supabase)
researcher = ResearchService(settings.ANTHROPIC_API_KEY)
designer = InfographicDesigner(settings.ANTHROPIC_API_KEY, settings.FAL_API_KEY, settings.PUPPETEER_SERVICE_URL)
reviewer = TelegramReviewer(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID, queue_manager)
publisher = InstagramPublisher(settings.META_ACCESS_TOKEN, settings.META_INSTAGRAM_USER_ID)

@app.post("/api/research/run")
async def trigger_research():
    logger.info("Starting research cycle...")
    results = await researcher.run_research_cycle()
    added = 0
    for res in results:
        is_dup = await queue_manager.check_duplicate(res.title[:20])
        if not is_dup:
            brief = DesignBrief(
                topic=res.title,
                headline=f"The Truth About {res.title[:15]}",
                story_angle="Informative",
                key_facts=res.key_facts,
                visual_metaphor="A soaring rocket",
                canvas_format="9:16",
                design_language="dark-glass"
            )
            await queue_manager.add_to_queue(res, brief)
            added += 1
    return {"status": "success", "found": len(results), "added_to_queue": added}

@app.post("/api/design/generate")
async def generate_design():
    item = await queue_manager.get_next_pending()
    if not item:
        return {"status": "empty_queue"}
        
    await queue_manager.update_status(item.id, "generating")
    try:
        brief = DesignBrief(**item.design_brief)
        result = await designer.generate_infographic(brief)
        await queue_manager.update_status(
            item.id, 
            "generated",
            image_url=result["image_url"],
            html_path=result["html_path"],
            caption=result["caption"],
            hashtags=result["hashtags"]
        )
        return {"status": "success", "item_id": item.id}
    except Exception as e:
        logger.error(f"Design generation failed: {e}")
        await queue_manager.update_status(item.id, "failed")
        return {"status": "error", "message": str(e)}

@app.post("/api/review/send")
async def send_for_review(item_id: str):
    res = supabase.table("infographic_queue").select("*").eq("id", item_id).execute()
    if not res.data:
        return {"status": "not_found"}
    item = InfographicItem(**res.data[0])
    await reviewer.send_for_review(item)
    return {"status": "sent"}

@app.post("/api/publish")
async def publish_approved():
    items = await queue_manager.get_approved_for_posting()
    published = []
    for item in items:
        if item.image_url:
            post_id = await publisher.publish_image(item.image_url, item.caption or item.title)
            if post_id:
                await queue_manager.update_status(item.id, "published")
                published.append(item.id)
    return {"status": "success", "published": published}

@app.get("/api/queue/stats")
async def queue_stats():
    stats = await queue_manager.get_queue_stats()
    return {"stats": stats}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
