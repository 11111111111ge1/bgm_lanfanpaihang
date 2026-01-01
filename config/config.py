"""
Bangumi烂番排行配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API配置
BANGUMI_BASE_URL = "https://api.bgm.tv"
BANGUMI_ACCESS_TOKEN = os.getenv("BANGUMI_ACCESS_TOKEN")

# 搜索参数
ANIME_TYPE = 2  # 动画类型
MIN_RANK = 9500  # 最小排名阈值（从9500开始搜索，获取所有排名靠后的动漫）

# 索引配置
NEW_INDEX_ID = 87084  # 今年的索引ID
OLD_INDEX_ID = 74044  # 去年的索引ID，用于对比排名变化

# 请求配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
RETRY_TIMES = 3  # 重试次数
RETRY_DELAY = 2  # 重试延迟（秒）
RATE_LIMIT_DELAY = 1  # 请求间隔（秒）

# 分页配置
PAGE_SIZE = 50  # 每页结果数

# 输出配置
OUTPUT_DIR = "output"
JSON_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "json")
TOP_N = 100  # 最终输出的TOP N条目数量（设置为较大值以导出所有数据）

# 确保输出目录存在
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
