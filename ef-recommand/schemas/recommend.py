# schemas/recommend.py
from pydantic import BaseModel
from typing import List, Optional, Any, Dict


class ContentPostDBO(BaseModel):
    postId: Optional[int] = None
    title: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None

    class Config:
        populate_by_name = True


class ContentInteractionRecordDBO(BaseModel):
    interactionId: Optional[int] = None
    ownerId: Optional[int] = None
    targetPostId: Optional[int] = None
    isLike: Optional[int] = None
    isDislike: Optional[int] = None

    class Config:
        populate_by_name = True


class RecommendRequestDTO(BaseModel):
    postList: List[ContentPostDBO] = []
    interactionList: List[ContentInteractionRecordDBO] = []

    class Config:
        populate_by_name = True


class RecommendItem(BaseModel):
    postId: int
    finalScore: float
    hybridScore: float
    reason: str


class RecommendResponse(BaseModel):
    userId: int
    recommendPostList: List[RecommendItem] = []
    isColdStart: bool
    message: str
    debugQueryParams: Dict[str, Any] = {}
    debugRequestBody: Dict[str, Any] = {}