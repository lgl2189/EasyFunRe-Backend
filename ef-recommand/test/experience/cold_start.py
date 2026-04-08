import numpy as np
import random
from typing import List, Dict


class ColdStartService:
    """
    模块4：冷启动与新用户处理模块（毕业设计最终版）
    包含：冷启动判断 + 兴趣标签向量 + 负反馈机制 + 探索推荐
    """

    def __init__(self, vector_dim: int = 50, theta: int = 10, seed: int = 42):
        self.vector_dim = vector_dim
        self.theta = theta  # 冷启动阈值，默认10次交互
        random.seed(seed)
        np.random.seed(seed)

        self.user_interaction_count = {}
        self.user_tag_vectors = {}
        self.video_vectors = {}
        self.video_category = {}
        self.video_popularity = {}

        self._init_mock_data()

    def _init_mock_data(self):
        for vid in range(1, 101):
            vec = np.random.randn(self.vector_dim).astype(np.float32)
            vec /= (np.linalg.norm(vec) + 1e-8)

            if random.random() < 0.35:
                self.video_category[vid] = "tech"
                active = random.sample(range(self.vector_dim), 18)
                vec[active] *= 2.2
                vec /= (np.linalg.norm(vec) + 1e-8)
            else:
                self.video_category[vid] = "other"

            self.video_vectors[vid] = vec
            self.video_popularity[vid] = random.betavariate(2, 5)

        print(f"模拟数据初始化完成：{len(self.video_vectors)} 个视频（约35%为科技/AI类）\n")

    def register_user(self, user_id: int, interest_tags: List[str]):
        """新用户注册"""
        vec = np.random.randn(self.vector_dim).astype(np.float32) * 0.6
        active_dims = random.sample(range(self.vector_dim), 22)
        vec[active_dims] *= 4.8
        vec /= (np.linalg.norm(vec) + 1e-8)

        self.user_tag_vectors[user_id] = vec.copy()
        self.user_interaction_count[user_id] = 0
        print(f"用户 {user_id} 注册成功，兴趣标签: {interest_tags}\n")

    def add_interaction(self, user_id: int, count: int = 1):
        """记录用户行为次数"""
        if user_id not in self.user_interaction_count:
            self.user_interaction_count[user_id] = 0
        self.user_interaction_count[user_id] += count
        print(f"用户 {user_id} 交互次数 → {self.user_interaction_count[user_id]}")

    def is_cold_start(self, user_id: int) -> bool:
        """判断是否仍处于冷启动阶段"""
        return self.user_interaction_count.get(user_id, 0) < self.theta

    def cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)

    def dislike_video(self, user_id: int, video_id: int, strength: float = 0.75):
        """负反馈机制：用户不喜欢某个视频"""
        if user_id not in self.user_tag_vectors or video_id not in self.video_vectors:
            print(f"负反馈失败：用户或视频不存在")
            return

        user_vec = self.user_tag_vectors[user_id].copy()
        video_vec = self.video_vectors[video_id]

        sim = self.cosine_similarity(user_vec, video_vec)

        if sim < 0.12:
            print(f"视频 {video_id} 相似度较低 ({sim:.4f})，负反馈影响较小")
            return

        # 正确反向惩罚
        adjustment = strength * sim * video_vec
        user_vec = user_vec - adjustment
        user_vec /= (np.linalg.norm(user_vec) + 1e-8)

        self.user_tag_vectors[user_id] = user_vec
        print(f"✓ 已应用负反馈：不喜欢视频 {video_id} (相似度 {sim:.4f})，用户画像已更新")

    def recommend(self, user_id: int, top_n: int = 12) -> List[Dict]:
        """冷启动推荐主方法"""
        if user_id not in self.user_tag_vectors:
            return self._popular_recommendation(top_n)

        if not self.is_cold_start(user_id):
            print(f"\n用户 {user_id} 已退出冷启动（交互次数 = {self.user_interaction_count[user_id]}）")
            print("→ 建议切换到模块3：融合机制与用户可控推荐\n")
            return []

        user_vec = self.user_tag_vectors[user_id]
        scored = []

        for vid, video_vec in self.video_vectors.items():
            sim = self.cosine_similarity(user_vec, video_vec)
            pop = self.video_popularity.get(vid, 0.3)
            final_score = 0.87 * sim + 0.13 * pop

            reason = "弱匹配"
            if sim > 0.42:
                reason = "强兴趣匹配"
            elif sim > 0.25:
                reason = "兴趣匹配"

            if self.video_category.get(vid) == "tech" and sim > 0.25:
                reason += " (tech)"

            scored.append({
                "video_id": vid,
                "score": round(final_score, 4),
                "sim": round(sim, 4),
                "reason": reason
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        # 兴趣驱动推荐为主 + 少量探索
        main_recs = scored[:max(10, top_n - 2)]
        explore_list = self._get_explore_videos(num=top_n - len(main_recs),
                                                exclude_ids=[x["video_id"] for x in main_recs])

        for item in explore_list:
            item["score"] = round(item["score"] * 0.52, 4)
            item["sim"] = 0.0
            item["reason"] = "探索推荐"

        final_list = main_recs + explore_list
        final_list.sort(key=lambda x: x["score"], reverse=True)

        return final_list[:top_n]

    def _popular_recommendation(self, top_n: int = 12) -> List[Dict]:
        popular = sorted(self.video_popularity.items(), key=lambda x: x[1], reverse=True)
        return [{"video_id": vid, "score": round(score, 4), "sim": 0.0, "reason": "平台热门"}
                for vid, score in popular[:top_n]]

    def _get_explore_videos(self, num: int = 2, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = []
        candidates = [vid for vid in self.video_vectors if vid not in exclude_ids]
        random.shuffle(candidates)
        return [{
            "video_id": vid,
            "score": round(random.uniform(0.48, 0.65), 4),
            "reason": "探索推荐"
        } for vid in candidates[:num]]


# ====================== 完整演示 ======================
if __name__ == "__main__":
    print("=== 模块4：冷启动与新用户处理模块（最终版） - 毕业设计实验 ===\n")

    service = ColdStartService(theta=10)

    user_id = 1001
    service.register_user(user_id, ["科技", "AI", "编程"])

    print("【初始冷启动推荐】")
    rec = service.recommend(user_id, top_n=12)
    for i, item in enumerate(rec, 1):
        sim_str = f"sim={item['sim']:.4f}" if item.get('sim', 0) > 0 else "sim=-"
        print(f"{i:2d}. 视频ID {item['video_id']:3d} | 分数 {item['score']:.4f} | {sim_str} | {item['reason']}")

    print("\n" + "─" * 90)
    print("演示负反馈机制：")
    service.dislike_video(user_id, video_id=12, strength=0.75)
    service.dislike_video(user_id, video_id=39, strength=0.70)

    print("\n【负反馈后的推荐结果】")
    rec_after = service.recommend(user_id, top_n=12)
    for i, item in enumerate(rec_after, 1):
        sim_str = f"sim={item['sim']:.4f}" if item.get('sim', 0) > 0 else "sim=-"
        print(f"{i:2d}. 视频ID {item['video_id']:3d} | 分数 {item['score']:.4f} | {sim_str} | {item['reason']}")

    print("\n" + "═" * 90)
    print("继续模拟交互以退出冷启动...")
    for _ in range(5):
        service.add_interaction(user_id)

    print("\n当前交互次数已达到退出阈值 → 系统应切换到模块3（混合推荐）")