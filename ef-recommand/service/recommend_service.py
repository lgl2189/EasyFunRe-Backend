import random
import numpy as np
import jieba
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from schemas.recommend import RecommendRequest, RecommendItem
from service.client.recommend_client import recommend_client  # 你提供的客户端


# ====================== BPR 协同过滤（模块1） ======================
@dataclass
class BPRModel:
    """简化版 BPR 模型存储结构（离线训练后加载）"""
    user_factors: np.ndarray
    item_factors: np.ndarray
    user_bias: np.ndarray
    item_bias: np.ndarray
    global_bias: float
    n_users: int
    n_videos: int


class RecommendService:
    def __init__(self, vector_dim: int = 50, content_dim: int = 300, cold_theta: int = 10):
        self.vector_dim = vector_dim
        self.content_dim = content_dim
        self.cold_theta = cold_theta

        # ====================== 数据存储 ======================
        self.video_vectors: Dict[int, np.ndarray] = {}  # CF 简单向量（冷启动用）
        self.video_content_vectors: Dict[int, np.ndarray] = {}  # TF-IDF 内容向量
        self.video_category: Dict[int, str] = {}
        self.video_popularity: Dict[int, float] = {}
        self.video_meta: Dict[int, Dict] = {}  # 视频元数据缓存

        # 用户数据
        self.user_interaction_count: Dict[int, int] = {}
        self.user_tag_vectors: Dict[int, np.ndarray] = {}  # 冷启动画像（模块4）
        self.user_content_profiles: Dict[int, np.ndarray] = {}  # 内容画像（模块2）

        # 协同过滤模型（模块1）
        self.bpr_model: BPRModel | None = None

        # 初始化
        self._init_mock_videos()
        jieba.initialize()  # 初始化分词

    # ====================== 初始化模拟数据 ======================
    def _init_mock_videos(self):
        random.seed(42)
        np.random.seed(42)
        for vid in range(1, 501):
            # CF 向量
            vec = np.random.randn(self.vector_dim).astype(np.float32)
            vec /= (np.linalg.norm(vec) + 1e-8)
            self.video_vectors[vid] = vec

            self.video_popularity[vid] = random.betavariate(2, 5)
            self.video_category[vid] = "tech" if random.random() < 0.35 else "other"

    # ====================== 微服务调用（使用独立客户端） ======================
    async def _load_videos_from_service(self):
        """从 video-service 加载视频元数据并构建内容向量"""
        videos = await recommend_client.get_all_videos_for_content()  # 或 get_videos_metadata()
        if not videos:
            # 开发阶段兜底
            videos = await recommend_client.get_mock_videos()

        self.video_meta = {v["video_id"]: v for v in videos}
        self._build_content_vectors(videos)

    def _build_content_vectors(self, videos: List[Dict]):
        """模块2：使用 jieba + TF-IDF 构建真实内容特征向量"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        print("正在构建内容特征向量（TF-IDF + jieba）...")

        texts = []
        video_ids = []
        for v in videos:
            text = f"{v.get('title', '')} {v.get('tags', '')} {v.get('category', '')}"
            texts.append(text)
            video_ids.append(v["video_id"])

        vectorizer = TfidfVectorizer(
            max_features=self.content_dim,
            tokenizer=lambda t: list(jieba.cut(t, cut_all=False)),
            token_pattern=None,
            min_df=1,
            max_df=0.85,
        )

        tfidf_matrix = vectorizer.fit_transform(texts)
        vectors = normalize(tfidf_matrix, norm='l2').toarray()

        for vid, vec in zip(video_ids, vectors):
            self.video_content_vectors[vid] = vec.astype(np.float32)

        print(f"内容向量构建完成！视频数量: {len(videos)} | 维度: {vectors.shape[1]}")

    # ====================== 模块1：协同过滤（BPR） ======================
    def load_bpr_model(self, user_factors: np.ndarray, item_factors: np.ndarray,
                       user_bias: np.ndarray, item_bias: np.ndarray,
                       global_bias: float, n_users: int, n_videos: int):
        """离线训练后调用此方法加载 BPR 模型"""
        self.bpr_model = BPRModel(
            user_factors=user_factors,
            item_factors=item_factors,
            user_bias=user_bias,
            item_bias=item_bias,
            global_bias=global_bias,
            n_users=n_users,
            n_videos=n_videos
        )
        print(f"BPR 模型加载成功 | 用户: {n_users} | 视频: {n_videos} | 隐因子: {user_factors.shape[1]}")

    def get_cf_scores(self, user_id: int, candidate_size: int = 80) -> Dict[int, float]:
        """模块1：使用 BPR 模型预测分数"""
        if not self.bpr_model or user_id >= self.bpr_model.n_users:
            # 模型未加载或用户超出范围 → 返回随机分数兜底
            return {vid: random.uniform(1.0, 8.5) for vid in list(self.video_vectors.keys())[:candidate_size]}

        user_vec = self.bpr_model.user_factors[user_id]
        u_bias = self.bpr_model.user_bias[user_id]

        scores = {}
        for vid in range(min(candidate_size, self.bpr_model.n_videos)):
            if vid >= len(self.bpr_model.item_factors):
                continue
            item_vec = self.bpr_model.item_factors[vid]
            i_bias = self.bpr_model.item_bias[vid]
            score = float(np.dot(user_vec, item_vec) + u_bias + i_bias + self.bpr_model.global_bias)
            scores[vid] = max(0.1, score)  # 避免负分过大

        # 简单缩放让最高分更合理
        if scores:
            max_score = max(scores.values())
            scale = 8.5 / max(1.0, max_score)
            for vid in scores:
                scores[vid] *= scale

        return scores

    # ====================== 模块4：冷启动与负反馈 ======================
    def register_user(self, user_id: int, interest_tags: List[str]):
        vec = np.random.randn(self.vector_dim).astype(np.float32) * 0.6
        active = random.sample(range(self.vector_dim), 22)
        vec[active] *= 4.8
        vec /= (np.linalg.norm(vec) + 1e-8)
        self.user_tag_vectors[user_id] = vec
        self.user_interaction_count[user_id] = 0
        print(f"用户 {user_id} 冷启动注册成功，兴趣标签: {interest_tags}")

    def add_interaction(self, user_id: int, count: int = 1):
        self.user_interaction_count[user_id] = self.user_interaction_count.get(user_id, 0) + count

    def dislike_video(self, user_id: int, video_id: int, strength: float = 0.75):
        """负反馈机制"""
        if user_id not in self.user_tag_vectors or video_id not in self.video_vectors:
            return
        user_vec = self.user_tag_vectors[user_id].copy()
        sim = self._cosine_sim(user_vec, self.video_vectors[video_id])
        if sim < 0.12:
            return
        adjustment = strength * sim * self.video_vectors[video_id]
        user_vec -= adjustment
        user_vec /= (np.linalg.norm(user_vec) + 1e-8)
        self.user_tag_vectors[user_id] = user_vec
        print(f"✓ 负反馈应用：用户 {user_id} 不喜欢视频 {video_id} (sim={sim:.4f})")

    def is_cold_start(self, user_id: int) -> bool:
        return self.user_interaction_count.get(user_id, 0) < self.cold_theta

    def _cold_start_recommend(self, user_id: int, top_n: int) -> List[Dict]:
        """模块4：冷启动推荐"""
        if user_id not in self.user_tag_vectors:
            popular = sorted(self.video_popularity.items(), key=lambda x: x[1], reverse=True)
            return [{"video_id": vid, "score": score, "reason": "平台热门"}
                    for vid, score in popular[:top_n]]

        user_vec = self.user_tag_vectors[user_id]
        scored = []
        for vid, vvec in self.video_vectors.items():
            sim = self._cosine_sim(user_vec, vvec)
            pop = self.video_popularity.get(vid, 0.3)
            score = 0.87 * sim + 0.13 * pop
            reason = "强兴趣匹配" if sim > 0.42 else "兴趣匹配" if sim > 0.25 else "弱匹配"
            if self.video_category.get(vid) == "tech" and sim > 0.25:
                reason += " (tech)"
            scored.append({"video_id": vid, "score": score, "reason": reason})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    # ====================== 模块2：内容特征 ======================
    def update_content_profile(self, user_id: int, interactions: List[Tuple[int, float]]):
        """更新用户内容画像"""
        if user_id not in self.user_content_profiles:
            self.user_content_profiles[user_id] = np.zeros(self.content_dim, dtype=np.float32)

        profile = self.user_content_profiles[user_id]
        new_vec = np.zeros(self.content_dim, dtype=np.float32)
        total_weight = 0.0

        for vid, weight in interactions:
            if vid in self.video_content_vectors:
                w = weight * (3.0 if weight > 0 else 2.0)
                new_vec += self.video_content_vectors[vid] * w
                total_weight += abs(w)

        if total_weight > 0:
            new_vec /= total_weight
            profile = 0.4 * profile + 0.6 * new_vec
            norm = np.linalg.norm(profile)
            if norm > 1e-8:
                profile /= norm
            self.user_content_profiles[user_id] = profile

    def get_content_scores(self, user_id: int, candidate_size: int = 60) -> Dict[int, float]:
        if user_id not in self.user_content_profiles or not self.video_content_vectors:
            return {}
        user_vec = self.user_content_profiles[user_id]
        scores = {}
        for vid, vec in list(self.video_content_vectors.items())[:candidate_size]:
            sim = float(np.dot(user_vec, vec))
            if sim > 0.01:
                scores[vid] = sim
        return scores

    # ====================== 模块3：融合与用户可控 ======================
    def _normalize(self, scores: Dict[int, float]) -> Dict[int, float]:
        if not scores:
            return {}
        min_v, max_v = min(scores.values()), max(scores.values())
        if max_v == min_v:
            return {k: 0.5 for k in scores}
        return {k: (v - min_v) / (max_v - min_v + 1e-8) for k, v in scores.items()}

    def _cosine_sim(self, v1: np.ndarray, v2: np.ndarray) -> float:
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

    def fuse_and_recommend(self, req: RecommendRequest) -> List[RecommendItem]:
        """核心融合逻辑（模块3）"""
        cf_scores = self.get_cf_scores(req.user_id)
        content_scores = self.get_content_scores(req.user_id)

        norm_cf = self._normalize(cf_scores)
        norm_content = self._normalize(content_scores)

        all_vids = set(norm_cf.keys()) | set(norm_content.keys())
        fused = {}
        for vid in all_vids:
            s_cf = norm_cf.get(vid, 0.0)
            s_ct = norm_content.get(vid, 0.0)
            base = req.alpha * s_cf + (1.0 - req.alpha) * s_ct
            bonus = req.w_bound * (1.0 - s_ct) * 0.5
            fused[vid] = base + bonus

        # MMR 简化版重排序
        lambda_val = 1.0 - req.w_div
        sorted_list = sorted(fused.items(), key=lambda x: x[1], reverse=True)

        selected = []
        for vid, h_score in sorted_list[:req.top_n]:
            selected.append(RecommendItem(
                video_id=vid,
                final_score=round(h_score * lambda_val, 4),
                hybrid_score=round(h_score, 4),
                reason="混合推荐"
            ))
        return selected

    # ====================== 统一推荐入口 ======================
    async def get_recommendations(self, req: RecommendRequest) -> Dict[str, Any]:
        user_id = req.user_id

        # 首次加载视频内容向量
        if not self.video_content_vectors:
            await self._load_videos_from_service()

        # 更新交互次数
        self.add_interaction(user_id)

        # 获取用户交互历史（用于内容画像更新）
        interactions = await recommend_client.get_user_interactions(user_id)
        if interactions:
            self.update_content_profile(user_id, interactions)

        # 冷启动判断
        if self.is_cold_start(user_id):
            recs = self._cold_start_recommend(user_id, req.top_n)
            items = [
                RecommendItem(
                    video_id=item["video_id"],
                    final_score=round(item["score"], 4),
                    hybrid_score=round(item["score"], 4),
                    reason=item.get("reason", "冷启动推荐")
                ) for item in recs
            ]
            return {
                "user_id": user_id,
                "items": items,
                "is_cold_start": True,
                "message": "冷启动阶段 - 基于注册兴趣标签推荐"
            }

        # 非冷启动：执行模块3融合推荐
        items = self.fuse_and_recommend(req)
        return {
            "user_id": user_id,
            "items": items,
            "is_cold_start": False,
            "message": f"混合推荐完成 (α={req.alpha:.2f}, 多样性={req.w_div:.2f}, 破圈={req.w_bound:.2f})"
        }