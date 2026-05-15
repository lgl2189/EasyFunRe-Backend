import random
from typing import List, Dict, Optional

import numpy as np
import jieba
from collections import Counter
import re


class ColdStartService:
    """
    模块4：冷启动与新用户处理模块
    """

    def __init__(self, vectorDim: int = 300, seed: int = 42):
        self.vectorDim = vectorDim
        random.seed(seed)
        np.random.seed(seed)

        self.userTagVectors: Dict[int, np.ndarray] = {}
        self.postVectors: Dict[int, np.ndarray] = {}
        self.postPopularity: Dict[int, float] = {}
        self.vectorizer = None

    def setCandidatePosts(self, posts: List[Dict], content_vectors: Optional[Dict[int, np.ndarray]] = None):
        """加载候选视频向量"""
        self.postVectors = {}
        self.postPopularity = {}

        if content_vectors:
            self.postVectors = content_vectors.copy()
        else:
            for v in posts:
                vid = v.get('post_id') or v.get('postId')
                if vid is None:
                    continue
                vec = np.random.randn(self.vectorDim).astype(np.float32)
                vec /= (np.linalg.norm(vec) + 1e-8)
                self.postVectors[vid] = vec

        for vid in self.postVectors:
            self.postPopularity[vid] = random.betavariate(2, 5)

    def registerUser(self, userId: int, interestTags: List[str]):
        """基于兴趣标签生成初始用户向量"""
        if not interestTags or len(interestTags) < 3:
            interestTags = interestTags or ["科技", "生活", "娱乐"]

        user_text = " ".join([tag * 8 for tag in interestTags])

        try:
            if self.vectorizer is not None:
                tfidf_vec = self.vectorizer.transform([user_text]).toarray()[0]
                vec = np.array(tfidf_vec, dtype=np.float32)
            else:
                # 兜底逻辑
                vec = np.random.randn(self.vectorDim).astype(np.float32) * 0.5
                active = random.sample(range(self.vectorDim), min(120, self.vectorDim))
                vec[active] *= 6.0

            norm = np.linalg.norm(vec)
            if norm > 1e-8:
                vec /= norm

            self.userTagVectors[userId] = vec.copy()
            return True

        except Exception:
            # 最终兜底
            vec = np.random.randn(self.vectorDim).astype(np.float32) * 0.5
            active = random.sample(range(self.vectorDim), min(120, self.vectorDim))
            vec[active] *= 6.0
            vec /= (np.linalg.norm(vec) + 1e-8)
            self.userTagVectors[userId] = vec.copy()
            return True

    def recommend(self, userId: int, topN: int = 12) -> List[Dict]:
        """冷启动推荐主逻辑"""
        if userId not in self.userTagVectors or not self.postVectors:
            return self._popularRecommendation(topN)

        userVec = self.userTagVectors[userId]
        scored = []

        for vid, postVec in self.postVectors.items():
            sim = self._cosineSimilarity(userVec, postVec)
            pop = self.postPopularity.get(vid, 0.3)
            finalScore = 0.82 * sim + 0.18 * pop

            reason = "兴趣标签匹配"
            if sim > 0.48:
                reason = "强兴趣匹配"
            elif sim > 0.30:
                reason = "相关兴趣匹配"

            scored.append({
                "post_id": vid,
                "score": round(finalScore, 4),
                "reason": reason
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        mainRecs = scored[:max(8, topN - 2)]

        exploreList = self._getExplorePosts(num=topN - len(mainRecs),
                                            excludeIds=[x["post_id"] for x in mainRecs])

        for item in exploreList:
            item["score"] = round(item["score"] * 0.45, 4)
            item["reason"] = "探索推荐（破圈）"

        finalList = mainRecs + exploreList
        finalList.sort(key=lambda x: x["score"], reverse=True)
        return finalList[:topN]

    def _popularRecommendation(self, topN: int = 12) -> List[Dict]:
        popular = sorted(self.postPopularity.items(), key=lambda x: x[1], reverse=True)
        return [{"post_id": vid, "score": round(score, 4), "reason": "平台热门"}
                for vid, score in popular[:topN]]

    def _getExplorePosts(self, num: int = 3, excludeIds=None):
        if excludeIds is None:
            excludeIds = []
        candidates = [vid for vid in self.postVectors if vid not in excludeIds]
        random.shuffle(candidates)
        return [{
            "post_id": vid,
            "score": round(random.uniform(0.45, 0.68), 4),
            "reason": "探索推荐"
        } for vid in candidates[:num]]

    def _cosineSimilarity(self, v1, v2):
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

    def extract_cold_start_tags(self, videos: List[Dict], limit: int = 50) -> List[str]:
        """从视频列表中提取冷启动兴趣标签"""
        if not videos or len(videos) == 0:
            return ["科技", "生活", "娱乐", "美食", "旅行", "教育", "音乐", "电影", "游戏", "体育"][:limit]

        all_texts: List[str] = []
        global_word_counter = Counter()

        for v in videos:
            title = str(v.get('title') or "")
            desc = str(v.get('description') or v.get('desc') or "")
            tags_str = str(v.get('tags') or v.get('category') or "")

            combined = f"{title} {desc} {tags_str}".strip()
            if not combined:
                continue

            all_texts.append(combined)
            words = jieba.lcut(combined)
            filtered = [w for w in words if len(w) >= 2 and not re.match(r'^\d+$', w)]
            global_word_counter.update(filtered)

        if not all_texts:
            return ["科技", "生活", "娱乐", "美食", "旅行", "教育"][:limit]

        corpus_text = " ".join(all_texts)
        tfidf_keywords = jieba.analyse.extract_tags(
            corpus_text, topK=limit * 4, withWeight=True,
            allowPOS=('n', 'vn', 'nr', 'ns', 'nt', 'nz', 'l')
        )

        candidate_tags = []
        seen = set()
        for word, tfidf_score in tfidf_keywords:
            if word in seen or len(word) < 2:
                continue
            freq = global_word_counter.get(word, 1)
            score = tfidf_score * 0.75 + (freq / max(1, len(videos))) * 0.25
            candidate_tags.append((word, score))
            seen.add(word)

        for word, freq in global_word_counter.most_common(limit * 3):
            if word not in seen and len(word) >= 2 and not re.match(r'^\d+$', word):
                score = freq / max(1, len(videos)) * 0.6
                candidate_tags.append((word, score))
                seen.add(word)

        candidate_tags.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in candidate_tags[:limit]]