import os
from utils.logger import get_logger
from dotenv import load_dotenv
from mem0 import MemoryClient

logger = get_logger(__name__)

load_dotenv()


class Mem0Manager:
    """Manages persistent user preferences with Mem0."""

    def __init__(self):
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("Mem0 api key is missing.")
        self.client = MemoryClient(api_key = api_key)

    def search_memories(self, query: str, user_id: str, limit: int = 5) -> list[str]:
        if not user_id or not user_id.strip():
            raise ValueError("A value user_id is required")

        try:
            result = self.client.search(
                query = query,
                filters = {"user_id": user_id},
                top_k = limit
            ) 
            results = (
                result.get("results", []
                           if isinstance(result, dict)
                           else getattr(result, "results", []))
            )
            return [
                item["memory"]
                for item in results
                if isinstance(item, dict) and item.get("memory")
            ] 

        except Exception:
            logger.exception(
                            "Mem0 search failed for user_id=%s",
                            user_id,
                        )
            

    def save_conversation(self, query: str, response: str, user_id: str) -> None:
        if not user_id or not user_id.strip():
            raise ValueError("A valid user_id is required") 

        try:
            self.client.add(
                messages = [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response}
                ],
                user_id = user_id,
                metadata = {"source": "Anime Recommender"}
            ) 
        except Exception:
            logger.error("Mem0 save failed for this user")    
