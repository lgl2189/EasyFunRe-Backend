import numpy as np
import pandas as pd
import pickle
import redis
from typing import Dict, Optional

def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


class BPR_MF:
    """
    毕业设计最终优化版 BPR Matrix Factorization（支持 tempPostId 映射）
    """
    def __init__(self, n_factors: int = 64, lr: float = 0.1, reg: float = 0.0015,
                 n_epochs: int = 100, batch_size: int = 64, n_neg: int = 8):
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.n_neg = n_neg

        self.user_factors = None
        self.item_factors = None
        self.user_bias = None
        self.item_bias = None
        self.global_bias = 0.0

        # momentum 缓存
        self.m_user = None
        self.m_item = None
        self.m_u_bias = None
        self.m_i_bias = None
        self.momentum = 0.9

        # 新增：postId <-> tempPostId 双向映射（随模型一起保存）
        self.post_to_temp: Dict[int, int] = {}
        self.temp_to_post: Dict[int, int] = {}

    def fit(self, df: pd.DataFrame, n_users: int, n_items: int, temp_column: str = "post_id"):
        """训练主函数（支持 tempPostId 列）"""
        if df.empty:
            print("⚠️ 交互数据为空，无法训练")
            return False

        positive_inter = df[df['score'] > 0].copy()
        user_pos_items: Dict[int, set] = {}
        for uid in range(n_users):
            pos = positive_inter[positive_inter['user_id'] == uid][temp_column].unique()
            user_pos_items[uid] = set(pos)

        all_items = set(range(n_items))

        # 初始化
        self.user_factors = np.random.normal(0, 0.0025, (n_users, self.n_factors)).astype(np.float64)
        self.item_factors = np.random.normal(0, 0.0025, (n_items, self.n_factors)).astype(np.float64)
        self.user_bias = np.zeros(n_users, dtype=np.float64)
        self.item_bias = np.zeros(n_items, dtype=np.float64)

        self.m_user = np.zeros_like(self.user_factors)
        self.m_item = np.zeros_like(self.item_factors)
        self.m_u_bias = np.zeros(n_users, dtype=np.float64)
        self.m_i_bias = np.zeros(n_items, dtype=np.float64)

        print(f"🚀 BPR 训练开始 | 用户={n_users} | 视频={n_items} | 隐因子={self.n_factors} | epochs={self.n_epochs}")

        for epoch in range(self.n_epochs):
            total_loss = 0.0
            users = np.random.permutation(n_users)
            current_lr = self.lr * (0.95 ** (epoch // 10))

            for start in range(0, len(users), self.batch_size):
                batch_users = users[start:start + self.batch_size]
                for u in batch_users:
                    pos_items = user_pos_items.get(u, set())
                    if not pos_items:
                        continue
                    for _ in range(self.n_neg):
                        i = np.random.choice(list(pos_items))
                        neg_candidates = list(all_items - pos_items)
                        if not neg_candidates:
                            continue
                        j = np.random.choice(neg_candidates)

                        x_ui = (np.dot(self.user_factors[u], self.item_factors[i]) +
                                self.user_bias[u] + self.item_bias[i] + self.global_bias)
                        x_uj = (np.dot(self.user_factors[u], self.item_factors[j]) +
                                self.user_bias[u] + self.item_bias[j] + self.global_bias)
                        x_uij = x_ui - x_uj

                        sig = sigmoid(x_uij)
                        loss = -np.log(sig + 1e-12)
                        total_loss += loss

                        grad_common = 1 - sig
                        grad_u = grad_common * (self.item_factors[i] - self.item_factors[j])

                        # momentum 更新
                        self.m_user[u] = self.momentum * self.m_user[u] + (1 - self.momentum) * grad_u
                        self.m_item[i] = self.momentum * self.m_item[i] + (1 - self.momentum) * (grad_common * self.user_factors[u])
                        self.m_item[j] = self.momentum * self.m_item[j] + (1 - self.momentum) * (-grad_common * self.user_factors[u])

                        self.user_factors[u] += current_lr * (self.m_user[u] - self.reg * self.user_factors[u])
                        self.item_factors[i] += current_lr * (self.m_item[i] - self.reg * self.item_factors[i])
                        self.item_factors[j] += current_lr * (self.m_item[j] - self.reg * self.item_factors[j])

                        # bias 更新
                        self.m_u_bias[u] = self.momentum * self.m_u_bias[u] + (1 - self.momentum) * grad_common
                        self.m_i_bias[i] = self.momentum * self.m_i_bias[i] + (1 - self.momentum) * grad_common
                        self.m_i_bias[j] = self.momentum * self.m_i_bias[j] + (1 - self.momentum) * (-grad_common)

                        self.user_bias[u] += current_lr * (self.m_u_bias[u] - self.reg * self.user_bias[u])
                        self.item_bias[i] += current_lr * (self.m_i_bias[i] - self.reg * self.item_bias[i])
                        self.item_bias[j] += current_lr * (self.m_i_bias[j] - self.reg * self.item_bias[j])

            if (epoch + 1) % 10 == 0 or epoch == self.n_epochs - 1:
                avg_loss = total_loss / max(1, len(users) * self.n_neg)
                print(f"Epoch {epoch + 1:3d}/{self.n_epochs} | LR: {current_lr:.4f} | Avg Loss: {avg_loss:.4f}")

        print("🎉 BPR 训练完成！")
        return True

    def predict_scores(self, user_id: int, candidate_posts: Optional[list] = None, exclude_post_ids: set = None) -> \
    Dict[int, float]:
        """
        预测函数（修改版：支持过滤已交互视频）
        新增参数：
        - exclude_post_ids: 需要排除的已交互视频ID集合
        """
        if self.user_factors is None or user_id >= len(self.user_factors):
            return {}
        user_vec = self.user_factors[user_id]
        u_bias = self.user_bias[user_id]

        # 初始化排除集合
        if exclude_post_ids is None:
            exclude_post_ids = set()

        # 如果外部传了候选列表就用，否则用所有
        if candidate_posts is not None:
            cands = candidate_posts
        else:
            cands = list(self.temp_to_post.keys()) if self.temp_to_post else list(range(len(self.item_factors)))

        scores = {}
        for temp_id in cands:
            if temp_id >= len(self.item_factors):
                continue
            # 先通过 temp_to_post 映射回真实 postId，再判断是否需要排除
            real_id = self.temp_to_post.get(temp_id, temp_id)
            if real_id in exclude_post_ids:  # 新增：过滤已交互视频
                continue

            score = float(np.dot(user_vec, self.item_factors[temp_id]) +
                          u_bias + self.item_bias[temp_id] + self.global_bias)
            scores[real_id] = score

        # 按分数降序，只保留 Top 150
        sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:150])
        if sorted_scores:
            max_raw = max(sorted_scores.values())
            scale = 8.0 / max(1.0, max_raw)
            for vid in sorted_scores:
                sorted_scores[vid] *= scale

        print(f"✅ predict_scores 返回 Top-{len(sorted_scores)}（已过滤 {len(exclude_post_ids)} 个已交互视频）")
        return sorted_scores

    def save_to_redis(self, redis_client):
        """保存模型到 Redis（包含映射）"""
        state = {
            "user_factors": self.user_factors,
            "item_factors": self.item_factors,
            "user_bias": self.user_bias,
            "item_bias": self.item_bias,
            "global_bias": self.global_bias,
            "post_to_temp": self.post_to_temp,
            "temp_to_post": self.temp_to_post,
        }
        redis_client.set("bpr_model_state", pickle.dumps(state))
        print("✅ BPR 模型已保存到 Redis (key = bpr_model_state)")

    def load_from_redis(self, redis_client) -> bool:
        """从 Redis 加载模型（包含映射）"""
        data = redis_client.get("bpr_model_state")
        if not data:
            return False
        state = pickle.loads(data)
        self.user_factors = state["user_factors"]
        self.item_factors = state["item_factors"]
        self.user_bias = state["user_bias"]
        self.item_bias = state["item_bias"]
        self.global_bias = state["global_bias"]
        self.post_to_temp = state.get("post_to_temp", {})
        self.temp_to_post = state.get("temp_to_post", {})
        print("✅ BPR 模型和PostId映射已从 Redis 加载")
        return True