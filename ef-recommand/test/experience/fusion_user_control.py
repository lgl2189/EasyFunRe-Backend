import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any


# ==========================================
# 1. 对外接口定义：接收前端参数
# ==========================================
@dataclass
class RecommendParam:
    """用户控制参数 (建议由前端 Slider 传入 0.0 ~ 1.0 的值)"""
    alpha: float = 0.5  # 融合权重：0.0完全看内容，1.0完全看CF群体行为
    w_div: float = 0.0  # 多样性权重：越高推荐的分类越杂
    w_bound: float = 0.0  # 破圈控制：越高越倾向于推荐平时不看的视频
    top_n: int = 10  # 返回最终列表长度

    def validate(self):
        self.alpha = max(0.0, min(1.0, self.alpha))
        self.w_div = max(0.0, min(1.0, self.w_div))
        self.w_bound = max(0.0, min(1.0, self.w_bound))


# ==========================================
# 2. 核心服务：融合与多样性重排序
# ==========================================
class HybridFusionService:
    """
    模块3：核心融合服务 (解耦版)
    负责接收模块1和模块2的计算结果，执行归一化、加权、破圈补偿和 MMR 重排序
    """

    @staticmethod
    def _normalize(scores: Dict[int, float]) -> Dict[int, float]:
        """Min-Max 归一化：将任意范围的分数统一缩放到 0.0 ~ 1.0"""
        if not scores: return {}
        min_v, max_v = min(scores.values()), max(scores.values())
        if max_v == min_v:
            return {k: 0.5 for k in scores.keys()}
        return {k: (v - min_v) / (max_v - min_v + 1e-8) for k, v in scores.items()}

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个特征向量的余弦相似度 (用于MMR算法)"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0: return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def fuse_and_recommend(self,
                           params: RecommendParam,
                           cf_scores: Dict[int, float],
                           content_scores: Dict[int, float],
                           video_features: Dict[int, np.ndarray]) -> List[Dict[str, Any]]:
        """
        核心对外接口：执行融合推荐
        :param params: 前端传来的可控参数
        :param cf_scores: 模块1(CF) 算出的粗排分数 {video_id: score} (如 2.0~8.0)
        :param content_scores: 模块2(内容) 算出的相似度 {video_id: score} (如 0.0~1.0)
        :param video_features: 候选视频的底层特征向量 {video_id: numpy_array} (用于算MMR)
        :return: 最终排好序的视频字典列表
        """
        params.validate()

        # 1. 分数统一归一化
        norm_cf = self._normalize(cf_scores)
        norm_content = self._normalize(content_scores)

        # 取出所有候选视频 ID（双路召回的并集）
        all_candidates = set(norm_cf.keys()).union(set(norm_content.keys()))

        # 2. 计算基础融合分 + 破圈补偿
        fused_scores = {}
        for vid in all_candidates:
            s_cf = norm_cf.get(vid, 0.0)
            s_ct = norm_content.get(vid, 0.0)

            # (a) 基础加权公式
            base_score = params.alpha * s_cf + (1.0 - params.alpha) * s_ct

            # (b) 破圈边界控制 (w_bound)：如果该视频内容匹配度很低，反而给它探索奖励
            exploration_bonus = params.w_bound * (1.0 - s_ct) * 0.5

            fused_scores[vid] = base_score + exploration_bonus

        # 3. MMR 多样性重排序
        lambda_val = 1.0 - params.w_div
        candidates = list(fused_scores.items())
        selected_list = []

        while len(selected_list) < params.top_n and candidates:
            best_mmr = -float('inf')
            best_vid = None
            best_hybrid_score = 0.0

            for vid, h_score in candidates:
                penalty = 0.0
                if selected_list:
                    # 找到该视频与【已选中列表】里所有视频的最大相似度，作为惩罚项
                    vec_current = video_features.get(vid, np.zeros(1))
                    penalty = max(
                        self._cosine_similarity(vec_current, video_features.get(s['video_id'], np.zeros(1)))
                        for s in selected_list
                    )

                # (c) MMR 核心公式
                mmr_score = lambda_val * h_score - (1.0 - lambda_val) * penalty

                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_vid = vid
                    best_hybrid_score = h_score

            selected_list.append({
                "video_id": best_vid,
                "final_score": round(best_mmr, 4),
                "hybrid_score": round(best_hybrid_score, 4)
            })

            # 从候选池移除已选项
            candidates = [c for c in candidates if c[0] != best_vid]

        return selected_list


# ==========================================
# 3. 模拟数据生成与独立验证测试
# ==========================================
def generate_mock_inputs():
    """模拟模块1、模块2传入的实验数据"""
    categories = ["科技", "生活", "游戏", "影视", "音乐"]

    cf_scores = {}
    content_scores = {}
    video_features = {}
    video_meta = {}  # 仅用于打印对比

    np.random.seed(42)

    # 模拟生成 50 个候选视频
    for vid in range(1, 51):
        cat_idx = vid % 5
        cat_name = categories[cat_idx]
        video_meta[vid] = cat_name

        # 模拟视频向量 (one-hot 加上一些随机噪声)
        vec = np.random.normal(0.1, 0.05, 5)
        vec[cat_idx] += 1.0
        video_features[vid] = vec / np.linalg.norm(vec)

        # 模拟：当前用户是一个深度的“科技”迷
        if cat_name == "科技":
            cf_scores[vid] = np.random.uniform(6.0, 9.0)  # CF 发现该用户行为像科技迷
            content_scores[vid] = np.random.uniform(0.8, 0.99)  # 内容画像也是完美匹配科技
        elif cat_name == "影视":
            cf_scores[vid] = np.random.uniform(4.0, 7.0)  # CF 挖掘到其他科技迷也看影视，分数中等偏高
            content_scores[vid] = np.random.uniform(0.1, 0.3)  # 但内容画像上，影视和科技毫不相干
        else:
            cf_scores[vid] = np.random.uniform(1.0, 3.0)  # 其他不感兴趣
            content_scores[vid] = np.random.uniform(0.0, 0.2)

    return cf_scores, content_scores, video_features, video_meta


def print_result(title, result, meta_data):
    print(f"\n{'-' * 60}\n{title}\n{'-' * 60}")
    print(f"排名 | 视频ID | 分类 | 最终MMR分 | 融合基础分")
    print("-" * 60)
    cat_counts = {}
    for i, item in enumerate(result, 1):
        vid = item['video_id']
        cat = meta_data[vid]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        print(f" {i:2d}  | {vid:5d}  | {cat:4s} |  {item['final_score']:.4f}   |  {item['hybrid_score']:.4f}")

    print("-" * 60)
    print("分类分布统计:", ", ".join([f"{k}:{v}个" for k, v in cat_counts.items()]))


if __name__ == "__main__":
    # 1. 准备依赖和Mock数据
    fusion_service = HybridFusionService()
    cf_data, content_data, features_data, meta_data = generate_mock_inputs()

    print("=== 模块3融合对外接口 测试实验 ===")
    print("当前模拟用户画像：深度【科技】迷。CF模型推测他可能对【影视】有潜在群体偏好。")

    # 实验A：纯信息茧房 (只看内容，不多样，不破圈)
    param_a = RecommendParam(alpha=0.0, w_div=0.0, w_bound=0.0, top_n=10)
    res_a = fusion_service.fuse_and_recommend(param_a, cf_data, content_data, features_data)
    print_result("[实验A] 信息茧房模式 (完全基于历史内容，alpha=0)", res_a, meta_data)

    # 实验B：常规混合推荐 (1:1融合，微调多样性)
    param_b = RecommendParam(alpha=0.5, w_div=0.2, w_bound=0.1, top_n=10)
    res_b = fusion_service.fuse_and_recommend(param_b, cf_data, content_data, features_data)
    print_result("[实验B] 常规混合推荐 (CF与Content各占一半，少量多样性)", res_b, meta_data)

    # 实验C：强力打破茧房 (偏向CF，高多样性惩罚，高破圈探索)
    param_c = RecommendParam(alpha=0.6, w_div=0.5, w_bound=0.6, top_n=10)
    res_c = fusion_service.fuse_and_recommend(param_c, cf_data, content_data, features_data)
    print_result("[实验C] 强力打破茧房 (提高CF群体推荐，拉高多样性和探索参数)", res_c, meta_data)