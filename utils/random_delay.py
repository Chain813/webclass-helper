"""
随机延迟生成器 - 基于高斯分布模拟人类操作间隔
"""
import random
import time
from utils.logger import log


def human_delay(min_sec: float = 1.5, max_sec: float = 5.0, label: str = ""):
    """
    模拟人类操作延迟（高斯分布）
    
    使用正态分布生成随机延迟时间，集中在均值附近，
    比均匀分布更接近真实人类行为。
    
    Args:
        min_sec: 最小延迟秒数
        max_sec: 最大延迟秒数
        label: 操作标签，用于日志输出
    """
    mean = (min_sec + max_sec) / 2
    std = (max_sec - min_sec) / 4  # 约 95% 的值落在 [min, max] 范围内
    delay = random.gauss(mean, std)
    delay = max(min_sec, min(max_sec, delay))  # 钳制到范围内

    if label:
        log.debug(f"⏳ {label} - 等待 {delay:.1f}s")
    time.sleep(delay)


def random_micro_delay(min_ms: int = 200, max_ms: int = 800):
    """
    微小延迟（毫秒级），模拟人类鼠标移动/点击间隔
    
    Args:
        min_ms: 最小延迟毫秒
        max_ms: 最大延迟毫秒
    """
    delay_ms = random.randint(min_ms, max_ms)
    time.sleep(delay_ms / 1000.0)


def random_long_break(min_min: float = 5.0, max_min: float = 15.0):
    """
    长休息（分钟级），模拟人类学习间歇
    
    Args:
        min_min: 最小休息分钟
        max_min: 最大休息分钟
    """
    break_time = random.uniform(min_min, max_min)
    log.info(f"☕ 模拟休息中... {break_time:.1f} 分钟后继续")
    time.sleep(break_time * 60)
    log.info("📚 休息结束，继续学习")


def jitter(base_seconds: float, jitter_pct: float = 0.3) -> float:
    """
    给一个基准时间添加随机抖动
    
    Args:
        base_seconds: 基准秒数
        jitter_pct: 抖动百分比（默认 ±30%）
    
    Returns:
        带抖动的时间（秒）
    """
    delta = base_seconds * jitter_pct
    return base_seconds + random.uniform(-delta, delta)
