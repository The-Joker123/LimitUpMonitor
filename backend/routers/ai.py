from fastapi import APIRouter
import os
import requests

from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/ai-chat")
def ai_chat(request: ChatRequest):
    """
    代理AI聊天请求到 MiniMax Coding Plan API
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    if not api_key:
        return {"error": "MINIMAX_API_KEY 未配置，请在 .env 文件中设置"}
    if not group_id:
        return {"error": "MINIMAX_GROUP_ID 未配置，请在 .env 文件中设置"}

    try:
        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_pro",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "group_id": group_id,
                "model": "MiniMax-Text-01",
                "messages": request.messages,
                "reply_constraints": {"sender_type": "BOT", "receiver_type": "USER"},
                "bot_setting": [
                    {
                        "bot_name": "AI助手",
                        "content": "你是一个有用的AI助手，请用中文回答用户问题。",
                    }
                ],
            },
            timeout=30,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}
