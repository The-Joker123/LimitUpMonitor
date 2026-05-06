from fastapi import APIRouter, HTTPException
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api", tags=["config"])

CONFIG_PATH = Path(os.getenv("CONFIG_FILE", str(Path(__file__).parent.parent.parent / "config.json")))


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def get_admin_password():
    pw = os.getenv("ADMIN_PASSWORD", "")
    if pw:
        return pw
    return load_config().get("adminPassword", "")


@router.get("/config")
def get_config():
    """获取配置（AI key 和管理密码除外）"""
    config = load_config()
    if "ai" in config:
        config["ai"]["apiKey"] = ""
    config.pop("adminPassword", None)
    return config


@router.post("/config/ai")
def update_ai_config(provider: str, api_key: str, base_url: str, model: str, admin_password: str = ""):
    """更新 AI 配置（需要管理密码）"""
    expected = get_admin_password()
    if expected and admin_password != expected:
        raise HTTPException(status_code=403, detail="管理密码错误")

    config = load_config()
    if "ai" not in config:
        config["ai"] = {}
    config["ai"]["provider"] = provider
    config["ai"]["apiKey"] = api_key
    config["ai"]["baseUrl"] = base_url
    config["ai"]["model"] = model
    save_config(config)
    return {"status": "ok"}
