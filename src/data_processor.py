"""
数据处理器
提取、转换和验证API响应数据
"""
from typing import Dict, List, Optional
from datetime import datetime


class DataProcessor:
    """数据处理类"""

    def __init__(self):
        self.all_anime = []

    def extract_anime_data(self, api_response: Dict) -> List[Dict]:
        """
        从API响应中提取动漫数据

        Args:
            api_response: API响应数据

        Returns:
            提取的动漫列表
        """
        if not api_response or "data" not in api_response:
            return []

        anime_list = []
        for item in api_response.get("data", []):

            rating = item.get("rating", {})

            anime_data = {
                "id": item.get("id"),
                "name": item.get("name", ""),
                "name_cn": item.get("name_cn", ""),
                "score": rating.get("score", 0),
                "rank": rating.get("rank", 0),
                "rating_total": rating.get("total", 0),  # 评分人数
                "nsfw": item.get("nsfw", False),
                "date": item.get("date", ""),
                "image": item.get("image", ""),
                "summary": item.get("summary", "")
            }
            anime_list.append(anime_data)

        return anime_list

    def sort_by_score(self, anime_list: List[Dict]) -> List[Dict]:
        """
        按评分排序（从低到高）

        Args:
            anime_list: 动漫列表

        Returns:
            排序后的列表
        """
        return sorted(anime_list, key=lambda x: (x.get("score", 0), -x.get("rank", 0)))

    def separate_nsfw(self, anime_list: List[Dict]) -> tuple:
        """
        分离普通内容和受限内容

        Args:
            anime_list: 动漫列表

        Returns:
            (普通内容列表, 受限内容列表)
        """
        normal = [anime for anime in anime_list if not anime.get("nsfw", False)]
        nsfw = [anime for anime in anime_list if anime.get("nsfw", False)]
        return normal, nsfw
