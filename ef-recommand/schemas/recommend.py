from typing import List

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: int
    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="CF权重 (0=纯内容, 1=纯CF)")
    w_div: float = Field(default=0.2, ge=0.0, le=1.0, description="多样性权重")
    w_bound: float = Field(default=0.1, ge=0.0, le=1.0, description="破圈/探索强度")
    top_n: int = Field(default=12, ge=1, le=50)

class RecommendItem(BaseModel):
    video_id: int
    final_score: float
    hybrid_score: float
    reason: str = ""

class RecommendResponse(BaseModel):
    user_id: int
    items: List[RecommendItem]
    is_cold_start: bool
    message: str = ""