import numpy as np
import pandas as pd


def sigmoid(x):
    """BPR 使用的 sigmoid 函数"""
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


class BPR_MF:
    """
    最终优化版 BPR Matrix Factorization（推荐用于毕业设计）
    - 重点优化了预测分数区分度
    - 隐因子维度提升到64（符合文档推荐）
    """

    def __init__(self, n_factors=64, lr=0.1, reg=0.0015, n_epochs=120, batch_size=64, n_neg=8):
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

        self.m_user = None
        self.m_item = None
        self.m_u_bias = None
        self.m_i_bias = None
        self.momentum = 0.9

    def fit(self, df, n_users, n_items):
        positive_inter = df[df['score'] > 0].copy()

        user_pos_items = {}
        all_items = set(range(n_items))
        for uid in range(n_users):
            pos = positive_inter[positive_inter['user_id'] == uid]['video_id'].unique()
            user_pos_items[uid] = set(pos)

        # 初始化（优化尺度，提升区分度）
        self.user_factors = np.random.normal(0, 0.0025, (n_users, self.n_factors)).astype(np.float64)
        self.item_factors = np.random.normal(0, 0.0025, (n_items, self.n_factors)).astype(np.float64)
        self.user_bias = np.zeros(n_users, dtype=np.float64)
        self.item_bias = np.zeros(n_items, dtype=np.float64)

        self.m_user = np.zeros_like(self.user_factors)
        self.m_item = np.zeros_like(self.item_factors)
        self.m_u_bias = np.zeros(n_users, dtype=np.float64)
        self.m_i_bias = np.zeros(n_items, dtype=np.float64)

        print(f"开始 BPR 训练 | 隐因子={self.n_factors} | 用户={n_users} | 视频={n_items} | 负采样={self.n_neg}")
        min_loss = float('inf')

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

                        dot_ui = np.dot(self.user_factors[u], self.item_factors[i])
                        dot_uj = np.dot(self.user_factors[u], self.item_factors[j])
                        x_ui = dot_ui + self.user_bias[u] + self.item_bias[i] + self.global_bias
                        x_uj = dot_uj + self.user_bias[u] + self.item_bias[j] + self.global_bias
                        x_uij = x_ui - x_uj

                        sig = sigmoid(x_uij)
                        loss = -np.log(sig + 1e-12)
                        total_loss += loss

                        grad_common = (1 - sig)

                        grad_u = grad_common * (self.item_factors[i] - self.item_factors[j])
                        grad_i = grad_common * self.user_factors[u]
                        grad_j = -grad_common * self.user_factors[u]

                        self.m_user[u] = self.momentum * self.m_user[u] + (1 - self.momentum) * grad_u
                        self.m_item[i] = self.momentum * self.m_item[i] + (1 - self.momentum) * grad_i
                        self.m_item[j] = self.momentum * self.m_item[j] + (1 - self.momentum) * grad_j

                        self.user_factors[u] += current_lr * (self.m_user[u] - self.reg * self.user_factors[u])
                        self.item_factors[i] += current_lr * (self.m_item[i] - self.reg * self.item_factors[i])
                        self.item_factors[j] += current_lr * (self.m_item[j] - self.reg * self.item_factors[j])

                        self.m_u_bias[u] = self.momentum * self.m_u_bias[u] + (1 - self.momentum) * grad_common
                        self.m_i_bias[i] = self.momentum * self.m_i_bias[i] + (1 - self.momentum) * grad_common
                        self.m_i_bias[j] = self.momentum * self.m_i_bias[j] + (1 - self.momentum) * (-grad_common)

                        self.user_bias[u] += current_lr * (self.m_u_bias[u] - self.reg * self.user_bias[u])
                        self.item_bias[i] += current_lr * (self.m_i_bias[i] - self.reg * self.item_bias[i])
                        self.item_bias[j] += current_lr * (self.m_i_bias[j] - self.reg * self.item_bias[j])

            avg_loss = total_loss / max(1, len(users) * self.n_neg)
            if avg_loss < min_loss:
                min_loss = avg_loss

            if (epoch + 1) % 5 == 0 or epoch == self.n_epochs - 1:
                print(f"Epoch {epoch + 1:3d}/{self.n_epochs} | LR: {current_lr:.4f} | Avg Loss: {avg_loss:.4f}")

        print(f"BPR 训练完成！最低 Loss: {min_loss:.4f}\n")
        return self.user_factors, self.item_factors, self.user_bias, self.item_bias, self.global_bias


# ====================== 模拟数据生成 ======================
def generate_improved_simulation_data(n_users=400, n_videos=1500, seed=42):
    """改进版模拟数据"""
    np.random.seed(seed)
    n_clusters = 4
    users_per_cluster = n_users // n_clusters
    user_cluster = np.repeat(np.arange(n_clusters), users_per_cluster)
    if len(user_cluster) < n_users:
        user_cluster = np.concatenate([user_cluster, np.zeros(n_users - len(user_cluster), dtype=int)])

    video_popularity = np.random.zipf(2.0, n_videos)
    video_cluster = np.random.randint(0, n_clusters, n_videos)

    interactions = []
    for uid in range(n_users):
        cluster = user_cluster[uid]
        n_inter = np.random.randint(35, 80)
        n_own = int(n_inter * 0.7)
        n_cross = n_inter - n_own

        own_videos = np.where(video_cluster == cluster)[0]
        cross_videos = np.where(video_cluster != cluster)[0]

        selected_own = np.random.choice(own_videos, min(n_own, len(own_videos)), replace=False)
        selected_cross = np.random.choice(cross_videos, min(n_cross, len(cross_videos)), replace=False)
        selected_videos = np.concatenate([selected_own, selected_cross])

        for vid in selected_videos:
            if np.random.rand() < 0.25:
                score = -np.random.uniform(1.0, 5.0)
            else:
                base = np.random.uniform(1.8, 5.5)
                score = base * (1 + 0.25 * (video_popularity[vid] / video_popularity.max()))
            interactions.append({'user_id': uid, 'video_id': int(vid), 'score': round(score, 2)})

    return pd.DataFrame(interactions), n_users, n_videos


# ====================== 预测函数（重点优化区分度） ======================
def get_cf_scores(test_user_id: int, top_n: int = 10):
    """对应设计文档 getCFScores - 已优化分数区分度"""
    if test_user_id >= n_users or test_user_id < 0:
        print(f"用户 {test_user_id} 超出范围（冷启动需单独处理）")
        return {}

    user_vec = user_factors[test_user_id]
    u_bias = user_bias[test_user_id]

    scores = {}
    for vid in range(n_videos):
        item_vec = item_factors[vid]
        i_bias = item_bias[vid]
        score = float(np.dot(user_vec, item_vec) + u_bias + i_bias + global_bias)
        scores[vid] = score

    # 温和缩放：让最高分接近 8~9，保留自然差异
    if scores:
        max_raw = max(scores.values())
        scale = 8.0 / max(1.0, max_raw)  # 控制最高分在8左右
        for vid in scores:
            scores[vid] = scores[vid] * scale

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print(f"\n用户 {test_user_id} 的协同过滤 Top {top_n} 推荐：")
    print("视频ID\t预测分数")
    print("-" * 35)
    for vid, score in sorted_scores[:top_n]:
        print(f"{vid:6d}\t{score:8.4f}")

    return dict(sorted_scores[:top_n])


# ====================== 主程序 ======================
if __name__ == "__main__":
    print("正在生成改进版模拟数据...\n")

    # 推荐规模：用户400，视频1500，平衡效果与速度
    df, n_users, n_videos = generate_improved_simulation_data(n_users=400, n_videos=1000, seed=42)

    print(f"模拟数据生成完成！用户: {n_users} | 视频: {n_videos} | 交互: {len(df)} 条")
    print(f"正反馈比例: {(df['score'] > 0).mean():.1%}\n")

    print("=== 开始 BPR 协同过滤训练 ===")
    bpr_model = BPR_MF(n_factors=64, lr=0.1, reg=0.0015, n_epochs=1000, n_neg=8)

    global user_factors, item_factors, user_bias, item_bias, global_bias
    user_factors, item_factors, user_bias, item_bias, global_bias = bpr_model.fit(df, n_users, n_videos)

    print("\n" + "=" * 80)
    print("协同过滤推荐测试（来自不同兴趣簇的用户）：")
    get_cf_scores(5)
    get_cf_scores(105)
    get_cf_scores(205)
    get_cf_scores(305)

    print("\n" + "=" * 80)
    print("协同过滤模块训练完成！")
    print("预测分数区分度已优化，可直接用于模块3融合。")