"""
Bangumi API客户端
处理HTTP请求、认证、分页和错误处理
"""
import requests
import time
from typing import Dict, List, Optional
from config.config import (
    BANGUMI_BASE_URL,
    BANGUMI_ACCESS_TOKEN,
    REQUEST_TIMEOUT,
    RETRY_TIMES,
    RETRY_DELAY,
    RATE_LIMIT_DELAY,
    PAGE_SIZE,
    ANIME_TYPE,
    MIN_RANK
)


class BangumiAPIClient:
    """Bangumi API客户端类"""

    def __init__(self):
        self.base_url = BANGUMI_BASE_URL
        self.access_token = BANGUMI_ACCESS_TOKEN
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        """设置请求头"""
        if not self.access_token:
            raise ValueError("BANGUMI_ACCESS_TOKEN未设置，请在.env文件中配置")

        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "onebyten/bgmlanfanpaihang (https://github.com/11111111111ge1/bgm_lanfanpaihang)",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        发送HTTP请求，带重试机制

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(RETRY_TIMES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=REQUEST_TIMEOUT,
                    **kwargs
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise Exception("认证失败：Token无效或已过期")
                elif response.status_code == 429:
                    print(f"触发速率限制，等待{RETRY_DELAY * (attempt + 1)}秒后重试...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    if attempt < RETRY_TIMES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                print(f"请求超时，尝试 {attempt + 1}/{RETRY_TIMES}")
                if attempt < RETRY_TIMES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                print(f"请求异常: {e}")
                if attempt < RETRY_TIMES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        raise Exception("请求失败，已达到最大重试次数")

    def search_worst_anime(self, offset: int = 0, limit: int = PAGE_SIZE) -> Dict:
        """
        搜索排名靠后的动漫

        Args:
            offset: 偏移量
            limit: 每页数量

        Returns:
            搜索结果
        """
        # limit 和 offset 应该作为 URL 查询参数
        endpoint = f"/v0/search/subjects?limit={limit}&offset={offset}"

        # payload 只包含搜索条件
        payload = {
            "keyword": "",
            "sort": "rank",
            "filter": {
                "type": [ANIME_TYPE],
                "rank": [f">{MIN_RANK}"],
                "nsfw": True
            }
        }

        print(f"正在获取数据: offset={offset}, limit={limit}")

        # 打印请求信息到文件
        import json
        import os
        from datetime import datetime

        # 创建调试输出目录
        debug_dir = "output/debug"
        os.makedirs(debug_dir, exist_ok=True)

        # 生成文件名（包含时间戳和offset）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request_file = os.path.join(debug_dir, f"api_request_offset_{offset}_{timestamp}.json")
        response_file = os.path.join(debug_dir, f"api_response_offset_{offset}_{timestamp}.json")

        # 保存请求信息
        request_info = {
            "url": f"{self.base_url}{endpoint}",
            "method": "POST",
            "headers": dict(self.session.headers),
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }

        with open(request_file, "w", encoding="utf-8") as f:
            json.dump(request_info, f, ensure_ascii=False, indent=2)

        print(f"API 请求已保存到: {request_file}")

        # 发送请求
        result = self._make_request("POST", endpoint, json=payload)

        # 保存响应信息
        with open(response_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"API 响应已保存到: {response_file}")

        # 请求间隔，避免触发速率限制
        time.sleep(RATE_LIMIT_DELAY)

        return result
