import arxiv
import httpx
import logging
from typing import List, Dict, Any
from anthropic import AsyncAnthropic
import json
from src.models import ResearchResult

logger = logging.getLogger(__name__)

class ResearchService:
    def __init__(self, anthropic_api_key: str):
        self.client = AsyncAnthropic(api_key=anthropic_api_key)

    async def fetch_arxiv(self, categories: List[str], max_results: int = 20) -> List[Dict[str, Any]]:
        query = " OR ".join([f"cat:{cat}" for cat in categories])
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        results = []
        for result in search.results():
            results.append({
                "title": result.title,
                "summary": result.summary,
                "url": result.entry_id
            })
        return results

    async def fetch_hackernews_top(self, limit: int = 15) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient() as client:
            try:
                top_response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                top_response.raise_for_status()
                story_ids = top_response.json()[:limit]
                
                for sid in story_ids:
                    item_response = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    item_response.raise_for_status()
                    item = item_response.json()
                    if item:
                        results.append({
                            "title": item.get("title", ""),
                            "summary": item.get("text", ""),
                            "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}")
                        })
            except Exception as e:
                logger.error(f"Error fetching HackerNews: {e}")
        return results

    async def score_topic(self, title: str, summary: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze this topic for an infographic:
        Title: {title}
        Summary: {summary}

        Return a JSON response with the following keys:
        - novelty_score (0-10)
        - impact_score (0-10)
        - viz_score (0-10)
        - priority_score (0-10, average of the above)
        - is_visualizable (boolean)
        - story_angles (list of 3 strings)
        """
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f"Error parsing Claude score response: {e}")
            return {"novelty_score": 0, "impact_score": 0, "viz_score": 0, "priority_score": 0, "is_visualizable": False, "story_angles": []}

    async def extract_facts(self, title: str, content: str) -> Dict[str, Any]:
        prompt = f"""
        Extract key information for an infographic:
        Title: {title}
        Content: {content}

        Return a JSON with:
        - key_facts (list of strings)
        - comparisons (list of strings)
        - timeline_events (list of strings)
        - visual_metaphor_suggestions (list of strings)
        """
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f"Error parsing Claude facts response: {e}")
            return {"key_facts": [], "comparisons": [], "timeline_events": [], "visual_metaphor_suggestions": []}

    async def run_research_cycle(self) -> List[ResearchResult]:
        raw_items = []
        raw_items.extend(await self.fetch_arxiv(["cs.AI", "cs.LG", "q-bio", "physics"], max_results=10))
        raw_items.extend(await self.fetch_hackernews_top(limit=10))
        
        results = []
        for item in raw_items:
            title = item["title"]
            summary = item["summary"]
            
            score_data = await self.score_topic(title, summary)
            if score_data.get("priority_score", 0) >= 7 and score_data.get("is_visualizable"):
                facts_data = await self.extract_facts(title, summary)
                results.append(ResearchResult(
                    source_url=item["url"],
                    title=title,
                    summary=summary,
                    key_facts=facts_data.get("key_facts", []),
                    viz_score=score_data.get("viz_score", 0),
                    novelty_score=score_data.get("novelty_score", 0),
                    priority_score=score_data.get("priority_score", 0)
                ))
        return results
