"""
超星学习通自动刷课脚本 - 主入口
零风险防封号设计 | DrissionPage 无痕自动化 | DeepSeek AI 答题

使用方法：
    1. 编辑 config.py 填写账号密码和课程信息
    2. 运行: python main.py
    3. 首次运行可能需要手动完成验证码
"""
import sys
import os
import time
import signal
from datetime import datetime

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(__file__))

from config import CONFIG
from utils.logger import log
from utils.random_delay import human_delay
from core.browser import BrowserManager
from core.login import perform_login
from core.course import CourseManager
from core.player import VideoPlayer
from core.answer import AIAnswerer
from core.anti_detect import inject_on_new_page
from scheduler.human_scheduler import HumanScheduler


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════╗
║          🎓 超星学习通 · 智能刷课助手               ║
║     DrissionPage 无痕自动化 | DeepSeek AI 答题      ║
║                                                      ║
║  ⚡ 1倍速原生播放  🛡️ 零WebDriver指纹              ║
║  👤 智能人类作息  🤖 AI自动答题                     ║
╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def graceful_exit(browser_manager):
    """优雅退出"""
    def handler(signum, frame):
        log.info("\n🛑 收到退出信号，正在安全关闭...")
        browser_manager.quit()
        log.info("👋 再见！")
        sys.exit(0)
    return handler


def validate_config():
    """验证配置有效性"""
    login = CONFIG.get("login", {})
    if not login.get("phone") or not login.get("password"):
        log.error("❌ 请在 config.py 中填写手机号和密码")
        log.error("   位置: CONFIG -> login -> phone / password")
        return False

    courses = CONFIG.get("courses", [])
    if not courses:
        log.warning("⚠️ 未指定课程，将刷所有未完成的课程")

    deepseek = CONFIG.get("deepseek", {})
    if deepseek.get("enabled") and not deepseek.get("api_key"):
        log.warning("⚠️ DeepSeek API Key 未配置，AI 答题将被禁用")

    return True


def run():
    """主运行流程"""
    print_banner()
    log.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 启动刷课脚本")

    # 验证配置
    if not validate_config():
        return

    # 初始化各模块
    browser_mgr = BrowserManager(CONFIG.get("browser", {}))
    scheduler = HumanScheduler(CONFIG.get("schedule", {}))
    answerer = AIAnswerer(CONFIG.get("deepseek", {}))

    # 注册退出信号
    signal.signal(signal.SIGINT, graceful_exit(browser_mgr))

    try:
        # ============================================
        # 1. 启动浏览器
        # ============================================
        page = browser_mgr.start()

        # ============================================
        # 2. 登录
        # ============================================
        if not perform_login(page, CONFIG.get("login", {})):
            log.error("❌ 登录失败，请检查账号密码")
            browser_mgr.quit()
            return

        human_delay(2.0, 4.0, "登录成功后等待")

        # ============================================
        # 3. 获取课程列表
        # ============================================
        course_mgr = CourseManager(page, CONFIG.get("courses", []))
        courses = course_mgr.fetch_courses()

        if not courses:
            log.error("❌ 未找到任何课程")
            browser_mgr.quit()
            return

        # ============================================
        # 4. 初始化播放器
        # ============================================
        player = VideoPlayer(page, CONFIG.get("safety", {}))

        # ============================================
        # 5. 开始刷课循环
        # ============================================
        log.info("=" * 50)
        log.info("🚀 开始自动刷课")
        log.info("=" * 50)

        for course_idx, course in enumerate(courses):
            # 检查调度器
            if not scheduler.can_study_now():
                log.info("⏰ 不在学习时段，等待下一个时段...")
                scheduler.wait_until_next_day()

            log.info(f"\n{'='*50}")
            log.info(f"📚 课程 [{course_idx + 1}/{len(courses)}]: {course['name']}")
            log.info(f"{'='*50}")

            # 获取章节列表
            chapters = course_mgr.get_chapters(course["url"])

            if not chapters:
                log.warning(f"⚠️ 课程 {course['name']} 无章节，跳过")
                continue

            # 启动学习会话
            scheduler.start_session()

            for ch_idx, chapter in enumerate(chapters):
                # 跳过已完成章节
                if chapter.get("completed"):
                    log.debug(f"  ✓ 章节已完成: {chapter['name']}")
                    continue

                # 检查是否需要休息
                if scheduler.should_take_break():
                    scheduler.take_break()
                    scheduler.start_session()

                    # 休息后检查是否还在学习时段
                    if not scheduler.can_study_now():
                        log.info("⏰ 学习时段结束")
                        break

                log.info(f"\n  📖 章节 [{ch_idx + 1}/{len(chapters)}]: {chapter['name']}")

                # 导航到章节
                if not course_mgr.navigate_to_chapter(chapter):
                    continue

                # 处理视频播放
                start_time = time.time()
                player.play_current_page()
                elapsed = time.time() - start_time
                scheduler.record_study_time(elapsed)

                # 处理测验/作业
                answerer.handle_quiz(page)

                # 章节完成，随机等待后切换
                human_delay(
                    CONFIG["safety"]["chapter_switch_delay_min"],
                    CONFIG["safety"]["chapter_switch_delay_max"],
                    "切换到下一章节",
                )

            log.info(f"\n✅ 课程 {course['name']} 处理完成")

        # ============================================
        # 6. 完成
        # ============================================
        log.info("\n" + "=" * 50)
        log.info("🎉 所有课程处理完成！")
        log.info(f"📊 {answerer.get_token_summary()}")
        status = scheduler.get_status()
        log.info(f"📊 今日学习时长: {status['daily_studied_hours']} 小时")
        log.info("=" * 50)

    except KeyboardInterrupt:
        log.info("\n🛑 用户中断，安全退出...")

    except Exception as e:
        log.error(f"❌ 运行异常: {e}")
        import traceback
        log.debug(traceback.format_exc())

    finally:
        browser_mgr.quit()


if __name__ == "__main__":
    run()
