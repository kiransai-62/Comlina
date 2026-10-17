# server/app/integrations/instagram/comments.py
from typing import Dict, Any
from app.integrations.instagram.client import MetaGraphClient

class InstagramComments:
    def __init__(self, client: MetaGraphClient):
        self.client = client

    async def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        """
        Posts a public reply directly under an Instagram comment.
        Uses POST /vXX.X/{comment-id}/replies with message=...
        """
        endpoint = f"{comment_id}/replies"
        return await self.client.post(endpoint, json_data={"message": message})

    async def hide_comment(self, comment_id: str, hide: bool = True) -> Dict[str, Any]:
        """
        Hides or unhides a comment (e.g. for spam/negative sentiment protection).
        """
        endpoint = f"{comment_id}"
        return await self.client.post(endpoint, json_data={"hide": hide})
