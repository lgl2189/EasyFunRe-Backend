import random
from typing import List, Dict

import numpy as np


class ColdStartService:
    """
    模块4：冷启动与新用户处理模块
    """

    def __init__(self, vectorDim: int = 50, seed: int = 42):
        self.vectorDim = vectorDim
        random.seed(seed)
        np.random.seed(seed)

        self.userTagVectors: Dict[int, np.ndarray] = {}
        self.postVectors: Dict[int, np.ndarray] = {}
        self.postCategory: Dict[int, str] = {}
        self.postPopularity: Dict[int, float] = {}

    def setCandidatePosts(self, posts: List[Dict]):
        """加载候选视频"""
        self.postVectors = {}
        self.postCategory = {}
        self.postPopularity = {}

        for v in posts:
            vid = v.get('post_id')
            if vid is None:
                continue

            vec = np.random.randn(self.vectorDim).astype(np.float32)
            vec /= (np.linalg.norm(vec) + 1e-8)

            if random.random() < 0.35:
                self.postCategory[vid] = "tech"
                active = random.sample(range(self.vectorDim), 18)
                vec[active] *= 2.2
                vec /= (np.linalg.norm(vec) + 1e-8)
            else:
                self.postCategory[vid] = "other"

            self.postVectors[vid] = vec
            self.postPopularity[vid] = random.betavariate(2, 5)

    def registerUser(self, userId: int, interestTags: List[str]):
        """新用户注册"""
        vec = np.random.randn(self.vectorDim).astype(np.float32) * 0.6
        activeDims = random.sample(range(self.vectorDim), 22)
        vec[activeDims] *= 4.8
        vec /= (np.linalg.norm(vec) + 1e-8)

        self.userTagVectors[userId] = vec.copy()
        return True

    def dislikePost(self, userId: int, postId: int, strength: float = 0.75):
        """负反馈机制"""
        if userId not in self.userTagVectors or postId not in self.postVectors:
            return False

        userVec = self.userTagVectors[userId].copy()
        postVec = self.postVectors[postId]
        sim = self._cosineSimilarity(userVec, postVec)

        if sim < 0.12:
            return False

        adjustment = strength * sim * postVec
        userVec -= adjustment
        userVec /= (np.linalg.norm(userVec) + 1e-8)

        self.userTagVectors[userId] = userVec
        return True

    def recommend(self, userId: int, topN: int = 12) -> List[Dict]:
        """冷启动推荐"""
        if userId not in self.userTagVectors:
            return self._popularRecommendation(topN)

        userVec = self.userTagVectors[userId]
        scored = []

        for vid, postVec in self.postVectors.items():
            sim = self._cosineSimilarity(userVec, postVec)
            pop = self.postPopularity.get(vid, 0.3)
            finalScore = 0.87 * sim + 0.13 * pop

            reason = "弱匹配"
            if sim > 0.42:
                reason = "强兴趣匹配"
            elif sim > 0.25:
                reason = "兴趣匹配"
            if self.postCategory.get(vid) == "tech" and sim > 0.25:
                reason += " (tech)"

            scored.append({
                "post_id": vid,
                "score": round(finalScore, 4),
                "sim": round(sim, 4),
                "reason": reason
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        mainRecs = scored[:max(10, topN - 2)]

        exploreList = self._getExplorePosts(num=topN - len(mainRecs),
                                            excludeIds=[x["post_id"] for x in mainRecs])

        for item in exploreList:
            item["score"] = round(item["score"] * 0.52, 4)
            item["sim"] = 0.0
            item["reason"] = "探索推荐"

        finalList = mainRecs + exploreList
        finalList.sort(key=lambda x: x["score"], reverse=True)
        return finalList[:topN]

    def _popularRecommendation(self, topN: int = 12) -> List[Dict]:
        popular = sorted(self.postPopularity.items(), key=lambda x: x[1], reverse=True)
        return [{"post_id": vid, "score": round(score, 4), "sim": 0.0, "reason": "平台热门"}
                for vid, score in popular[:topN]]

    def _getExplorePosts(self, num: int = 2, excludeIds=None):
        if excludeIds is None:
            excludeIds = []
        candidates = [vid for vid in self.postVectors if vid not in excludeIds]
        random.shuffle(candidates)
        return [{
            "post_id": vid,
            "score": round(random.uniform(0.48, 0.65), 4),
            "reason": "探索推荐"
        } for vid in candidates[:num]]

    def _cosineSimilarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)