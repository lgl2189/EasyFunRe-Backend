import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import jieba
from typing import List, Dict, Tuple
import os


class ContentFeatureService:
    """
    模块2：内容特征融合模块
    """

    def __init__(self, targetDim: int = 300):
        self.targetDim = targetDim

        # jieba 初始化
        projectRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cacheDir = os.path.join(projectRoot, "cache")
        os.makedirs(cacheDir, exist_ok=True)

        jieba.dt.tmp_dir = cacheDir
        jieba.dt.cache_file = os.path.join(cacheDir, "jieba.cache")
        jieba.initialize()

        self.vectorizer = TfidfVectorizer(
            max_features=targetDim,
            tokenizer=lambda t: list(jieba.cut(t, cut_all=False)),
            token_pattern=None,
            min_df=1,
            max_df=0.8,
        )

        self.postVectors: Dict[int, np.ndarray] = {}
        self.userProfiles: Dict[int, np.ndarray] = {}
        self.actualDim = targetDim

    def buildPostVectors(self, posts: List[Dict]):
        """构建视频内容向量"""
        if not posts:
            self.postVectors = {}
            self.actualDim = self.targetDim
            return self.targetDim

        texts = [f"{v.get('title','')} {v.get('tags','')} {v.get('category','')}" for v in posts]
        postIds = [v['post_id'] for v in posts if v.get('post_id') is not None]

        tfidfMatrix = self.vectorizer.fit_transform(texts)
        vectors = normalize(tfidfMatrix, norm='l2').toarray()

        actual_dim = vectors.shape[1]

        # 维度对齐
        if actual_dim < self.targetDim:
            padded = np.zeros((len(posts), self.targetDim), dtype=np.float32)
            padded[:, :actual_dim] = vectors
            vectors = padded
        elif actual_dim > self.targetDim:
            vectors = vectors[:, :self.targetDim]

        self.actualDim = self.targetDim

        self.postVectors = {}
        for vid, vec in zip(postIds, vectors):
            self.postVectors[vid] = vec.astype(np.float32)

        return self.targetDim

    def updateUserProfile(self, userId: int, interactions: List[Tuple[int, float]]):
        """更新用户内容画像"""
        if userId not in self.userProfiles:
            self.userProfiles[userId] = np.zeros(self.actualDim, dtype=np.float32)

        newVec = np.zeros(self.actualDim, dtype=np.float32)
        totalWeight = 0.0

        for vid, weight in interactions:
            if vid in self.postVectors:
                vec = self.postVectors[vid]
                if len(vec) != self.actualDim:
                    continue
                adjustedWeight = weight * (3.0 if weight > 0 else 2.5)
                newVec += vec * adjustedWeight
                totalWeight += abs(adjustedWeight)

        if totalWeight > 0:
            newVec /= totalWeight
            norm = np.linalg.norm(newVec)
            if norm > 1e-8:
                newVec /= norm
            self.userProfiles[userId] = newVec

    def getContentScores(self, userId: int, candidateSize: int = 150, exclude_post_ids: set = None) -> Dict[int, float]:
        """获取内容相似度分数"""
        if userId not in self.userProfiles or not self.postVectors:
            return {}

        userVec = self.userProfiles[userId]
        if exclude_post_ids is None:
            exclude_post_ids = set()

        scored = []
        for vid, vec in self.postVectors.items():
            if vid in exclude_post_ids:
                continue
            if len(vec) != len(userVec):
                continue
            sim = float(np.dot(userVec, vec))
            scored.append((vid, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_scores = scored[:candidateSize]
        scores = {vid: sim for vid, sim in top_scores if sim > 0.01}
        return scores

    def contentSimilarity(self, userId: int, postId: int) -> float:
        """单视频内容相似度"""
        if userId not in self.userProfiles or postId not in self.postVectors:
            return 0.0

        userVec = self.userProfiles[userId]
        vec = self.postVectors[postId]

        if len(userVec) != len(vec):
            return 0.0

        return float(np.dot(userVec, vec))