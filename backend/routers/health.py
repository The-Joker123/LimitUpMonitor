from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}
