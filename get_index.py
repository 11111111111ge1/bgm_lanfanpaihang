"""
获取Bangumi索引信息的独立脚本
调用以下API:
1. GET /v0/indices/{index_id} - 获取索引基本信息
2. GET /v0/indices/{index_id}/subjects - 获取索引中的条目列表
"""
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from config.config import (
    BANGUMI_BASE_URL,
    BANGUMI_ACCESS_TOKEN,
    REQUEST_TIMEOUT,
    RETRY_TIMES,
    RETRY_DELAY,
    RATE_LIMIT_DELAY,
    OLD_INDEX_ID
)


def get_index_by_id(index_id: int) -> dict:
    """
    根据ID获取索引信息

    Args:
        index_id: 索引ID

    Returns:
        索引信息字典
    """
    if not BANGUMI_ACCESS_TOKEN:
        raise ValueError("BANGUMI_ACCESS_TOKEN未设置，请在.env文件中配置")

    url = f"{BANGUMI_BASE_URL}/v0/indices/{index_id}"
    headers = {
        "Authorization": f"Bearer {BANGUMI_ACCESS_TOKEN}",
        "User-Agent": "bgmlanfanpaihang/1.0",
        "Accept": "application/json"
    }

    print(f"正在获取索引 ID: {index_id}")
    print(f"请求URL: {url}")

    for attempt in range(RETRY_TIMES):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                print(f"✓ 成功获取索引信息")
                return response.json()
            elif response.status_code == 404:
                print(f"✗ 索引不存在 (ID: {index_id})")
                return None
            elif response.status_code == 401:
                raise Exception("认证失败：Token无效或已过期")
            else:
                print(f"请求失败，状态码: {response.status_code}")
                if attempt < RETRY_TIMES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    import time
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    response.raise_for_status()

        except requests.exceptions.Timeout:
            print(f"请求超时，尝试 {attempt + 1}/{RETRY_TIMES}")
            if attempt < RETRY_TIMES - 1:
                import time
                time.sleep(RETRY_DELAY)
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            if attempt < RETRY_TIMES - 1:
                import time
                time.sleep(RETRY_DELAY)
            else:
                raise

    raise Exception("请求失败，已达到最大重试次数")


def get_index_subjects(index_id: int, subject_type: int = 2, limit: int = 30, offset: int = 0) -> dict:
    """
    获取索引中的条目列表

    Args:
        index_id: 索引ID
        subject_type: 条目类型 (1=书籍, 2=动画, 3=音乐, 4=游戏, 6=三次元)
        limit: 每页数量
        offset: 偏移量

    Returns:
        条目列表数据
    """
    if not BANGUMI_ACCESS_TOKEN:
        raise ValueError("BANGUMI_ACCESS_TOKEN未设置，请在.env文件中配置")

    url = f"{BANGUMI_BASE_URL}/v0/indices/{index_id}/subjects"
    params = {
        "type": subject_type,
        "limit": limit,
        "offset": offset
    }
    headers = {
        "Authorization": f"Bearer {BANGUMI_ACCESS_TOKEN}",
        "User-Agent": "bgmlanfanpaihang/1.0",
        "Accept": "application/json"
    }

    print(f"正在获取索引条目列表 (offset={offset}, limit={limit})")

    for attempt in range(RETRY_TIMES):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"✗ 索引不存在或无条目 (ID: {index_id})")
                return None
            elif response.status_code == 401:
                raise Exception("认证失败：Token无效或已过期")
            else:
                print(f"请求失败，状态码: {response.status_code}")
                if attempt < RETRY_TIMES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
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


def get_all_index_subjects(index_id: int, subject_type: int = 2) -> list:
    """
    获取索引中的所有条目（自动分页）

    Args:
        index_id: 索引ID
        subject_type: 条目类型

    Returns:
        所有条目列表
    """
    all_subjects = []
    offset = 0
    limit = 50  # 每页50条

    while True:
        result = get_index_subjects(index_id, subject_type, limit, offset)

        if not result or "data" not in result:
            break

        subjects = result.get("data", [])
        if not subjects:
            break

        all_subjects.extend(subjects)
        print(f"✓ 已获取 {len(all_subjects)} 条目")

        total = result.get("total", 0)
        if len(all_subjects) >= total:
            break

        offset += limit
        time.sleep(RATE_LIMIT_DELAY)  # 避免触发速率限制

    return all_subjects


def save_index_to_file(index_data: dict, index_id: int, output_dir: str = "output/indices"):
    """
    保存索引信息到JSON文件

    Args:
        index_data: 索引数据
        index_id: 索引ID
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"index_{index_id}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # 保存数据
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 索引信息已保存到: {filepath}")
    return filepath


def main():
    """主函数"""
    print("=" * 60)
    print("Bangumi 索引信息获取工具")
    print("=" * 60)

    try:
        # 从配置文件读取索引ID
        if not OLD_INDEX_ID:
            print("✗ 配置文件中未设置 OLD_INDEX_ID")
            print("请在 config/config.py 中设置 OLD_INDEX_ID")
            return

        index_id = OLD_INDEX_ID
        print(f"\n使用配置的索引ID: {index_id}")

        # 1. 获取索引基本信息
        print("\n" + "=" * 60)
        print("步骤 1/3: 获取索引基本信息")
        print("=" * 60)
        index_data = get_index_by_id(index_id)

        if not index_data:
            print("\n✗ 未找到该索引")
            return

        # 显示基本信息
        print("\n索引信息:")
        print(f"  ID: {index_data.get('id', 'N/A')}")
        print(f"  标题: {index_data.get('title', 'N/A')}")
        desc = index_data.get('desc', 'N/A')
        print(f"  描述: {desc[:100]}..." if len(desc) > 100 else f"  描述: {desc}")
        print(f"  创建者ID: {index_data.get('creator_id', 'N/A')}")
        print(f"  条目总数: {index_data.get('total', 'N/A')}")

        # 2. 获取索引中的所有动画条目
        print("\n" + "=" * 60)
        print("步骤 2/3: 获取索引中的动画条目列表")
        print("=" * 60)
        subjects = get_all_index_subjects(index_id, subject_type=2)

        if subjects:
            print(f"\n✓ 共获取 {len(subjects)} 个动画条目")
        else:
            print("\n⚠ 该索引中没有动画条目")

        # 3. 保存数据
        print("\n" + "=" * 60)
        print("步骤 3/3: 保存数据到文件")
        print("=" * 60)

        # 合并数据
        complete_data = {
            "index_info": index_data,
            "subjects": subjects,
            "metadata": {
                "fetch_date": datetime.now().isoformat(),
                "total_subjects": len(subjects),
                "subject_type": 2,
                "subject_type_name": "动画"
            }
        }

        filepath = save_index_to_file(complete_data, index_id)

        # 显示统计信息
        print(f"\n数据统计:")
        print(f"  索引ID: {index_id}")
        print(f"  索引标题: {index_data.get('title', 'N/A')}")
        print(f"  动画条目数: {len(subjects)}")
        print(f"  保存位置: {filepath}")

        print("\n" + "=" * 60)
        print("✓ 所有操作完成")
        print("=" * 60)

    except ValueError:
        print("✗ 请输入有效的数字ID")
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
