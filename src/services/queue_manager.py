import logging
from typing import List, Optional, Dict
from src.models import ResearchResult, DesignBrief, InfographicItem

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self, supabase_client):
        self.db = supabase_client

    async def add_to_queue(self, research_result: ResearchResult, design_brief: DesignBrief) -> str:
        data = {
            "topic_fingerprint": f"{research_result.title[:20]}_{design_brief.topic[:20]}".replace(" ", "_"),
            "title": research_result.title,
            "summary": research_result.summary,
            "key_facts": research_result.key_facts,
            "novelty_score": research_result.novelty_score,
            "viz_score": research_result.viz_score,
            "priority_score": research_result.priority_score,
            "design_brief": design_brief.model_dump(),
            "status": "pending"
        }
        res = self.db.table("infographic_queue").insert(data).execute()
        return res.data[0]["id"] if res.data else ""

    async def get_next_pending(self) -> Optional[InfographicItem]:
        res = self.db.table("infographic_queue").select("*").eq("status", "pending").order("priority_score", desc=True).limit(1).execute()
        if res.data:
            return InfographicItem(**res.data[0])
        return None

    async def update_status(self, item_id: str, status: str, **kwargs):
        update_data = {"status": status, **kwargs}
        self.db.table("infographic_queue").update(update_data).eq("id", item_id).execute()

    async def get_queue_stats(self) -> Dict[str, int]:
        res = self.db.table("infographic_queue").select("status").execute()
        stats = {}
        for row in res.data:
            stats[row["status"]] = stats.get(row["status"], 0) + 1
        return stats

    async def check_duplicate(self, topic_fingerprint: str) -> bool:
        res = self.db.table("infographic_queue").select("id").eq("topic_fingerprint", topic_fingerprint).execute()
        return len(res.data) > 0

    async def get_approved_for_posting(self) -> List[InfographicItem]:
        res = self.db.table("infographic_queue").select("*").eq("status", "approved").lte("scheduled_for", "now()").execute()
        return [InfographicItem(**item) for item in res.data]
