"""
浏览器管理模块 - DrissionPage 封装
使用 CDP 接管真实浏览器，无 WebDriver 指纹
"""
import os
import sys
from DrissionPage import Chromium, ChromiumOptions
from core.anti_detect import inject_anti_detect, verify_fingerprint
from utils.logger import log


class BrowserManager:
    """浏览器生命周期管理器"""

    def __init__(self, config: dict):
        """
        初始化浏览器管理器
        
        Args:
            config: 来自 config.py 的 CONFIG["browser"] 字典
        """
        self.config = config
        self.browser = None
        self.page = None

    def start(self):
        """启动浏览器并完成初始化"""
        log.info("🌐 正在启动浏览器...")

        opts = ChromiumOptions()

        # 设置浏览器路径
        browser_path = self.config.get("browser_path", "")
        if browser_path:
            opts.set_browser_path(browser_path)

        # 用户数据目录（保存 Cookie 等）
        user_data_dir = self.config.get("user_data_dir", "")
        if not user_data_dir:
            user_data_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "browser_data"
            )
        opts.set_user_data_path(user_data_dir)

        # 无头模式（默认关闭，有头模式更安全）
        if self.config.get("headless", False):
            opts.headless()
            log.warning("⚠️ 无头模式已开启，风险较高")

        # 关键：禁用自动化标志
        opts.set_argument("--disable-blink-features=AutomationControlled")

        # 其他安全参数
        opts.set_argument("--no-first-run")
        opts.set_argument("--no-default-browser-check")
        opts.set_argument("--disable-popup-blocking")

        # 设置正常的窗口大小
        opts.set_argument("--window-size=1366,768")

        try:
            self.browser = Chromium(opts)
            self.page = self.browser.latest_tab
            log.info("✅ 浏览器启动成功")

            # 指纹安全自检
            self.page.get("https://www.baidu.com")
            safe = verify_fingerprint(self.page)
            if not safe:
                log.warning("⚠️ 检测到自动化痕迹，但 DrissionPage 通常不会被检测")

            return self.page

        except Exception as e:
            log.error(f"❌ 浏览器启动失败: {e}")
            log.error("请确保已安装 Chrome 或 Edge 浏览器")
            sys.exit(1)

    def navigate(self, url: str):
        """
        导航到指定 URL，并注入反检测脚本
        
        Args:
            url: 目标 URL
        """
        log.debug(f"🔗 导航到: {url}")
        self.page.get(url)
        # 每次页面加载后重新注入反检测脚本
        inject_anti_detect(self.page)

    def get_page(self):
        """获取当前页面对象"""
        return self.page

    def quit(self):
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.quit()
                log.info("🔒 浏览器已关闭")
        except Exception:
            pass
