"""
Bangumi索引上传脚本
将烂番排行数据上传到Bangumi索引
"""
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置参数
BANGUMI_BASE_URL = "https://api.bgm.tv"
BANGUMI_ACCESS_TOKEN = os.getenv("BANGUMI_ACCESS_TOKEN")
NEW_INDEX_ID = 87084  # 今年的索引ID
OLD_INDEX_ID = 74044  # 去年的索引ID
RATE_LIMIT_DELAY = 1  # API调用间隔（秒）
RETRY_TIMES = 3  # 重试次数
RETRY_DELAY = 2  # 重试延迟（秒）

# 数据文件路径
DATA_FILE = Path(__file__).parent / "output" / "json" / "bangumi_worst_anime_2026.json"
LAST_YEAR_INDICES_DIR = Path(__file__).parent / "output" / "indices"
LAST_YEAR_RANKS_DIR = Path(__file__).parent / "output" / "ranks"


class IndexUploader:
    """索引上传器类"""

    def __init__(self):
        """初始化上传器"""
        if not BANGUMI_ACCESS_TOKEN:
            raise ValueError("BANGUMI_ACCESS_TOKEN未设置，请在.env文件中配置")

        self.base_url = BANGUMI_BASE_URL
        self.access_token = BANGUMI_ACCESS_TOKEN
        self.session = requests.Session()
        self._setup_headers()

        # 数据存储
        self.normal_subjects = []
        self.nsfw_subjects = []
        self.last_year_rankings = {}  # 存储去年的排名数据 {subject_id: rank_position}
        self.last_year_nsfw_rankings = {}  # 存储去年的NSFW排名数据 {subject_id: rank_position}

    def _setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "onebyten/bgmlanfanpaihang (https://github.com/11111111111ge1/bgm_lanfanpaihang)",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送HTTP请求，带重试机制"""
        url = f"{self.base_url}{endpoint}"

        # 打印请求信息
        print(f"\n{'='*60}")
        print(f"请求详情:")
        print(f"  方法: {method}")
        print(f"  URL: {url}")
        print(f"  Headers: {dict(self.session.headers)}")
        if 'json' in kwargs:
            print(f"  Payload: {json.dumps(kwargs['json'], ensure_ascii=False, indent=2)}")
        print(f"{'='*60}\n")

        for attempt in range(RETRY_TIMES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=30,
                    **kwargs
                )

                # 打印响应信息
                print(f"响应详情:")
                print(f"  状态码: {response.status_code}")
                print(f"  响应头: {dict(response.headers)}")
                print(f"  响应体: {response.text}")
                print(f"{'='*60}\n")

                if response.status_code in [200, 204]:
                    if response.content:
                        return response.json()
                    return {}
                elif response.status_code == 401:
                    raise Exception("认证失败：Token无效或已过期")
                elif response.status_code == 429:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"触发速率限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
                    if attempt < RETRY_TIMES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                print(f"请求异常: {e}")
                if attempt < RETRY_TIMES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        raise Exception("请求失败，已达到最大重试次数")

    def load_data(self):
        """加载JSON数据并分离normal和nsfw条目"""
        print(f"正在加载数据文件: {DATA_FILE}")

        if not DATA_FILE.exists():
            raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}")

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.normal_subjects = data.get('normal', [])
        self.nsfw_subjects = data.get('nsfw', [])

        print(f"加载完成: {len(self.normal_subjects)} 个normal条目, {len(self.nsfw_subjects)} 个nsfw条目")
        return data.get('metadata', {})

    def fetch_last_year_rankings(self):
        """从本地文件加载去年的排名数据"""
        print(f"\n正在加载去年的排名数据 (索引ID: {OLD_INDEX_ID})")

        try:
            # 查找最新的去年索引文件
            if not LAST_YEAR_INDICES_DIR.exists():
                print(f"⚠ 索引目录不存在: {LAST_YEAR_INDICES_DIR}")
                print("将所有条目标记为NEW")
                return

            # 查找所有匹配去年索引ID的文件
            index_files = list(LAST_YEAR_INDICES_DIR.glob(f"index_{OLD_INDEX_ID}_*.json"))

            if not index_files:
                print(f"⚠ 未找到去年的索引文件 (index_{OLD_INDEX_ID}_*.json)")
                print("将所有条目标记为NEW")
                return

            # 按修改时间排序，获取最新的文件
            latest_file = max(index_files, key=lambda f: f.stat().st_mtime)
            print(f"使用文件: {latest_file.name}")

            # 读取JSON文件
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            subjects = data.get('subjects', [])
            for subject in subjects:
                subject_id = subject.get('id')
                # 从comment中提取排名，格式如 "1 -" 或 "1 ↑2"
                comment = subject.get('comment', '')
                if comment and subject_id:
                    # 提取第一个数字作为排名
                    rank_str = comment.split()[0] if comment.split() else None
                    if rank_str and rank_str.isdigit():
                        self.last_year_rankings[subject_id] = int(rank_str)

            print(f"✓ 成功加载 {len(self.last_year_rankings)} 个去年的排名数据")

        except Exception as e:
            print(f"⚠ 加载去年排名数据失败: {e}")
            print("将所有条目标记为NEW")

    def fetch_last_year_nsfw_rankings(self):
        """从本地ranks文件加载去年的NSFW排名数据"""
        print(f"\n正在加载去年的NSFW排名数据")

        try:
            # 查找最新的ranks文件
            if not LAST_YEAR_RANKS_DIR.exists():
                print(f"⚠ ranks目录不存在: {LAST_YEAR_RANKS_DIR}")
                print("将所有NSFW条目标记为NEW")
                return

            # 查找所有ranks文件
            ranks_files = list(LAST_YEAR_RANKS_DIR.glob("ranks_*.json"))

            if not ranks_files:
                print(f"⚠ 未找到ranks文件 (ranks_*.json)")
                print("将所有NSFW条目标记为NEW")
                return

            # 按修改时间排序，获取最新的文件
            latest_file = max(ranks_files, key=lambda f: f.stat().st_mtime)
            print(f"使用文件: {latest_file.name}")

            # 读取JSON文件
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # data是一个数组，每个元素包含 id 和 rank 字段
            for subject in data:
                subject_id = subject.get('id')
                rank_position = subject.get('rank')  # 这是TOP100中的排名位置
                if subject_id and rank_position:
                    self.last_year_nsfw_rankings[subject_id] = rank_position

            print(f"✓ 成功加载 {len(self.last_year_nsfw_rankings)} 个去年的NSFW排名数据")

        except Exception as e:
            print(f"⚠ 加载去年NSFW排名数据失败: {e}")
            print("将所有NSFW条目标记为NEW")


    def generate_comment(self, current_rank: int, subject_id: int, is_nsfw: bool = False) -> str:
        """生成排名变化的comment

        Args:
            current_rank: 今年的排名
            subject_id: 条目ID
            is_nsfw: 是否为NSFW条目

        Returns:
            格式化的comment字符串，如 "12 ↓2", "13 ↑1", "10 NEW"
        """
        # 根据是否为NSFW选择不同的去年排名数据源
        last_year_rankings = self.last_year_nsfw_rankings if is_nsfw else self.last_year_rankings

        if subject_id not in last_year_rankings:
            return f"{current_rank} NEW"

        last_year_rank = last_year_rankings[subject_id]
        rank_change = last_year_rank - current_rank  # 正数表示排名上升（数字变小）

        if rank_change > 0:
            # 排名上升（数字变小了）
            return f"{current_rank} ↑{rank_change}"
        elif rank_change < 0:
            # 排名下降（数字变大了）
            return f"{current_rank} ↓{abs(rank_change)}"
        else:
            # 排名不变
            return f"{current_rank} -"


    def generate_description(self) -> str:
        """生成索引描述，包含NSFW条目列表"""
        # 基础描述
        desc_lines = [
            "根据制表时的排名倒序排序",
            "制表时间：26/01/01",
            "排名后箭头代表和前一年表格排名变化",
            f"2025年版本：[url]https://bgm.tv/index/{OLD_INDEX_ID}[/url]",
            "讨论：[url]待填写[/url]",
            "受限条目不直接录入，在此单独列出："
        ]

        # 添加NSFW条目列表，带排名变化
        for subject in self.nsfw_subjects:
            rank_pos = subject['rank_position']
            subject_id = subject['id']
            name = subject.get('name_cn') or subject.get('name', '')
            comment = self.generate_comment(rank_pos, subject_id, is_nsfw=True)
            desc_lines.append(f"{comment} [url=https://bgm.tv/subject/{subject_id}]{name}[/url]")

        return "\r\n".join(desc_lines)

    def update_index_info(self, title: str, description: str):
        """更新索引的标题和描述"""
        print(f"\n步骤1: 更新索引信息 (ID: {NEW_INDEX_ID})")
        print(f"标题: {title}")
        print(f"描述长度: {len(description)} 字符")

        # 跳过此API调用，因为 PUT /v0/indices/{index_id} API有bug 已反馈，等待修复 https://github.com/bangumi/api/issues/270
        print("⚠ 跳过索引信息更新 (PUT /v0/indices/{index_id} API有bug)")
        return {}

        # endpoint = f"/v0/indices/{NEW_INDEX_ID}"
        # payload = {
        #     "title": title,
        #     "description": description
        # }

        # try:
        #     result = self._make_request("PUT", endpoint, json=payload)
        #     print("✓ 索引信息更新成功")
        #     time.sleep(RATE_LIMIT_DELAY)
        #     return result
        # except Exception as e:
        #     print(f"✗ 索引信息更新失败: {e}")
        #     raise

    def upload_subject(self, subject_id: int, rank_position: int, comment: str):
        """上传单个条目到索引（使用PUT方法，如果不存在会自动创建）"""
        endpoint = f"/v0/indices/{NEW_INDEX_ID}/subjects/{subject_id}"
        payload = {
            "sort": rank_position,
            "comment": comment
        }

        try:
            result = self._make_request("PUT", endpoint, json=payload)
            time.sleep(RATE_LIMIT_DELAY)
            return result
        except Exception as e:
            print(f"  ✗ 上传失败 (ID: {subject_id}): {e}")
            return None

    def upload_all_subjects(self):
        """批量上传所有normal条目"""
        print(f"\n步骤2: 上传所有normal条目 (共 {len(self.normal_subjects)} 个)")

        success_count = 0
        fail_count = 0

        for idx, subject in enumerate(self.normal_subjects, 1):
            subject_id = subject['id']
            rank_position = subject['rank_position']
            name = subject.get('name_cn') or subject.get('name', '')
            comment = self.generate_comment(rank_position, subject_id)

            print(f"[{idx}/{len(self.normal_subjects)}] 上传: {name} (ID: {subject_id}, 排名: {rank_position}, Comment: {comment})")

            result = self.upload_subject(subject_id, rank_position, comment)
            if result is not None:
                success_count += 1
                print(f"  ✓ 成功")
            else:
                fail_count += 1

        print(f"\n上传完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        return success_count, fail_count

    def run(self):
        """执行完整的上传流程"""
        import time as time_module
        start_time = time_module.time()

        print("=" * 60)
        print("Bangumi索引上传脚本")
        print("=" * 60)

        try:
            # 加载数据
            metadata = self.load_data()
            print(f"数据年份: {metadata.get('year', 'N/A')}")
            print(f"获取时间: {metadata.get('fetch_date', 'N/A')}")

            # 获取去年的排名数据
            self.fetch_last_year_rankings()
            self.fetch_last_year_nsfw_rankings()

            # 生成描述
            description = self.generate_description()

            # 步骤1: 更新索引信息
            title = "BANGUMI最差动漫TOP100（2026）"
            self.update_index_info(title, description)

            # 步骤2: 上传所有条目
            success_count, fail_count = self.upload_all_subjects()

            # 完成
            elapsed_time = time_module.time() - start_time
            print("\n" + "=" * 60)
            print("上传流程完成")
            print(f"总耗时: {elapsed_time:.2f} 秒")
            print(f"成功: {success_count} 个条目")
            print(f"失败: {fail_count} 个条目")
            print("=" * 60)

        except Exception as e:
            print(f"\n执行失败: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """主入口函数"""
    try:
        uploader = IndexUploader()
        uploader.run()
    except Exception as e:
        print(f"\n程序异常退出: {e}")
        exit(1)


if __name__ == "__main__":
    main()
