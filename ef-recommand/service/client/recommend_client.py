import random
import time
from typing import List, Dict, Tuple, Optional

import httpx
import nacos
from fastapi import HTTPException

from config.config_manager import config


class RecommendClient:
    """
    Python版“Feign Client”
    支持：
    - Nacos 服务发现
    - 简单负载均衡
    - 实例缓存
    - 统一异常处理
    """

    def __init__(self):
        # ====================== Nacos 配置 ======================
        self.nacos_client = nacos.NacosClient("127.0.0.1:8848")

        # 服务名
        self.video_service_name = config.get("service.video_service")
        self.behavior_service_name = config.get("service.behavior_service")
        self.user_service_name = config.get("service.user_service")

        # ====================== HTTP 配置 ======================
        self.timeout = httpx.Timeout(config.get("http.timeout", 10), connect=5.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # ====================== 本地缓存 ======================
        self._service_cache = {}  # {service_name: [instances]}
        self._cache_expire = {}  # {service_name: timestamp}
        self.cache_ttl = 10  # 秒

    # ====================== 服务发现 ======================
    def _get_service_instances(self, service_name: str):
        now = time.time()

        # 缓存命中
        if (
            service_name in self._service_cache
            and now < self._cache_expire.get(service_name, 0)
        ):
            return self._service_cache[service_name]

        try:
            instances = self.nacos_client.list_naming_instance(service_name)
            hosts = instances.get("hosts", [])

            if not hosts:
                raise HTTPException(
                    status_code=503,
                    detail=f"{service_name} 无可用实例"
                )

            # 更新缓存
            self._service_cache[service_name] = hosts
            self._cache_expire[service_name] = now + self.cache_ttl

            return hosts

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Nacos 服务发现失败: {str(e)}"
            )

    def _choose_instance(self, service_name: str) -> str:
        hosts = self._get_service_instances(service_name)

        # 简单随机负载均衡
        instance = random.choice(hosts)

        ip = instance["ip"]
        port = instance["port"]

        return f"http://{ip}:{port}"

    # ====================== 通用请求方法 ======================
    async def _get(self, service_name: str, path: str, params=None):
        base_url = self._choose_instance(service_name)
        url = f"{base_url}{path}"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"{service_name} 返回错误: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"无法连接到 {service_name}: {str(e)}"
            )

    async def _post(self, service_name: str, path: str, json=None):
        base_url = self._choose_instance(service_name)
        url = f"{base_url}{path}"

        try:
            response = await self.client.post(url, json=json)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"{service_name} 返回错误: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"无法连接到 {service_name}: {str(e)}"
            )

    # ====================== 具体业务接口 ======================

    async def get_videos_metadata(self, video_ids: Optional[List[int]] = None) -> List[Dict]:
        params = {}
        if video_ids:
            params["videoIds"] = ",".join(map(str, video_ids))

        return await self._get(
            self.video_service_name,
            "/api/videos/metadata",
            params=params
        )

    async def get_user_interactions(self, user_id: int) -> List[Tuple[int, float]]:
        data = await self._get(
            self.behavior_service_name,
            f"/api/interactions/{user_id}"
        )

        interactions = []
        for item in data:
            vid = item.get("video_id") or item.get("videoId")
            weight = item.get("weight") or item.get("score") or item.get("feedback", 0)
            if vid is not None:
                interactions.append((int(vid), float(weight)))

        return interactions

    async def get_all_videos_for_content(self) -> List[Dict]:
        return await self._get(
            self.video_service_name,
            "/api/videos/all"
        )

    async def notify_interaction(self, user_id: int, video_id: int, action: str, value: float = 1.0):
        try:
            await self._post(
                self.behavior_service_name,
                "/api/interactions/notify",
                json={
                    "user_id": user_id,
                    "video_id": video_id,
                    "action": action,
                    "value": value
                }
            )
        except Exception:
            # 不影响主流程
            pass

    # ====================== 关闭连接（可选） ======================
    async def close(self):
        await self.client.aclose()


# ====================== 单例 ======================
recommend_client = RecommendClient()