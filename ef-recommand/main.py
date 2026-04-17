from fastapi import FastAPI
from controller.recommend_controller import router as recommend_router

app = FastAPI(
    title="视频推荐服务",
    description="基于协同过滤 + 内容特征融合 + 用户可控的混合推荐服务（四模块架构）",
    version="1.0.0"
)

app.include_router(recommend_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)