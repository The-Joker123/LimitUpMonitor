from fastapi import APIRouter
import os
import requests
import anthropic

from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["ai"])

# MiniMax Coding Plan uses Anthropic API compatible endpoint
ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"


@router.post("/ai-chat")
def ai_chat(request: ChatRequest):
    """
    代理AI聊天请求到 MiniMax Coding Plan API (Anthropic API 兼容)
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        return {"error": "MINIMAX_API_KEY 未配置，请在 .env 文件中设置"}

    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=ANTHROPIC_BASE_URL,
        )

        # 构建 system 消息
        system_prompt = "你是一位专业的中文金融顾问，专注于分析A股涨停数据。回答要求：简洁专业，结论先行；如需引用数据请从上下文中提取；数据不足时明确告知；涉及投资建议时提醒风险。"

        # 分离 system 消息和其他消息
        messages = request.messages
        system_msg = None
        if messages and messages[0].get("role") == "system":
            system_msg = messages[0].get("content", "")
            messages = messages[1:]

        if system_msg:
            system_prompt = system_msg

        response = client.messages.create(
            model="MiniMax-M2.7",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )

        # 处理响应内容，可能包含 text 或 thinking blocks
        content_text = ""
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                content_text = block.text
                break

        # 兼容前端格式
        return {
            "choices": [
                {
                    "message": {
                        "content": content_text
                    }
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}
