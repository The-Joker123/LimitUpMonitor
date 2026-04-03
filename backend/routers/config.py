from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/api", tags=["config"])

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/config")
def get_config():
    """获取配置（AI key 除外）"""
    config = load_config()
    # 不返回明文 API Key
    if "ai" in config:
        config["ai"]["apiKey"] = ""
    return config


@router.post("/config/ai")
def update_ai_config(provider: str, api_key: str, base_url: str, model: str):
    """更新 AI 配置"""
    config = load_config()
    if "ai" not in config:
        config["ai"] = {}
    config["ai"]["provider"] = provider
    config["ai"]["apiKey"] = api_key
    config["ai"]["baseUrl"] = base_url
    config["ai"]["model"] = model
    save_config(config)
    return {"status": "ok"}
