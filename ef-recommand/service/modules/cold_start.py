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

    # ====================== 新增：冷启动兴趣标签提取逻辑 ======================
    def extract_cold_start_tags(self, videos: List[Dict], limit: int = 50) -> List[str]:
        """
        从视频列表中提取高质量兴趣标签（核心业务逻辑）
        放在 ColdStartService 中最合适
        """
        import re
        from collections import Counter
        import jieba
        import jieba.analyse

        if not videos or len(videos) == 0:
            print("⚠️ [ColdStartService] 视频数据为空，返回默认标签")
            default_tags = ["科技", "生活", "娱乐", "美食", "旅行", "教育", "音乐", "电影", "游戏", "体育",
                            "时尚", "健康", "汽车", "财经", "新闻", "AI", "编程", "摄影", "短视频", "动画"]
            return default_tags[:limit]

        print(f"✅ [ColdStartService] 开始从 {len(videos)} 个视频提取兴趣标签...")

        # 1. 准备语料和全局词频
        all_texts: List[str] = []
        global_word_counter = Counter()

        for v in videos:
            title = str(v.get('title') or v.get('Title') or "")
            desc = str(v.get('description') or v.get('desc') or v.get('Description') or "")
            tags_str = str(v.get('tags') or v.get('Tags') or v.get('category') or v.get('Category') or "")

            combined = f"{title} {desc} {tags_str}".strip()
            if not combined:
                continue

            all_texts.append(combined)

            # 全局词频辅助
            words = jieba.lcut(combined)
            filtered = [w for w in words if len(w) >= 2 and not re.match(r'^\d+$', w)]
            global_word_counter.update(filtered)

        if not all_texts:
            print("⚠️ [ColdStartService] 无有效文本，使用默认标签")
            return ["科技", "生活", "娱乐", "美食", "旅行", "教育"][:limit]

        # 2. TF-IDF 提取关键词
        corpus_text = " ".join(all_texts)

        tfidf_keywords = jieba.analyse.extract_tags(
            corpus_text,
            topK=limit * 4,
            withWeight=True,
            allowPOS=('n', 'vn', 'nr', 'ns', 'nt', 'nz', 'l')
        )

        # 3. 综合评分排序（TF-IDF + 全局频率）
        candidate_tags = []
        seen = set()

        for word, tfidf_score in tfidf_keywords:
            if word in seen or len(word) < 2:
                continue
            freq = global_word_counter.get(word, 1)
            score = tfidf_score * 0.75 + (freq / max(1, len(videos))) * 0.25
            candidate_tags.append((word, score))
            seen.add(word)

        # 4. 兜底补充高频词
        for word, freq in global_word_counter.most_common(limit * 3):
            if word not in seen and len(word) >= 2 and not re.match(r'^\d+$', word):
                score = freq / max(1, len(videos)) * 0.6
                candidate_tags.append((word, score))
                seen.add(word)

        # 5. 最终返回
        candidate_tags.sort(key=lambda x: x[1], reverse=True)
        final_tags = [tag for tag, _ in candidate_tags[:limit]]

        print(f"✅ [ColdStartService] 标签提取完成 → 返回 {len(final_tags)} 个标签")
        return final_tags
