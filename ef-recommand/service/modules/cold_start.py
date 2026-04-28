import random
from typing import List, Dict, Optional

import numpy as np
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer  # 如果需要独立使用


class ColdStartService:
    """
    模块4：冷启动与新用户处理模块（已优化）
    - 使用用户选择的 interestTags 生成真实向量
    - 复用 ContentFeatureService 的 300 维 TF-IDF 向量空间
    - 支持最小标签数量校验 + 兜底
    """

    def __init__(self, vectorDim: int = 300, seed: int = 42):  # 统一为300维
        self.vectorDim = vectorDim
        random.seed(seed)
        np.random.seed(seed)

        self.userTagVectors: Dict[int, np.ndarray] = {}
        self.postVectors: Dict[int, np.ndarray] = {}  # 将从 contentService 复制
        self.postPopularity: Dict[int, float] = {}
        self.vectorizer = None  # ← 新增：用于复用 TF-IDF vectorizer

    def setCandidatePosts(self, posts: List[Dict], content_vectors: Optional[Dict[int, np.ndarray]] = None):
        """加载候选视频向量（推荐从 contentService 传入真实向量）"""
        self.postVectors = {}
        self.postPopularity = {}

        if content_vectors:
            self.postVectors = content_vectors.copy()
        else:
            # 兜底：随机生成（仅测试用，生产应传入真实向量）
            for v in posts:
                vid = v.get('post_id') or v.get('postId')
                if vid is None:
                    continue
                vec = np.random.randn(self.vectorDim).astype(np.float32)
                vec /= (np.linalg.norm(vec) + 1e-8)
                self.postVectors[vid] = vec

        for vid in self.postVectors:
            self.postPopularity[vid] = random.betavariate(2, 5)

        print(f"✅ ColdStart setCandidatePosts 完成 | 视频数: {len(self.postVectors)} | 维度: {self.vectorDim}")

    def registerUser(self, userId: int, interestTags: List[str]):
        """基于用户选择的兴趣标签生成初始用户向量（最终强版本）"""
        if not interestTags or len(interestTags) < 3:
            print(f"⚠️ 用户{userId} 兴趣标签数量不足，使用兜底标签")
            interestTags = interestTags or ["科技", "生活", "娱乐"]

        # 构建高质量伪文档，针对每个标签重复更多次
        user_text = " ".join([tag * 8 for tag in interestTags])

        print(f"🔧 [ColdStart] 用户{userId} 处理标签: {interestTags}")

        try:
            # 优先复用 ContentFeatureService 的 vectorizer（最精准）
            if hasattr(self, 'vectorizer') and self.vectorizer is not None:
                tfidf_vec = self.vectorizer.transform([user_text]).toarray()[0]
                vec = np.array(tfidf_vec, dtype=np.float32)
                print(f"✅ 使用 TF-IDF vectorizer 生成用户向量")
            else:
                # 增强版词频映射
                words = jieba.lcut(user_text)
                word_counter = {}
                for w in words:
                    if len(w) >= 2:
                        word_counter[w] = word_counter.get(w, 0) + 8

                vec = np.zeros(self.vectorDim, dtype=np.float32)
                idx = 0
                for count in word_counter.values():
                    if idx + 12 < self.vectorDim:
                        vec[idx:idx + 12] = count * 1.5  # 加强权重
                        idx += 12

                # 添加适量噪声，避免过于稀疏
                noise = np.random.randn(self.vectorDim).astype(np.float32) * 0.08
                vec += noise

            # L2归一化
            norm = np.linalg.norm(vec)
            if norm > 1e-8:
                vec /= norm

            self.userTagVectors[userId] = vec.copy()

            print(f"✅ 用户{userId} 冷启动画像生成完成 | 标签: {interestTags} | 维度: {self.vectorDim}")
            return True

        except Exception as e:
            print(f"⚠️ registerUser 异常: {e}，使用随机增强兜底")
            vec = np.random.randn(self.vectorDim).astype(np.float32) * 0.5
            active = random.sample(range(self.vectorDim), min(120, self.vectorDim))
            vec[active] *= 6.0
            vec /= (np.linalg.norm(vec) + 1e-8)
            self.userTagVectors[userId] = vec.copy()
            return True

    def recommend(self, userId: int, topN: int = 12) -> List[Dict]:
        """冷启动推荐主逻辑"""
        if userId not in self.userTagVectors or not self.postVectors:
            print("⚠️ 冷启动向量未初始化，回退到热门推荐")
            return self._popularRecommendation(topN)

        userVec = self.userTagVectors[userId]
        scored = []

        for vid, postVec in self.postVectors.items():
            sim = self._cosineSimilarity(userVec, postVec)
            pop = self.postPopularity.get(vid, 0.3)
            finalScore = 0.82 * sim + 0.18 * pop  # 偏向兴趣匹配，同时保留一定探索性

            reason = "兴趣标签匹配"
            if sim > 0.48:
                reason = "强兴趣匹配"
            elif sim > 0.30:
                reason = "相关兴趣匹配"

            scored.append({
                "post_id": vid,
                "score": round(finalScore, 4),
                "sim": round(sim, 4),
                "reason": reason
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        mainRecs = scored[:max(8, topN - 2)]

        # 补充探索推荐（避免过于集中，符合破解信息茧房）
        exploreList = self._getExplorePosts(num=topN - len(mainRecs),
                                            excludeIds=[x["post_id"] for x in mainRecs])

        for item in exploreList:
            item["score"] = round(item["score"] * 0.45, 4)
            item["reason"] = "探索推荐（破圈）"

        finalList = mainRecs + exploreList
        finalList.sort(key=lambda x: x["score"], reverse=True)
        return finalList[:topN]

    # 以下方法保持基本不变（可微调）
    def _popularRecommendation(self, topN: int = 12) -> List[Dict]:
        popular = sorted(self.postPopularity.items(), key=lambda x: x[1], reverse=True)
        return [{"post_id": vid, "score": round(score, 4), "sim": 0.0, "reason": "平台热门"}
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
