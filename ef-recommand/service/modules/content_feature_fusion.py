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
        self.actualDim = targetDim  # 默认初始化为目标维度

    def buildPostVectors(self, posts: List[Dict]):
        """构建视频内容向量 - 强制固定维度为 targetDim，避免 shape mismatch"""
        if not posts:
            print("⚠️ buildPostVectors: 没有传入视频数据，使用空向量")
            self.postVectors = {}
            self.actualDim = self.targetDim
            return self.targetDim

        texts = [f"{v.get('title','')} {v.get('tags','')} {v.get('category','')}" for v in posts]
        postIds = [v['post_id'] for v in posts if v.get('post_id') is not None]

        # TF-IDF 向量化
        tfidfMatrix = self.vectorizer.fit_transform(texts)
        vectors = normalize(tfidfMatrix, norm='l2').toarray()

        actual_dim = vectors.shape[1]

        # === 关键修复：强制对齐到 targetDim ===
        if actual_dim < self.targetDim:
            padded = np.zeros((len(posts), self.targetDim), dtype=np.float32)
            padded[:, :actual_dim] = vectors
            vectors = padded
            print(f"✅ buildPostVectors: 实际维度 {actual_dim} → 补零扩展到 {self.targetDim}")
        elif actual_dim > self.targetDim:
            vectors = vectors[:, :self.targetDim]
            print(f"⚠️ buildPostVectors: 实际维度 {actual_dim} → 截断到 {self.targetDim}")

        self.actualDim = self.targetDim

        # 保存向量
        self.postVectors = {}
        for vid, vec in zip(postIds, vectors):
            self.postVectors[vid] = vec.astype(np.float32)

        print(f"✅ buildPostVectors 完成 | 视频数量: {len(posts)} | 固定维度: {self.targetDim}")
        return self.targetDim

    def updateUserProfile(self, userId: int, interactions: List[Tuple[int, float]]):
        """
        更新用户内容画像（修改版：支持传入完整历史交互）
        核心变更：
        - 移除 0.4历史画像 + 0.6新交互 的增量融合逻辑
        - 直接基于传入的完整 interactions 计算用户画像
        - 若 interactions 为空，保持现有画像不变（避免清空历史）
        """
        # 1. 初始化：用户无历史画像时创建零向量
        if userId not in self.userProfiles:
            self.userProfiles[userId] = np.zeros(self.actualDim, dtype=np.float32)

        # 2. 基于传入的完整交互计算聚合向量
        newVec = np.zeros(self.actualDim, dtype=np.float32)
        totalWeight = 0.0

        for vid, weight in interactions:
            # 防御性检查：视频必须有向量且维度一致
            if vid in self.postVectors:
                vec = self.postVectors[vid]
                if len(vec) != self.actualDim:
                    continue
                # 保留原有的权重放大逻辑：正反馈×3，负反馈×2.5
                adjustedWeight = weight * (3.0 if weight > 0 else 2.5)
                newVec += vec * adjustedWeight
                totalWeight += abs(adjustedWeight)

        # 3. 更新画像逻辑
        if totalWeight > 0:
            # 有有效交互：直接用完整交互的聚合向量作为新画像
            newVec /= totalWeight
            profile = newVec
            # 保留原有的L2归一化
            norm = np.linalg.norm(profile)
            if norm > 1e-8:
                profile /= norm
            self.userProfiles[userId] = profile
        else:
            # 无有效交互：保持现有画像不变（避免每次空交互都重置为零向量）
            pass

    def getContentScores(self, userId: int, candidateSize: int = 150, exclude_post_ids: set = None) -> Dict[int, float]:
        """
        获取内容相似度分数（修改版：支持过滤已交互视频）
        新增参数：
        - exclude_post_ids: 需要排除的已交互视频ID集合
        """
        if userId not in self.userProfiles or not self.postVectors:
            return {}
        userVec = self.userProfiles[userId]
        if len(userVec) != self.actualDim:
            print(f"⚠️ 用户画像维度异常: {len(userVec)} != {self.actualDim}")
            return {}

        # 初始化排除集合
        if exclude_post_ids is None:
            exclude_post_ids = set()

        # 计算所有视频的相似度（跳过已交互视频）
        scored = []
        for vid, vec in self.postVectors.items():
            if vid in exclude_post_ids:  # 新增：过滤已交互视频
                continue
            if len(vec) != len(userVec):
                continue
            sim = float(np.dot(userVec, vec))
            scored.append((vid, sim))

        # 按相似度降序排序，取前 candidateSize 个
        scored.sort(key=lambda x: x[1], reverse=True)
        top_scores = scored[:candidateSize]
        scores = {vid: sim for vid, sim in top_scores if sim > 0.01}
        print(
            f"✅ getContentScores 返回 Top-{len(scores)}（已过滤 {len(exclude_post_ids)} 个已交互视频，最高 sim={max(scores.values()) if scores else 0:.4f}）")
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