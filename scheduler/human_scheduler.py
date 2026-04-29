"""
智能调度器 - 模拟人类学习作息规律
核心防封策略：不在不合理的时间学习，不连续学习过长时间
"""
import random
import time
from datetime import datetime, timedelta
from utils.logger import log


class HumanScheduler:
    """人类行为模拟调度器"""

    def __init__(self, config: dict):
        """
        Args:
            config: CONFIG["schedule"] 调度配置
        """
        self.start_hour = config.get("start_hour", 8)
        self.end_hour = config.get("end_hour", 22)
        self.max_daily_hours = config.get("max_daily_hours", 8)
        self.study_min = config.get("study_minutes_min", 40)
        self.study_max = config.get("study_minutes_max", 60)
        self.break_min = config.get("break_minutes_min", 5)
        self.break_max = config.get("break_minutes_max", 15)

        # 运行状态追踪
        self.daily_study_seconds = 0
        self.session_start_time = None
        self.current_session_duration = 0
        self.last_date = datetime.now().date()

    def can_study_now(self) -> bool:
        """
        检查当前时间是否在允许学习的时段内
        
        Returns:
            True 表示可以学习
        """
        now = datetime.now()

        # 检查日期是否变更（重置每日计时）
        if now.date() != self.last_date:
            log.info("📅 新的一天，重置学习计时")
            self.daily_study_seconds = 0
            self.last_date = now.date()

        # 检查时段
        if now.hour < self.start_hour:
            wait_seconds = (self.start_hour - now.hour) * 3600 - now.minute * 60
            log.info(f"🌙 当前时间 {now.strftime('%H:%M')} 早于开始时间 {self.start_hour}:00")
            log.info(f"💤 等待 {wait_seconds // 60} 分钟后开始...")
            time.sleep(wait_seconds)
            return True

        if now.hour >= self.end_hour:
            log.info(f"🌙 当前时间 {now.strftime('%H:%M')} 已过结束时间 {self.end_hour}:00")
            log.info("📴 今日学习结束，明天继续")
            return False

        # 检查每日学习上限
        daily_hours = self.daily_study_seconds / 3600
        if daily_hours >= self.max_daily_hours:
            log.info(f"📊 今日已学习 {daily_hours:.1f} 小时，达到上限 {self.max_daily_hours} 小时")
            log.info("📴 今日学习结束，明天继续")
            return False

        return True

    def start_session(self):
        """开始一个学习会话"""
        self.session_start_time = time.time()
        self.current_session_duration = random.uniform(
            self.study_min * 60, self.study_max * 60
        )
        log.info(
            f"📚 开始学习会话，计划学习 {self.current_session_duration / 60:.0f} 分钟"
        )

    def should_take_break(self) -> bool:
        """
        检查是否应该休息
        
        Returns:
            True 表示应该休息
        """
        if self.session_start_time is None:
            return False

        elapsed = time.time() - self.session_start_time
        return elapsed >= self.current_session_duration

    def take_break(self):
        """执行休息"""
        # 更新学习时间统计
        if self.session_start_time:
            elapsed = time.time() - self.session_start_time
            self.daily_study_seconds += elapsed

        break_duration = random.uniform(self.break_min * 60, self.break_max * 60)
        daily_hours = self.daily_study_seconds / 3600

        log.info(f"☕ 休息 {break_duration / 60:.1f} 分钟（今日已学习 {daily_hours:.1f} 小时）")
        time.sleep(break_duration)
        log.info("📚 休息结束，继续学习")

        # 重置会话
        self.session_start_time = None

    def record_study_time(self, seconds: float):
        """
        记录学习时间
        
        Args:
            seconds: 学习秒数
        """
        self.daily_study_seconds += seconds

    def get_status(self) -> dict:
        """获取当前调度状态"""
        daily_hours = self.daily_study_seconds / 3600
        remaining_hours = max(0, self.max_daily_hours - daily_hours)

        return {
            "daily_studied_hours": round(daily_hours, 2),
            "remaining_hours": round(remaining_hours, 2),
            "in_session": self.session_start_time is not None,
            "can_study": self.can_study_now(),
        }

    def wait_until_next_day(self):
        """等待到第二天的开始时间"""
        now = datetime.now()
        tomorrow_start = datetime(
            now.year, now.month, now.day, self.start_hour, 0, 0
        ) + timedelta(days=1)

        # 添加随机偏移（±15分钟），不要精确在整点开始
        offset = random.randint(-15 * 60, 15 * 60)
        wait_target = tomorrow_start + timedelta(seconds=offset)

        wait_seconds = (wait_target - now).total_seconds()
        if wait_seconds > 0:
            log.info(f"💤 等待至明天 {wait_target.strftime('%H:%M')} 开始学习")
            log.info(f"⏰ 预计等待 {wait_seconds / 3600:.1f} 小时")
            time.sleep(wait_seconds)
