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
    userTagList: List["RecommendTagItem"] = []

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


# schemas/recommend.py  在 ColdStartTagsResponse 之后添加

class RecommendTagItem(BaseModel):
    """
    单个冷启动标签项，与 Java 的 RecommendTagDTO 对应
    """
    tagName: str

    class Config:
        populate_by_name = True