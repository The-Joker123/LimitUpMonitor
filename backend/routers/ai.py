from fastapi import APIRouter
import os
import json
from pathlib import Path
import requests

from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["ai"])

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"


def load_ai_config():
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return config.get("ai", {})
    except Exception:
        return {}


def build_openai_payload(model, messages, system_prompt):
    """构建 OpenAI 兼容格式的请求体"""
    all_messages = []
    if system_prompt:
        all_messages.append({"role": "system", "content": system_prompt})
    all_messages.extend(messages)
    return {
        "model": model,
        "messages": all_messages,
        "max_tokens": 4096,
        "temperature": 0.7
    }


def call_dashscope(api_key, base_url, model, messages, system_prompt):
    """调用阿里百炼 API (OpenAI 兼容)"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = build_openai_payload(model, messages, system_prompt)
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        return {"error": f"DashScope API error: {response.status_code} - {response.text}"}
    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return {"choices": [{"message": {"content": content}}]}


def call_openai_compatible(api_key, base_url, model, messages, system_prompt):
    """调用标准 OpenAI 兼容 API"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = build_openai_payload(model, messages, system_prompt)
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        return {"error": f"API error: {response.status_code} - {response.text}"}
    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return {"choices": [{"message": {"content": content}}]}


@router.post("/ai-chat")
def ai_chat(request: ChatRequest):
    """
    代理AI聊天请求，支持多 provider
    """
    ai_config = load_ai_config()
    api_key = ai_config.get("apiKey") or os.getenv("MINIMAX_API_KEY")

    if not api_key:
        return {"error": "AI API Key 未配置，请在设置中配置"}

    provider = ai_config.get("provider", "minimax")
    base_url = ai_config.get("baseUrl", "https://api.minimaxi.com/anthropic")
    model = ai_config.get("model", "MiniMax-M2.7")

    # 分离 system 消息
    messages = request.messages
    system_prompt = "你是一位专业的中文金融顾问，专注于分析A股涨停数据。回答要求：简洁专业，结论先行；如需引用数据请从上下文中提取；数据不足时明确告知；涉及投资建议时提醒风险。"
    if messages and messages[0].get("role") == "system":
        system_prompt = messages[0].get("content", "")
        messages = messages[1:]

    try:
        if provider == "dashscope":
            return call_dashscope(api_key, base_url, model, messages, system_prompt)
        elif provider in ("openai",):
            return call_openai_compatible(api_key, base_url, model, messages, system_prompt)
        else:
            # MiniMax / Anthropic 用 anthropic SDK
            import anthropic
            client_kwargs = {"api_key": api_key}
            if provider in ("minimax", "anthropic"):
                client_kwargs["base_url"] = base_url
            client = anthropic.Anthropic(**client_kwargs)
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
            )
            content_text = ""
            for block in response.content:
                if hasattr(block, 'text') and block.text:
                    content_text = block.text
                    break
            return {"choices": [{"message": {"content": content_text}}]}
    except Exception as e:
        return {"error": str(e)}
