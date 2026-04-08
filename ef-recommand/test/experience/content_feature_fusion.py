# content_feature_module_final.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import jieba
import random
import os
from typing import List, Dict, Tuple

# ====================== 关键修复：强制 jieba 缓存写入项目 data 目录 ======================
# 创建 data 目录（如果不存在）
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 设置 jieba 缓存路径到项目 data 目录
jieba_cache_file = os.path.join(DATA_DIR, "jieba.cache")
os.environ["JIEBA_CACHE_DIR"] = DATA_DIR   # 部分版本支持
jieba.dt.cache_file = jieba_cache_file     # 直接指定缓存文件路径

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# 初始化 jieba（现在会把缓存写到 ./data/jieba.cache）
jieba.initialize()
print(f"jieba 缓存已设置到项目目录: {jieba_cache_file}\n")

# ====================== 内容特征融合服务类（最终稳定版） ======================
class ContentFeatureService:
    """
    内容特征融合模块最终稳定版
    对应设计文档 Module 2
    """
    def __init__(self, target_dim=300):
        self.target_dim = target_dim
        self.vectorizer = TfidfVectorizer(
            max_features=target_dim,
            tokenizer=lambda t: list(jieba.cut(t, cut_all=False)),
            token_pattern=None,
            min_df=1,
            max_df=0.8,
        )
        self.video_vectors: Dict[int, np.ndarray] = {}
        self.user_profiles: Dict[int, np.ndarray] = {}
        self.actual_dim = None

    def build_video_vectors(self, videos: List[Dict]):
        print(f"正在为 {len(videos)} 个视频构建内容特征向量...")
        texts = [f"{v.get('title','')} {v.get('tags','')} {v.get('category','')}" for v in videos]
        video_ids = [v['video_id'] for v in videos]

        tfidf_matrix = self.vectorizer.fit_transform(texts)
        vectors = normalize(tfidf_matrix, norm='l2').toarray()
        self.actual_dim = vectors.shape[1]
        print(f"视频向量构建完成！实际维度: {self.actual_dim}\n")

        for vid, vec in zip(video_ids, vectors):
            self.video_vectors[vid] = vec.astype(np.float32)

    def update_user_profile(self, user_id: int, interactions: List[Tuple[int, float]]):
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = np.zeros(self.actual_dim, dtype=np.float32)

        profile = self.user_profiles[user_id]
        new_vec = np.zeros(self.actual_dim, dtype=np.float32)
        total_weight = 0.0

        for vid, weight in interactions:
            if vid in self.video_vectors:
                adjusted_weight = weight * (3.0 if weight > 0 else 2.5)
                new_vec += self.video_vectors[vid] * adjusted_weight
                total_weight += abs(adjusted_weight)

        if total_weight > 0:
            new_vec /= total_weight
            profile = 0.4 * profile + 0.6 * new_vec
            norm = np.linalg.norm(profile)
            if norm > 1e-8:
                profile /= norm
            self.user_profiles[user_id] = profile
            print(f"✓ 用户 {user_id} 内容画像更新完成")

    def content_similarity(self, user_id: int, video_id: int) -> float:
        if user_id not in self.user_profiles or video_id not in self.video_vectors:
            return 0.0
        return float(np.dot(self.user_profiles[user_id], self.video_vectors[video_id]))

    def get_content_scores(self, user_id: int, candidate_size: int = 15) -> Dict[int, float]:
        if user_id not in self.user_profiles:
            return {}

        user_vec = self.user_profiles[user_id]
        scores = {vid: float(np.dot(user_vec, vec))
                  for vid, vec in self.video_vectors.items()
                  if float(np.dot(user_vec, vec)) > 0.01}

        # 轻量MMR多样性
        final_scores = {}
        selected = []
        lambda_div = 0.18

        for _ in range(min(candidate_size, len(scores))):
            best_vid = None
            best_score = -np.inf
            for vid, raw_score in scores.items():
                if vid in selected:
                    continue
                diversity_penalty = sum(np.dot(self.video_vectors[vid], self.video_vectors[s])
                                      for s in selected) * lambda_div
                adjusted = raw_score - diversity_penalty
                if adjusted > best_score:
                    best_score = adjusted
                    best_vid = vid
            if best_vid:
                final_scores[best_vid] = round(best_score, 4)
                selected.append(best_vid)

        return dict(sorted(final_scores.items(), key=lambda x: x[1], reverse=True))


# ====================== 测试主程序 ======================
if __name__ == "__main__":
    # 生成模拟数据
    def generate_mock_videos(num=200):
        categories = ["科技", "生活", "游戏", "美食", "影视", "音乐", "财经", "教育", "汽车", "体育"]
        tags_pool = ["AI","机器学习","vlog","搞笑","游戏解说","美食教程","投资理财","编程",
                     "电影推荐","音乐","短视频","知识分享","健身","旅行","汽车"]
        videos = []
        for i in range(1, num + 1):
            cat = random.choice(categories)
            tags = random.sample(tags_pool, k=random.randint(3, 6))
            title = f"{random.choice(['爆款','超级','最新','2026','入门'])} {cat} {random.choice(tags)} 第{i}期"
            videos.append({"video_id": i, "title": title, "tags": ",".join(tags), "category": cat})
        return videos

    def generate_mock_interactions(videos, num=12):
        interacted = random.sample(videos, num)
        return [(v["video_id"], round(random.uniform(1.0, 2.8), 2) if random.random() < 0.75
                else round(random.uniform(-2.8, -1.0), 2)) for v in interacted]

    # 执行测试
    videos = generate_mock_videos(200)
    service = ContentFeatureService()

    service.build_video_vectors(videos)

    user_id = 10001
    interactions = generate_mock_interactions(videos, 12)

    print(f"\n用户 {user_id} 模拟交互行为：")
    for vid, w in interactions:
        title = next(v["title"] for v in videos if v["video_id"] == vid)
        sign = "👍" if w > 0 else "👎"
        print(f"  {sign} 视频 {vid:3d} | 权重 {w:6.2f} | {title[:55]}...")

    print("\n" + "="*90)
    service.update_user_profile(user_id, interactions)

    print("\n相似度验证：")
    for vid, w in interactions:
        sim = service.content_similarity(user_id, vid)
        print(f"视频 {vid:3d} (权重 {w:6.2f}) → 相似度 {sim:8.4f}")

    print("\n" + "="*90)
    scores = service.get_content_scores(user_id, candidate_size=15)

    print(f"用户 {user_id} 内容特征融合 Top 15 推荐：")
    print("排名\t视频ID\t分数\t标题")
    print("-" * 85)
    for rank, (vid, score) in enumerate(scores.items(), 1):
        title = next((v["title"] for v in videos if v["video_id"] == vid), "未知")
        print(f"{rank:2d}\t{vid:5d}\t{score:8.4f}\t{title[:60]}")

    print("\n=== 内容特征融合模块验证完成 ===")