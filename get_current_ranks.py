import re
import requests
import time
import json
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv


##等sai老板修，这个操作只能对公开目录生效，私密目录没法用
# 加载环境变量
load_dotenv()

# 获取访问令牌
BANGUMI_ACCESS_TOKEN = os.getenv("BANGUMI_ACCESS_TOKEN")

def get_latest_index_file(indices_dir: str = "output/indices") -> str:
    """获取最新的index文件路径"""
    indices_path = Path(indices_dir)
    if not indices_path.exists():
        raise FileNotFoundError(f"目录不存在: {indices_dir}")

    # 获取所有index_*.json文件
    index_files = list(indices_path.glob("index_*.json"))
    if not index_files:
        raise FileNotFoundError(f"在 {indices_dir} 中未找到index文件")

    # 按修改时间排序，获取最新的
    latest_file = max(index_files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)

def extract_subject_ids(desc_text: str) -> List[Dict]:
    """从描述文本中提取所有条目ID和排名位置

    Returns:
        List[Dict]: 包含 {'id': int, 'rank_position': int} 的列表
    """
    # 匹配格式: 数字 空格 任意字符 [url=https://bgm.tv/subject/数字]
    # 例如: "9 - [url=https://bgm.tv/subject/121724]"
    # 或: "34 NEW [url=https://bgm.tv/subject/328012]"
    pattern = r'(\d+)\s+[^\[]*\[url=https://bgm\.tv/subject/(\d+)\]'
    matches = re.findall(pattern, desc_text)

    results = []
    for rank_pos, subject_id in matches:
        results.append({
            'id': int(subject_id),
            'rank_position': int(rank_pos)
        })

    return results

def get_subject_rank(subject_id: int, rank_position: int = None, retry_times: int = 3, retry_delay: int = 2) -> Dict:
    """获取指定条目的rank信息，带重试机制

    Args:
        subject_id: 条目ID
        rank_position: 在TOP100中的排名位置
        retry_times: 重试次数
        retry_delay: 重试延迟（秒）

    Returns:
        包含条目信息的字典，其中rank字段为TOP100排名位置
    """
    url = f"https://api.bgm.tv/v0/subjects/{subject_id}"

    # 设置请求头
    headers = {
        "User-Agent": "bgmlanfanpaihang/1.0",
        "Content-Type": "application/json"
    }
    if BANGUMI_ACCESS_TOKEN:
        headers['Authorization'] = f'Bearer {BANGUMI_ACCESS_TOKEN}'

    for attempt in range(retry_times):
        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'id': subject_id,
                    'name': data.get('name', ''),
                    'name_cn': data.get('name_cn', ''),
                    'rank': rank_position,  # 使用TOP100排名位置
                    'score': data.get('rating', {}).get('score', None),
                    'total': data.get('rating', {}).get('total', None)
                }
            elif response.status_code == 401:
                print(f"  认证失败：Token无效或已过期")
                return {
                    'id': subject_id,
                    'name': '',
                    'name_cn': '',
                    'rank': rank_position,
                    'score': None,
                    'total': None,
                    'error': '认证失败'
                }
            elif response.status_code == 429:
                print(f"  触发速率限制，等待{retry_delay * (attempt + 1)}秒后重试...")
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                print(f"  请求失败，状态码: {response.status_code}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay)
                    continue
                response.raise_for_status()

        except requests.exceptions.Timeout:
            print(f"  请求超时，尝试 {attempt + 1}/{retry_times}")
            if attempt < retry_times - 1:
                time.sleep(retry_delay)
            else:
                return {
                    'id': subject_id,
                    'name': '',
                    'name_cn': '',
                    'rank': rank_position,
                    'score': None,
                    'total': None,
                    'error': '请求超时'
                }
        except Exception as e:
            print(f"  请求异常: {e}")
            if attempt < retry_times - 1:
                time.sleep(retry_delay)
            else:
                return {
                    'id': subject_id,
                    'name': '',
                    'name_cn': '',
                    'rank': rank_position,
                    'score': None,
                    'total': None,
                    'error': str(e)
                }

    return {
        'id': subject_id,
        'name': '',
        'name_cn': '',
        'rank': rank_position,
        'score': None,
        'total': None,
        'error': '请求失败，已达到最大重试次数'
    }

def main():
    # 检查访问令牌
    if not BANGUMI_ACCESS_TOKEN:
        print("错误: 未找到 BANGUMI_ACCESS_TOKEN")
        print("请在 .env 文件中设置 BANGUMI_ACCESS_TOKEN")
        return

    # 获取最新的index文件
    try:
        latest_index = get_latest_index_file()
        print(f"读取最新的index文件: {latest_index}\n")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    # 读取index文件并提取desc字段
    try:
        with open(latest_index, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        # desc字段在index_info对象中
        desc_text = index_data.get('index_info', {}).get('desc', '')
        if not desc_text:
            print("错误: index文件中没有找到desc字段")
            return

        print(f"从desc字段中提取条目ID...\n")
    except Exception as e:
        print(f"读取index文件失败: {e}")
        return

    subject_ids = extract_subject_ids(desc_text)
    print(f"找到 {len(subject_ids)} 个条目\n")

    results = []
    for item in subject_ids:
        subject_id = item['id']
        rank_position = item['rank_position']
        print(f"正在获取条目 {subject_id} (排名位置: {rank_position}) 的信息...")
        result = get_subject_rank(subject_id, rank_position)
        results.append(result)

        # 打印结果
        if 'error' in result:
            print(f"  ❌ 错误: {result['error']}\n")
        else:
            name = result['name_cn'] or result['name']
            rank = result['rank'] if result['rank'] else 'N/A'
            score = result['score'] if result['score'] else 'N/A'
            print(f"  ✓ {name}")
            print(f"    TOP100排名: {rank}")
            print(f"    评分: {score}")
            print(f"    评分人数: {result['total']}\n")

        # 避免请求过快
        time.sleep(0.5)

    # 输出汇总
    print("\n" + "="*60)
    print("汇总结果:")
    print("="*60)
    for result in results:
        if 'error' not in result:
            name = result['name_cn'] or result['name']
            rank = result['rank'] if result['rank'] else 'N/A'
            print(f"ID {result['id']:6d} | TOP100排名 {str(rank):>3s} | {name}")

    # 保存结果到JSON文件
    output_dir = Path("output/ranks")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ranks_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
