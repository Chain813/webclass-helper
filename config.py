"""
配置文件 - 超星学习通自动刷课脚本
修改以下配置后运行 main.py 即可
API Key 从 .env 文件读取，不会上传到 GitHub
"""
import os


def _load_env():
    """从 .env 文件加载环境变量"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()

CONFIG = {
    # ============================================================
    # 登录配置
    # ============================================================
    "login": {
        "phone": "",          # 手机号
        "password": "",       # 密码
    },

    # ============================================================
    # 课程配置 - 指定要刷的课程名称（模糊匹配）
    # 示例: ["大学英语", "思想政治", "高等数学"]
    # 留空 [] 则刷所有未完成课程
    # ============================================================
    "courses": [],

    # ============================================================
    # 调度配置 - 模拟人类学习作息
    # ============================================================
    "schedule": {
        "start_hour": 8,          # 每日开始学习时间（24小时制）
        "end_hour": 22,           # 每日结束学习时间
        "max_daily_hours": 8,     # 每日最多学习时长（小时）
        "study_minutes_min": 40,  # 连续学习最短时间（分钟）
        "study_minutes_max": 60,  # 连续学习最长时间（分钟）
        "break_minutes_min": 5,   # 休息最短时间（分钟）
        "break_minutes_max": 15,  # 休息最长时间（分钟）
    },

    # ============================================================
    # 安全配置 - 防检测参数（请勿随意修改）
    # ============================================================
    "safety": {
        "playback_speed": 1.0,       # 播放倍速（固定1.0，修改有封号风险）
        "min_action_delay": 1.5,     # 操作最小间隔（秒）
        "max_action_delay": 5.0,     # 操作最大间隔（秒）
        "chapter_switch_delay_min": 3,  # 切换章节最小等待（秒）
        "chapter_switch_delay_max": 8,  # 切换章节最大等待（秒）
        "random_mouse_move": True,   # 是否随机微移鼠标
    },

    # ============================================================
    # DeepSeek AI 答题配置
    # ============================================================
    "deepseek": {
        "enabled": True,
        "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),  # 从 .env 自动读取
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "max_tokens": 512,                          # 每次回答最大 token 数
        "temperature": 0.1,                         # 低温度 = 更确定的答案
    },

    # ============================================================
    # 浏览器配置
    # ============================================================
    "browser": {
        "headless": False,          # 是否无头模式（建议 False，有头更安全）
        "browser_path": "",         # Chrome/Edge 路径，留空自动检测
        "user_data_dir": "",        # 浏览器用户数据目录，留空自动创建
    },
}
