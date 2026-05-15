from fastapi import APIRouter, HTTPException, Query, Body
from schemas.recommend import RecommendRequestDTO, RecommendResponse, RecommendTagItem
from service.recommend_service import RecommendService
import requests
import pandas as pd
from typing import Dict, List, Any

router = APIRouter(prefix="/recommend", tags=["推荐服务"])

recommendService = RecommendService()


@router.post("/list", response_model=RecommendResponse)
async def getRecommendPostList(
        userId: int = Query(..., description="用户ID"),
        isColdStart: bool = Query(..., description="是否冷启动"),
        pageSize: int = Query(12, ge=1, le=50, description="每页数量"),
        alpha: float = Query(0.5, description="CF权重"),
        wDiv: float = Query(0.2, description="多样性权重"),
        wBound: float = Query(0.15, description="破圈权重"),
        body: RecommendRequestDTO = Body(...)
):
    try:
        result = await recommendService.getRecommendationPostList(
            userId=userId,
            isColdStart=isColdStart,
            reqBody=body,
            pageSize=pageSize,
            alpha=alpha,
            wDiv=wDiv,
            wBound=wBound
        )
        return RecommendResponse(**result)

    except Exception as e:
        print(f"❌ 推荐服务异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推荐服务异常: {str(e)}")


@router.post("/train/cf-model", response_model=dict)
async def train_cf_model():
    """手动触发 BPR 模型训练（支持 userId 连续映射）"""
    try:
        # 1. 获取交互记录
        inter_resp = requests.get("http://localhost:8093/recommend/interaction/all", timeout=15)
        inter_resp.raise_for_status()
        inter_result = inter_resp.json()

        # 2. 获取视频列表
        video_resp = requests.get("http://localhost:8093/recommend/video/all", timeout=15)
        video_resp.raise_for_status()
        video_result = video_resp.json()

        interactions = inter_result.get('data') if isinstance(inter_result, dict) else None
        videos = video_result.get('data') if isinstance(video_result, dict) else None

        if not interactions or not isinstance(interactions, list):
            return {"success": False, "message": "交互数据为空或格式错误"}

        df = pd.DataFrame(interactions)
        df = df.rename(columns={
            'ownerId': 'user_id',
            'targetPostId': 'post_id',
            'isLike': 'is_like',
            'isDislike': 'is_dislike'
        })

        def compute_score(row):
            if row.get('is_like') == 1:
                return 4.0
            elif row.get('is_dislike') == 1:
                return -2.0
            else:
                return 1.0

        df['score'] = df.apply(compute_score, axis=1)
        df = df.dropna(subset=['user_id', 'post_id'])
        df['user_id'] = df['user_id'].astype(int)
        df['post_id'] = df['post_id'].astype(int)

        if df.empty:
            return {"success": False, "message": "过滤后没有有效交互数据"}

        # ==================== 视频映射 ====================
        valid_posts = []
        seen = set()
        for v in videos or []:
            pid = v.get('postId') or v.get('post_id')
            if pid is not None:
                pid = int(pid)
                if pid not in seen:
                    seen.add(pid)
                    valid_posts.append({**v, 'postId': pid})

        valid_posts.sort(key=lambda x: x['postId'])
        post_to_temp: Dict[int, int] = {item['postId']: idx for idx, item in enumerate(valid_posts)}
        temp_to_post: Dict[int, int] = {idx: item['postId'] for idx, item in enumerate(valid_posts)}
        n_items = len(valid_posts)

        # ==================== 用户映射 ====================
        valid_users = sorted(df['user_id'].unique())
        user_to_temp: Dict[int, int] = {uid: idx for idx, uid in enumerate(valid_users)}
        temp_to_user: Dict[int, int] = {idx: uid for idx, uid in enumerate(valid_users)}
        n_users = len(valid_users)

        # ==================== 数据过滤并添加 temp 列 ====================
        df_filtered = df[df['post_id'].isin(post_to_temp.keys())].copy()
        df_filtered['tempPostId'] = df_filtered['post_id'].map(post_to_temp)
        df_filtered['tempUserId'] = df_filtered['user_id'].map(user_to_temp)

        df_filtered = df_filtered.dropna(subset=['tempUserId', 'tempPostId'])
        df_filtered['tempUserId'] = df_filtered['tempUserId'].astype(int)
        df_filtered['tempPostId'] = df_filtered['tempPostId'].astype(int)

        # 调用 Service 训练
        success = recommendService.train_cf_model_with_data(
            df=df_filtered,
            videos=valid_posts,
            n_users=n_users,
            n_items=n_items,
            user_to_temp=user_to_temp,
            temp_to_user=temp_to_user,
            post_to_temp=post_to_temp,
            temp_to_post=temp_to_post
        )

        if success:
            return {
                "success": True,
                "message": f"✅ BPR 模型训练完成！有效用户={n_users}，有效视频={n_items}",
                "tip": "现在 CF 模块对新用户支持更好"
            }
        else:
            return {"success": False, "message": "训练失败，请查看控制台日志"}

    except Exception as e:
        print(f"❌ Controller 处理异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ====================== 冷启动兴趣标签接口 ======================
@router.get("/cold-start/tags", response_model=List[RecommendTagItem])
async def get_cold_start_tags(
        limit: int = Query(50, ge=10, le=200, description="返回的兴趣标签数量")
):
    """
    获取冷启动注册用的兴趣标签列表
    返回结构：[{"tagName": "美食"}, {"tagName": "旅行"}, ...]
    """
    try:
        video_resp = requests.get("http://localhost:8093/recommend/video/all", timeout=20)
        video_resp.raise_for_status()
        video_result = video_resp.json()

        videos: List[Dict] = video_result.get('data') if isinstance(video_result, dict) else video_result
        if not isinstance(videos, list):
            videos = []

        # 调用 Service 获取标签
        result = recommendService.get_cold_start_tags(videos, limit=limit)

        tags_list: List[str] = result.get("tags", [])

        # 转换为 Java 端需要的格式
        tag_items = [{"tagName": tag} for tag in tags_list]

        return tag_items

    except requests.exceptions.RequestException as e:
        print(f"❌ [ColdStart Tags] 请求视频接口失败: {e}")
        default_tags = ["科技", "生活", "娱乐", "美食", "旅行", "教育"]
        tag_items = [{"tagName": tag} for tag in default_tags[:limit]]
        return tag_items

    except Exception as e:
        print(f"❌ [ColdStart Tags] 处理异常: {e}")
        import traceback
        traceback.print_exc()
        default_tags = ["科技", "生活", "娱乐", "美食", "旅行", "教育"]
        tag_items = [{"tagName": tag} for tag in default_tags[:limit]]
        return tag_items