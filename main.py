"""
Bangumi烂番排行数据获取工具 - 主入口
"""
import argparse
from datetime import datetime
from src.api_client import BangumiAPIClient
from src.data_processor import DataProcessor
from src.exporters import JSONExporter
from config.config import TOP_N


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="获取Bangumi最差动漫排行数据")
    parser.add_argument("--year", type=int, default=datetime.now().year,
                        help="年份（默认：当前年份）")
    parser.add_argument("--limit", type=int, default=TOP_N,
                        help=f"结果数量（默认：{TOP_N}）")
    args = parser.parse_args()

    print("=" * 60)
    print("Bangumi烂番排行数据获取工具")
    print("=" * 60)
    print(f"年份: {args.year}")
    print(f"目标数量: {args.limit}")
    print("-" * 60)

    try:
        # 初始化组件
        api_client = BangumiAPIClient()
        data_processor = DataProcessor()
        json_exporter = JSONExporter()

        # 获取数据
        print("\n[1/4] 正在从Bangumi API获取数据...")
        all_anime = []
        offset = 0
        page = 1

        while True:
            result = api_client.search_worst_anime(offset=offset)

            if not result or "data" not in result:
                print("没有更多数据")
                break

            anime_list = data_processor.extract_anime_data(result)
            if not anime_list:
                print("没有更多数据")
                break

            all_anime.extend(anime_list)
            print(f"  第 {page} 页: 获取到 {len(anime_list)} 条数据，累计 {len(all_anime)} 条")

            # 检查是否还有更多数据
            total = result.get("total", 0)
            if offset + len(anime_list) >= total:
                print(f"已获取所有数据，共 {len(all_anime)} 条")
                break

            offset += len(anime_list)
            page += 1

        # 处理数据
        print("\n[2/4] 正在处理数据...")
        sorted_anime = data_processor.sort_by_score(all_anime)
        print(f"  已按评分排序，共 {len(sorted_anime)} 条")

        # 分离普通和受限内容
        print("\n[3/4] 正在分离普通和受限内容...")
        normal_list, nsfw_list = data_processor.separate_nsfw(sorted_anime)
        print(f"  普通内容: {len(normal_list)} 条")
        print(f"  受限内容: {len(nsfw_list)} 条")

        # 导出数据
        print("\n[4/4] 正在导出数据...")
        json_exporter.export(normal_list, nsfw_list, year=args.year, top_n=args.limit)

        print("\n" + "=" * 60)
        print("[OK] 数据获取完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
