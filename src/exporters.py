"""
数据导出器
支持JSON格式导出
"""
import json
import os
from datetime import datetime
from typing import Dict, List
from config.config import JSON_OUTPUT_DIR


class JSONExporter:
    """JSON导出器"""

    def __init__(self):
        self.output_dir = JSON_OUTPUT_DIR

    def export(self, normal_list: List[Dict], nsfw_list: List[Dict],
               year: int = None, top_n: int = 100) -> str:
        """
        导出为JSON格式

        Args:
            normal_list: 普通内容列表
            nsfw_list: 受限内容列表
            year: 年份
            top_n: 导出前N条

        Returns:
            输出文件路径
        """
        if year is None:
            year = datetime.now().year

        # 合并 normal 和 nsfw 列表
        all_anime = normal_list + nsfw_list

        # 按 rank 从大到小排序
        sorted_anime = sorted(all_anime, key=lambda x: -x.get("rank", 0))

        # 取前 top_n 条
        top_anime = sorted_anime[:top_n]

        # 添加排名位置（rank_position）
        for idx, anime in enumerate(top_anime, 1):
            anime["rank_position"] = idx

        # 分离 normal 和 nsfw
        normal_output = [anime for anime in top_anime if not anime.get("nsfw", False)]
        nsfw_output = [anime for anime in top_anime if anime.get("nsfw", False)]

        # 构建输出数据
        output_data = {
            "metadata": {
                "fetch_date": datetime.now().isoformat(),
                "total_results": len(top_anime),
                "year": year,
                "normal_count": len(normal_output),
                "nsfw_count": len(nsfw_output)
            },
            "normal": normal_output,
            "nsfw": nsfw_output
        }

        # 生成文件名
        filename = f"bangumi_worst_anime_{year}.json"
        filepath = os.path.join(self.output_dir, filename)

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] JSON文件已导出: {filepath}")
        print(f"  - 总计: {len(top_anime)} 条（按rank从大到小排序）")
        print(f"  - 普通内容: {len(normal_output)} 条")
        print(f"  - 受限内容: {len(nsfw_output)} 条")

        return filepath
