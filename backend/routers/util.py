from fastapi import APIRouter
import requests

router = APIRouter(prefix="/api", tags=["util"])


@router.get("/translate")
def translate_text(text: str, from_lang: str = "en", to_lang: str = "zh"):
    """
    翻译文本（使用 MyMemory 免费翻译API）
    """
    try:
        lang_pair = f"{from_lang}|{to_lang}"
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": lang_pair}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("responseStatus") == 200:
            return {
                "translation": data.get("responseData", {}).get("translatedText", text)
            }
        else:
            return {"error": data.get("responseDetails", "翻译失败")}
    except Exception as e:
        return {"error": str(e)}
