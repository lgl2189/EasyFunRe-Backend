import pickle
from typing import List, Dict, Any, Set

import numpy as np
import pandas as pd
import redis

from schemas.recommend import RecommendRequestDTO, RecommendItem
from service.modules.cold_start import ColdStartService
from service.modules.collaborative_filtering import BPR_MF
from service.modules.content_feature_fusion import ContentFeatureService
from service.modules.hybrid import HybridFusionService, RecommendParam


class RecommendService:
    def __init__(self, vectorDim: int = 300, contentDim: int = 300):
        self.vectorDim = vectorDim
        self.contentDim = contentDim

        self.coldStartService = ColdStartService(vectorDim=vectorDim)
        self.contentService = ContentFeatureService(targetDim=contentDim)
        self.fusionService = HybridFusionService()

        self.bprModel: BPR_MF = BPR_MF(
            n_factors=64, lr=0.1, reg=0.0015,
            n_epochs=100, batch_size=64, n_neg=8
        )

        self.redis_client = redis.Redis(
            host="192.168.150.105",
            port=6379,
            username="easyfun",
            password="12345678",
            db=1,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=10
        )

        if not self.bprModel.load_from_redis(self.redis_client):
            print("⚠️ Redis 中没有找到 BPR 模型，请先进行训练")

        self.postMeta: Dict[int, Dict] = {}
        self.postFeatures: Dict[int, np.ndarray] = {}

    # ====================== Redis 推荐缓存 ======================
    def _get_all_recommended_post_ids(self, user_id: int) -> Set[int]:
        try:
            pattern = f"post:recommended:{user_id}:*"
            cursor = 0
            all_keys = []
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                all_keys.extend(keys)
                if cursor == 0:
                    break

            recommended_post_ids = set()
            for key in all_keys:
                post_ids_bytes = self.redis_client.lrange(key, 0, -1)
                post_ids = [int(pid.decode('utf-8')) for pid in post_ids_bytes if pid]
                recommended_post_ids.update(post_ids)

            return recommended_post_ids
        except Exception:
            return set()

    def is_post_recommended(self, user_id: int, post_id: int, cached_recommended_set: Set[int] = None) -> bool:
        recommended_set = cached_recommended_set or self._get_all_recommended_post_ids(user_id)
        return post_id in recommended_set

    def set_post_recommended_batch(self, user_id: int, post_ids: List[int]):
        if not post_ids:
            return
        try:
            first_post_id = post_ids[0]
            cache_key = f"post:recommended:{user_id}:{first_post_id}"
            self.redis_client.delete(cache_key)
            post_ids_str = [str(pid) for pid in post_ids]
            self.redis_client.rpush(cache_key, *post_ids_str)
            self.redis_client.expire(cache_key, 300)  # 5分钟
        except Exception:
            pass

    def _processRequestData(self, req: RecommendRequestDTO):
        posts = []
        for post in req.postList:
            posts.append({
                "post_id": post.postId,
                "title": post.title or "",
                "tags": post.tags or "",
                "category": post.category or ""
            })

        user_tags = [tag.tagName for tag in req.userTagList if getattr(tag, 'tagName', None)]

        if posts:
            self.postMeta = {v["post_id"]: v for v in posts}
            self.contentService.buildPostVectors(posts)
            self.postFeatures = self.contentService.postVectors.copy()
            self.coldStartService.vectorizer = self.contentService.vectorizer
            self.coldStartService.setCandidatePosts(posts, content_vectors=self.contentService.postVectors)

        # 处理交互记录
        interactionsMap: Dict[int, List[tuple]] = {}
        for inter in req.interactionList:
            uid = inter.ownerId
            vid = inter.targetPostId
            if uid is None or vid is None:
                continue
            weight = 1.0 if inter.isLike == 1 else (-0.8 if inter.isDislike == 1 else 0.3)
            interactionsMap.setdefault(uid, []).append((vid, weight))

        return interactionsMap, user_tags

    async def getRecommendationPostList(self, userId: int, isColdStart: bool,
                                        reqBody: RecommendRequestDTO,
                                        pageSize: int = 12,
                                        alpha: float = 0.5,
                                        wDiv: float = 0.2,
                                        wBound: float = 0.15) -> Dict[str, Any]:

        interactionsMap, user_tags = self._processRequestData(reqBody)
        userInteractions = interactionsMap.get(userId, [])
        interacted_post_ids = {vid for vid, _ in userInteractions}

        cached_recommended_set = self._get_all_recommended_post_ids(userId)

        if userInteractions:
            self.contentService.updateUserProfile(userId, userInteractions)

        # ====================== 冷启动路径 ======================
        if isColdStart:
            if user_tags:
                self.coldStartService.registerUser(userId, user_tags)
            else:
                self.coldStartService.registerUser(userId, ["科技", "生活", "娱乐"])

            recs = self.coldStartService.recommend(userId, pageSize)

            # 过滤已交互和已推荐
            recs = [item for item in recs
                    if item["post_id"] not in interacted_post_ids
                    and not self.is_post_recommended(userId, item["post_id"], cached_recommended_set)]

            if len(recs) < pageSize:
                popular_recs = self.coldStartService._popularRecommendation(pageSize * 2)
                for item in popular_recs:
                    if (item["post_id"] not in interacted_post_ids
                            and not self.is_post_recommended(userId, item["post_id"], cached_recommended_set)
                            and len(recs) < pageSize):
                        recs.append(item)

            items = [
                RecommendItem(
                    postId=item["post_id"],
                    finalScore=round(item.get("score", 0.0), 4),
                    hybridScore=round(item.get("score", 1.0), 4),
                    reason=item.get("reason", "冷启动推荐")
                ) for item in recs[:pageSize]
            ]

            if items:
                self.set_post_recommended_batch(userId, [item.postId for item in items])

            # ====================== 冷启动实验指标计算 ======================
            experiment_metrics = {}
            from config.config import isExperiment
            if isExperiment and self.postFeatures:
                experiment_metrics = self.compute_experiment_metrics(
                    recommend_list=recs[:pageSize],  # recs 是 cold start 返回的列表
                    postFeatures=self.postFeatures
                )

            return {
                "userId": userId,
                "recommendPostList": items,
                "isColdStart": True,
                "message": "冷启动推荐",
                "actualParams": {"alpha": None, "wDiv": None, "wBound": None},
                "debugQueryParams": {"userId": userId, "isColdStart": True, "pageSize": pageSize},
                "experimentMetrics": experiment_metrics,  # 新增
            }

        # ====================== 混合推荐路径 ======================
        content_exclude_ids = interacted_post_ids.union(cached_recommended_set)

        cfScores = self.getCFScores(
            userId, candidateSize=150,
            exclude_post_ids=interacted_post_ids,
            cached_recommended_set=cached_recommended_set
        )

        contentScores = self.contentService.getContentScores(
            userId, candidateSize=150, exclude_post_ids=content_exclude_ids
        )

        fusionParams = RecommendParam(alpha=alpha, wDiv=wDiv, wBound=wBound, topN=pageSize)
        fusedResults = self.fusionService.fuseAndRecommend(
            params=fusionParams,
            cfScores=cfScores,
            contentScores=contentScores,
            postFeatures=self.postFeatures
        )

        items = [
            RecommendItem(
                postId=item["postId"],
                finalScore=item["finalScore"],
                hybridScore=item["hybridScore"],
                reason="混合推荐 (CF + 内容特征)"
            ) for item in fusedResults
        ]

        if items:
            self.set_post_recommended_batch(userId, [item.postId for item in items])

        # ====================== 实验指标计算（直接集成到原有流程） ======================
        experiment_metrics = {}
        from config.config import isExperiment
        if isExperiment and not isColdStart and self.postFeatures:
            # 使用 fusedResults（原始融合结果，包含 postId）
            experiment_metrics = self.compute_experiment_metrics(
                recommend_list=fusedResults,  # fusedResults 是 List[Dict]，包含 "postId"
                postFeatures=self.postFeatures
            )

        return {
            "userId": userId,
            "recommendPostList": items,
            "isColdStart": False,
            "message": f"混合推荐完成 (α={alpha:.2f}, 多样性={wDiv:.2f}, 破圈={wBound:.2f})",
            "actualParams": {"alpha": round(alpha, 4), "wDiv": round(wDiv, 4), "wBound": round(wBound, 4)},
            "experimentMetrics": experiment_metrics,  # 新增：实验指标
        }

    def getCFScores(self, userId: int, candidateSize: int = 150,
                    exclude_post_ids: set = None, cached_recommended_set: Set[int] = None) -> Dict[int, float]:
        if self.bprModel is None or self.bprModel.user_factors is None:
            return {}

        final_exclude = set(exclude_post_ids) if exclude_post_ids else set()
        raw_cf_scores = self.bprModel.predict_scores(userId, exclude_post_ids=final_exclude)

        recommended_set = cached_recommended_set or self._get_all_recommended_post_ids(userId)
        filtered_cf_scores = {
            post_id: score for post_id, score in raw_cf_scores.items()
            if post_id not in recommended_set
        }

        sorted_filtered = dict(
            sorted(filtered_cf_scores.items(), key=lambda x: x[1], reverse=True)[:candidateSize]
        )
        return sorted_filtered

    def train_cf_model_with_data(self, df: pd.DataFrame, videos: list,
                                 n_users: int = None, n_items: int = None,
                                 user_to_temp: Dict[int, int] = None,
                                 temp_to_user: Dict[int, int] = None,
                                 post_to_temp: Dict[int, int] = None,
                                 temp_to_post: Dict[int, int] = None) -> bool:
        try:
            if df.empty:
                print("⚠️ 交互数据为空，无法训练")
                return False

            if n_users is None or n_items is None:
                # 兼容旧逻辑
                n_users_old = int(df['user_id'].max() + 1) + 10
                n_items_old = max(int(df['post_id'].max() + 1), 100)
                success = self.bprModel.fit(df, n_users_old, n_items_old)
            else:
                print(f"🚀 开始训练 BPR 模型 | 用户={n_users} | 视频={n_items}")
                success = self.bprModel.fit(
                    df, n_users, n_items,
                    user_column="tempUserId", temp_column="tempPostId"
                )

            if success:
                if n_users is not None:
                    self.bprModel.user_to_temp = dict(user_to_temp or {})
                    self.bprModel.temp_to_user = dict(temp_to_user or {})
                    self.bprModel.post_to_temp = dict(post_to_temp or {})
                    self.bprModel.temp_to_post = dict(temp_to_post or {})

                self.bprModel.save_to_redis(self.redis_client)
                print("🎉 BPR 模型训练完成并已保存到 Redis")
                return True
            return False

        except Exception as e:
            print(f"❌ BPR 模型训练异常: {e}")
            return False

    def get_cold_start_tags(self, videos: List[Dict], limit: int = 50) -> Dict[str, Any]:
        cache_key = "cold_start:tag-list"
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                tags = pickle.loads(cached)
                return {"tags": tags}

            tags = self.coldStartService.extract_cold_start_tags(videos, limit=limit)

            self.redis_client.set(
                cache_key, pickle.dumps(tags), ex=30 * 24 * 60 * 60
            )
            return {"tags": tags}

        except Exception:
            # 兜底
            tags = self.coldStartService.extract_cold_start_tags([], limit=limit)
            return {"tags": tags}

    def compute_experiment_metrics(self,
                                   recommend_list: List[Dict[str, Any]],
                                   postFeatures: Dict[int, np.ndarray],
                                   postCategories: Dict[int, str] = None) -> Dict[str, float]:
        """
        计算论文实验 6.2.1 中需要的两个关键指标：
        - ILD (Intra-List Diversity)：列表内视频间的平均不相似度
        - Novelty：基于流行度逆数加权的新颖性

        会在控制台直接打印实验指标，同时返回给调用方。
        """
        if not recommend_list:
            print("⚠️ [Experiment Metrics] 推荐列表为空，无法计算指标")
            return {"ILD": 0.0, "Novelty": 0.0}

        from config.config import isExperiment
        if not isExperiment:
            print("ℹ️ [Experiment Metrics] 实验模式已关闭 (isExperiment=False)")
            return {"ILD": 0.0, "Novelty": 0.0, "note": "实验模式已关闭"}

        # ====================== 统一提取 post_id ======================
        post_ids = []
        for item in recommend_list:
            pid = item.get("postId") or item.get("post_id")
            if pid is not None:
                post_ids.append(int(pid))

        n = len(post_ids)
        if n == 0:
            print("⚠️ [Experiment Metrics] 无法提取有效的 post_id")
            return {"ILD": 0.0, "Novelty": 0.0}

        # ====================== 1. 计算 Intra-List Diversity (ILD) ======================
        ild_sum = 0.0
        pair_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                vid1 = post_ids[i]
                vid2 = post_ids[j]
                vec1 = postFeatures.get(vid1, np.zeros(self.vectorDim, dtype=np.float32))
                vec2 = postFeatures.get(vid2, np.zeros(self.vectorDim, dtype=np.float32))

                if np.linalg.norm(vec1) > 1e-8 and np.linalg.norm(vec2) > 1e-8:
                    sim = HybridFusionService._cosineSimilarity(vec1, vec2)
                    ild_sum += (1.0 - sim)
                    pair_count += 1

        ild = (ild_sum / max(1, pair_count)) if pair_count > 0 else 0.0

        # ====================== 2. 计算 Novelty ======================
        novelty_sum = 0.0
        for vid in post_ids:
            pop = 0.0
            if hasattr(self, 'coldStartService') and vid in self.coldStartService.postPopularity:
                pop = self.coldStartService.postPopularity.get(vid, 0.3)
            else:
                pop = 0.3

            novelty = -np.log(max(pop, 1e-6)) if pop > 0 else 0.0
            novelty_sum += novelty

        novelty = novelty_sum / max(1, n)

        # ====================== 在控制台输出实验指标 ======================
        mode = "冷启动" if recommend_list and "reason" in recommend_list[0] and "冷启动" in str(
            recommend_list[0].get("reason", "")) else "混合推荐"

        print("\n" + "=" * 80)
        print(f"📊 【实验指标】 {mode} | Top-{n} 推荐结果")
        print(f"   ILD (多样性)     : {ild:.4f}")
        print(f"   Novelty (新颖性) : {novelty:.4f}")
        print(f"   列表大小         : {n}")
        print(
            f"   参数设置         : α={recommend_list[0].get('hybridScore', 'N/A') if 'hybridScore' in str(recommend_list[0]) else 'N/A'}")  # 简单提示
        print("=" * 80 + "\n")

        # ====================== 返回结果（保持接口正常） ======================
        return {
            "ILD": round(ild, 4),
            "Novelty": round(novelty, 4),
            "list_size": n,
            "post_ids": post_ids[:8]
        }
