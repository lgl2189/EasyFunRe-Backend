from typing import List, Dict, Any, Set
import numpy as np
import pandas as pd
import requests
import redis

from service.modules.cold_start import ColdStartService
from service.modules.collaborative_filtering import BPR_MF
from service.modules.content_feature_fusion import ContentFeatureService
from service.modules.fusion_user_control import HybridFusionService, RecommendParam

from schemas.recommend import RecommendRequestDTO, RecommendItem


class RecommendService:
    def __init__(self, vectorDim: int = 50, contentDim: int = 300):
        self.vectorDim = vectorDim
        self.contentDim = contentDim

        # 四个模块实例化
        self.coldStartService = ColdStartService(vectorDim=vectorDim)
        self.contentService = ContentFeatureService(targetDim=contentDim)
        self.fusionService = HybridFusionService()

        # BPR 模型（使用你最新的优化版）
        self.bprModel: BPR_MF = BPR_MF(
            n_factors=64,
            lr=0.1,
            reg=0.0015,
            n_epochs=100,
            batch_size=64,
            n_neg=8
        )

        # Redis 连接
        self.redis_client = redis.Redis(
            host="192.168.150.105",
            port=6379,
            username="easyfun",
            password="12345678",
            db=1,  # 固定使用数据库1
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=10
        )

        # 启动时尝试从 Redis 加载已训练的 BPR 模型
        if not self.bprModel.load_from_redis(self.redis_client):
            print("⚠️ Redis 中没有找到 BPR 模型，请先调用 /recommend/train/cf-model 接口进行训练")

        # 内存缓存
        self.postMeta: Dict[int, Dict] = {}
        self.postFeatures: Dict[int, np.ndarray] = {}

    # ====================== 新增：Redis缓存优化方法 ======================
    def _get_all_recommended_post_ids(self, user_id: int) -> Set[int]:
        """
        获取用户所有已推荐的postId集合（从所有推荐列表key中读取，仅调用1次Redis）
        :param user_id: 用户ID
        :return: 已推荐的postId集合
        """
        try:
            # 匹配该用户的所有推荐列表key（避免用KEYS命令阻塞Redis）
            pattern = f"post:recommended:{user_id}:*"
            cursor = 0
            all_keys = []
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                all_keys.extend(keys)
                if cursor == 0:
                    break

            # 批量读取所有列表内容并合并为集合
            recommended_post_ids = set()
            for key in all_keys:
                post_ids_bytes = self.redis_client.lrange(key, 0, -1)  # 获取列表所有元素
                post_ids = [int(pid.decode('utf-8')) for pid in post_ids_bytes if pid]
                recommended_post_ids.update(post_ids)

            print(f"🔍 [Redis缓存] 用户{user_id}已推荐postId数量：{len(recommended_post_ids)}")
            return recommended_post_ids
        except Exception as e:
            print(f"⚠️ [Redis缓存] 获取已推荐列表异常(user={user_id}): {str(e)}")
            return set()

    def is_post_recommended(self, user_id: int, post_id: int, cached_recommended_set: Set[int] = None) -> bool:
        """
        检查投稿是否已推荐（复用预加载的集合，避免多次Redis调用）
        :param user_id: 用户ID
        :param post_id: 投稿ID
        :param cached_recommended_set: 预加载的已推荐集合（可选，避免重复查询）
        :return: 是否已推荐
        """
        recommended_set = cached_recommended_set or self._get_all_recommended_post_ids(user_id)
        return post_id in recommended_set

    def set_post_recommended_batch(self, user_id: int, post_ids: List[int]):
        """
        批量设置推荐列表缓存（1次Redis调用写入所有postId，5分钟过期）
        :param user_id: 用户ID
        :param post_ids: 本次推荐的postId列表（非空）
        """
        if not post_ids:
            print(f"⚠️ [Redis缓存] 推荐列表为空，无需设置(user={user_id})")
            return

        try:
            # 生成缓存key：包含本次推荐列表的第一个postId
            first_post_id = post_ids[0]
            cache_key = f"post:recommended:{user_id}:{first_post_id}"

            # 原子化批量操作（先删旧key→批量写入→设置过期）
            self.redis_client.delete(cache_key)  # 清理残留
            post_ids_str = [str(pid) for pid in post_ids]
            self.redis_client.rpush(cache_key, *post_ids_str)  # 批量写入列表
            self.redis_client.expire(cache_key, 300)  # 5分钟过期

            print(f"✅ [Redis缓存] 批量设置推荐缓存(user={user_id}, key={cache_key})，包含{len(post_ids)}个投稿，5分钟后过期")
        except Exception as e:
            print(f"⚠️ [Redis缓存] 批量设置异常(user={user_id}): {str(e)}")

    # ====================== 原有方法修改 ======================
    def _processRequestData(self, req: RecommendRequestDTO):
        """处理请求中的视频和交互数据"""
        posts = []
        for post in req.postList:
            post_dict = {
                "post_id": post.postId,
                "title": post.title or "",
                "tags": post.tags or "",
                "category": post.category or ""
            }
            posts.append(post_dict)

        if posts:
            self.postMeta = {v["post_id"]: v for v in posts}
            self.contentService.buildPostVectors(posts)
            self.postFeatures = self.contentService.postVectors.copy()
            self.coldStartService.setCandidatePosts(posts)

        # 处理交互记录
        interactionsMap: Dict[int, List[tuple]] = {}
        for inter in req.interactionList:
            uid = inter.ownerId
            vid = inter.targetPostId
            if uid is None or vid is None:
                continue

            weight = 1.0 if inter.isLike == 1 else (-0.8 if inter.isDislike == 1 else 0.3)
            interactionsMap.setdefault(uid, []).append((vid, weight))

        return interactionsMap

    async def getRecommendationPostList(self, userId: int, isColdStart: bool,
                                        reqBody: RecommendRequestDTO,
                                        pageSize: int = 12,
                                        alpha: float = 0.5,
                                        wDiv: float = 0.2,
                                        wBound: float = 0.15) -> Dict[str, Any]:
        interactionsMap = self._processRequestData(reqBody)
        userInteractions = interactionsMap.get(userId, [])

        # 提取用户已交互的视频ID集合
        interacted_post_ids = {vid for vid, _ in userInteractions}
        print(f"🔍 DEBUG [user={userId}] 已交互视频数量 = {len(interacted_post_ids)}")

        # 提前加载用户所有已推荐的postId（仅1次Redis调用）
        cached_recommended_set = self._get_all_recommended_post_ids(userId)

        # 更新内容画像
        if userInteractions:
            self.contentService.updateUserProfile(userId, userInteractions)

        # ====================== 冷启动路径 ======================
        if isColdStart:
            recs = self.coldStartService.recommend(userId, pageSize)
            # 过滤：已交互 + 已推荐（复用预加载集合，无额外Redis调用）
            recs = [
                item for item in recs
                if item["post_id"] not in interacted_post_ids
                   and not self.is_post_recommended(userId, item["post_id"], cached_recommended_set)
            ]
            # 补充热门视频（同样复用预加载集合）
            if len(recs) < pageSize:
                popular_recs = self.coldStartService._popularRecommendation(pageSize * 2)
                for item in popular_recs:
                    if (item["post_id"] not in interacted_post_ids
                            and not self.is_post_recommended(userId, item["post_id"], cached_recommended_set)
                            and len(recs) < pageSize):
                        recs.append(item)

            # 构建返回结果
            items = [
                RecommendItem(
                    postId=item["post_id"],
                    finalScore=round(item.get("score", 0.0), 4),
                    hybridScore=round(item.get("score", 1.0), 4),
                    reason=item.get("reason", "冷启动推荐")
                ) for item in recs[:pageSize]
            ]
            # 批量设置缓存（1次Redis调用，替代原循环N次setex）
            if items:
                post_ids = [item.postId for item in items]
                self.set_post_recommended_batch(userId, post_ids)

            return {
                "userId": userId,
                "recommendPostList": items,
                "isColdStart": True,
                "message": "冷启动阶段 - 基于注册兴趣标签向量推荐（已过滤已交互/已推荐视频）",
                "actualParams": {"alpha": None, "wDiv": None, "wBound": None},
                "debugQueryParams": {
                    "userId": userId,
                    "isColdStart": True,
                    "pageSize": pageSize
                },
                "debugRequestBody": reqBody.model_dump()
            }

        # ====================== 正常混合推荐路径 ======================
        # 构建排除集合：已交互 + 已推荐（复用预加载集合）
        content_exclude_ids = interacted_post_ids.union(cached_recommended_set)

        # 协同过滤：过滤已交互 + 已推荐（复用预加载集合）
        cfScores = self.getCFScores(
            userId,
            candidateSize=150,
            exclude_post_ids=interacted_post_ids,
            cached_recommended_set=cached_recommended_set  # 传入预加载集合
        )
        # 内容特征：直接排除已交互+已推荐
        contentScores = self.contentService.getContentScores(
            userId,
            candidateSize=150,
            exclude_post_ids=content_exclude_ids
        )

        print(f"🔍 DEBUG [user={userId}] cfScores 数量 = {len(cfScores)}")
        print(f"🔍 DEBUG [user={userId}] contentScores 数量 = {len(contentScores)}")
        print(f"🔍 DEBUG [user={userId}] postFeatures 数量 = {len(self.postFeatures)}")
        print(f"🔍 DEBUG 参数生效情况 → alpha={alpha}, wDiv={wDiv}, wBound={wBound}")

        fusionParams = RecommendParam(
            alpha=alpha,
            wDiv=wDiv,
            wBound=wBound,
            topN=pageSize
        )
        fusedResults = self.fusionService.fuseAndRecommend(
            params=fusionParams,
            cfScores=cfScores,
            contentScores=contentScores,
            postFeatures=self.postFeatures
        )
        # 构建返回结果
        items = []
        for item in fusedResults:
            items.append(RecommendItem(
                postId=item["postId"],
                finalScore=item["finalScore"],
                hybridScore=item["hybridScore"],
                reason="混合推荐 (CF + 内容特征)" if cfScores else "内容驱动推荐"
            ))
        # 批量设置缓存（1次Redis调用）
        if items:
            post_ids = [item.postId for item in items]
            self.set_post_recommended_batch(userId, post_ids)

        return {
            "userId": userId,
            "recommendPostList": items,
            "isColdStart": False,
            "message": f"混合推荐完成 (α={alpha:.2f}, 多样性={wDiv:.2f}, 破圈={wBound:.2f})（已过滤已交互/已推荐视频）",
            "actualParams": {
                "alpha": round(alpha, 4),
                "wDiv": round(wDiv, 4),
                "wBound": round(wBound, 4)
            },
            "debugQueryParams": {
                "userId": userId,
                "isColdStart": False,
                "pageSize": pageSize,
                "alpha": alpha,
                "wDiv": wDiv,
                "wBound": wBound
            },
            "debugRequestBody": reqBody.model_dump()
        }

    def getCFScores(self, userId: int, candidateSize: int = 150,
                    exclude_post_ids: set = None, cached_recommended_set: Set[int] = None) -> Dict[int, float]:
        """
        CF分数获取（优化版：复用预加载的已推荐集合，无额外Redis调用）
        """
        if self.bprModel is None or self.bprModel.user_factors is None:
            return {}

        # 初始化已交互排除集合
        final_exclude_ids = set(exclude_post_ids) if exclude_post_ids else set()

        # 获取原始CF分数（过滤已交互）
        raw_cf_scores = self.bprModel.predict_scores(userId, exclude_post_ids=final_exclude_ids)

        # 过滤已推荐（复用预加载集合）
        recommended_set = cached_recommended_set or self._get_all_recommended_post_ids(userId)
        filtered_cf_scores = {
            post_id: score for post_id, score in raw_cf_scores.items()
            if post_id not in recommended_set
        }

        # 按分数降序取前N个
        sorted_filtered = dict(
            sorted(filtered_cf_scores.items(), key=lambda x: x[1], reverse=True)[:candidateSize]
        )

        print(f"🔍 DEBUG [user={userId}] 过滤已推荐缓存后，CF分数数量 = {len(sorted_filtered)}")
        return sorted_filtered

    def train_cf_model_with_data(self, df: pd.DataFrame, videos: list,
                                 n_items: int = None,
                                 post_to_temp: Dict[int, int] = None,
                                 temp_to_post: Dict[int, int] = None) -> bool:
        """接收 Controller 处理好的 DataFrame 和映射进行训练"""
        try:
            if df.empty:
                print("⚠️ 传入的交互数据为空，无法训练")
                return False

            # 如果没有传入映射（兼容旧调用）
            if n_items is None or post_to_temp is None or temp_to_post is None:
                print("⚠️ 映射参数缺失，使用旧逻辑...")
                n_users = int(df['user_id'].max() + 1)
                n_items_old = max(
                    int(df['post_id'].max() + 1),
                    max((v.get('postId') or v.get('post_id') or 0 for v in videos), default=0) + 100
                )
                success = self.bprModel.fit(df, n_users, n_items_old)
                if success:
                    self.bprModel.save_to_redis(self.redis_client)
                    print("🎉 BPR 模型训练完成（旧逻辑）并已保存到 Redis！")
                return success

            # 新逻辑：使用连续 tempPostId
            n_users = int(df['user_id'].max() + 1) + 10
            print(f"✅ 使用连续 tempPostId 训练 → 用户≈{n_users} | 视频={n_items} | 交互={len(df)}")
            print(f"正反馈比例: {(df['score'] > 0).mean():.1%}")

            success = self.bprModel.fit(df, n_users, n_items, temp_column='tempPostId')
            if success:
                # 保存映射到模型对象（随模型一起持久化）
                self.bprModel.post_to_temp = dict(post_to_temp)
                self.bprModel.temp_to_post = dict(temp_to_post)
                self.bprModel.save_to_redis(self.redis_client)
                print("🎉 BPR 模型训练完成（使用连续 tempPostId）并已成功保存到 Redis！")
                return True
            else:
                print("❌ BPR fit 方法返回失败")
                return False

        except Exception as e:
            print(f"❌ Service 训练异常: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return False