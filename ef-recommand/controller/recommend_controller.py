from typing import List

from fastapi import APIRouter, Depends, HTTPException

from schemas.recommend import RecommendRequest, RecommendResponse
from service.recommend_service import RecommendService

router = APIRouter(prefix="/api/recommend", tags=["推荐服务"])

# 依赖注入
def get_recommend_service() -> RecommendService:
    return RecommendService()

@router.post("/", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    service: RecommendService = Depends(get_recommend_service)
):
    try:
        result = await service.get_recommendations(request)
        return RecommendResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐服务异常: {str(e)}")


# 管理接口（可选）
@router.post("/register")
async def register_user(
    user_id: int,
    interest_tags: List[str],
    service: RecommendService = Depends(get_recommend_service)
):
    service.register_user(user_id, interest_tags)
    return {"message": f"用户 {user_id} 注册成功，冷启动画像已初始化"}

@router.post("/dislike")
async def dislike(
    user_id: int,
    video_id: int,
    strength: float = 0.75,
    service: RecommendService = Depends(get_recommend_service)
):
    service.dislike_video(user_id, video_id, strength)
    return {"message": f"负反馈已应用：用户{user_id} 不喜欢视频{video_id}"}

@router.post("/interaction")
async def add_interaction(
    user_id: int,
    count: int = 1,
    service: RecommendService = Depends(get_recommend_service)
):
    service.add_interaction(user_id, count)
    return {"message": f"交互次数更新为 {service.user_interaction_count.get(user_id, 0)}"}