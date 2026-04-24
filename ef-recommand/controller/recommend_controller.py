from fastapi import APIRouter, HTTPException, Query, Body
from schemas.recommend import RecommendRequestDTO, RecommendResponse
from service.recommend_service import RecommendService
import requests
import pandas as pd
from typing import Dict

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
    """手动触发 BPR 模型训练（数据拉取和预处理放在 Controller 中）"""
    try:
        print("📡 Controller 开始拉取训练数据...")

        # 1. 获取交互记录
        inter_resp = requests.get("http://localhost:8093/recommend/interaction/all", timeout=15)
        inter_resp.raise_for_status()
        inter_result = inter_resp.json()

        # 2. 获取视频列表
        video_resp = requests.get("http://localhost:8093/recommend/video/all", timeout=15)
        video_resp.raise_for_status()
        video_result = video_resp.json()

        # 提取 data
        interactions = inter_result.get('data') if isinstance(inter_result, dict) else None
        videos = video_result.get('data') if isinstance(video_result, dict) else None

        if not interactions or not isinstance(interactions, list):
            return {"success": False, "message": "交互数据为空或格式错误"}

        # 转为 DataFrame 并处理
        df = pd.DataFrame(interactions)

        # 字段映射
        df = df.rename(columns={
            'ownerId': 'user_id',
            'targetPostId': 'post_id',
            'isLike': 'is_like',
            'isDislike': 'is_dislike'
        })

        # 构造 score 列
        def compute_score(row):
            if row.get('is_like') == 1:
                return 4.0
            elif row.get('is_dislike') == 1:
                return -2.0
            else:
                return 1.0

        df['score'] = df.apply(compute_score, axis=1)

        # 数据清理
        df = df.dropna(subset=['user_id', 'post_id'])
        df['user_id'] = df['user_id'].astype(int)
        df['post_id'] = df['post_id'].astype(int)

        if df.empty:
            return {"success": False, "message": "过滤后没有有效交互数据"}

        print(f"✅ Controller 数据预处理完成 → 交互条数 = {len(df)}")

        # ==================== 新增：创建 postId → tempPostId 连续映射 ====================
        valid_posts = []
        seen = set()
        for v in videos or []:
            pid = v.get('postId') or v.get('post_id')
            if pid is not None:
                pid = int(pid)
                if pid not in seen:
                    seen.add(pid)
                    valid_posts.append({**v, 'postId': pid})  # 确保键一致

        if not valid_posts:
            return {"success": False, "message": "视频列表为空，无法创建映射"}

        valid_posts.sort(key=lambda x: x['postId'])  # 保证映射稳定
        post_to_temp: Dict[int, int] = {item['postId']: idx for idx, item in enumerate(valid_posts)}
        temp_to_post: Dict[int, int] = {idx: item['postId'] for idx, item in enumerate(valid_posts)}
        n_items = len(valid_posts)

        print(f"✅ 创建连续映射完成 → 有效视频数 = {n_items} | tempPostId 范围: 0 ~ {n_items-1}")

        # 过滤并添加 tempPostId
        df_filtered = df[df['post_id'].isin(post_to_temp.keys())].copy()
        if df_filtered.empty:
            return {"success": False, "message": "过滤后无有效交互数据"}

        df_filtered['tempPostId'] = df_filtered['post_id'].map(post_to_temp)
        dropped = len(df) - len(df_filtered)
        print(f"交互数据过滤: {len(df)} → {len(df_filtered)} 条 (丢弃 {dropped} 条历史无效视频交互)")

        # 调用 Service 进行训练（传入映射）
        success = recommendService.train_cf_model_with_data(
            df=df_filtered,
            videos=valid_posts,
            n_items=n_items,
            post_to_temp=post_to_temp,
            temp_to_post=temp_to_post
        )

        if success:
            return {
                "success": True,
                "message": "✅ BPR 协同过滤模型训练完成并已保存到 Redis！（使用连续 tempPostId）",
                "tip": "现在可以正常使用非冷启动推荐了"
            }
        else:
            return {"success": False, "message": "训练失败，请查看控制台日志"}

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求 Java 服务失败: {e}")
        return {"success": False, "message": f"请求后端失败: {str(e)}"}
    except Exception as e:
        print(f"❌ Controller 处理异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))