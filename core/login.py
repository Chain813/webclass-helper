"""
登录模块 - 账号密码自动登录 + Cookie 持久化
"""
import time
from utils.logger import log
from utils.random_delay import human_delay, random_micro_delay
from core.anti_detect import inject_on_new_page


# 学习通登录页 URL
LOGIN_URL = "https://passport2.chaoxing.com/login?fid=&newversion=true&refer=https://i.chaoxing.com"
HOME_URL = "https://i.chaoxing.com"
MOOC_URL = "https://mooc1-1.chaoxing.com"


def check_login_status(page) -> bool:
    """
    检查是否已登录（通过 Cookie 自动登录）
    
    Args:
        page: 浏览器页面对象
    
    Returns:
        True 表示已登录
    """
    try:
        page.get(HOME_URL)
        time.sleep(2)
        current_url = page.url

        # 如果没有被重定向到登录页，说明已登录
        if "passport" not in current_url and "login" not in current_url:
            log.info("✅ Cookie 有效，已自动登录")
            return True

        return False
    except Exception:
        return False


def login_with_password(page, phone: str, password: str) -> bool:
    """
    使用账号密码登录学习通
    
    Args:
        page: 浏览器页面对象
        phone: 手机号
        password: 密码
    
    Returns:
        True 表示登录成功
    """
    if not phone or not password:
        log.error("❌ 请在 config.py 中填写手机号和密码")
        return False

    log.info(f"🔑 正在登录账号: {phone[:3]}****{phone[-4:]}")

    try:
        # 导航到登录页
        page.get(LOGIN_URL)
        time.sleep(2)
        inject_on_new_page(page)

        # 等待页面加载
        human_delay(1.5, 3.0, "等待登录页加载")

        # 尝试切换到账号密码登录模式
        # 学习通登录页可能默认显示手机验证码登录，需要切换
        try:
            # 点击"密码登录"选项
            pwd_tab = page.ele("text:密码登录", timeout=3)
            if pwd_tab:
                pwd_tab.click()
                human_delay(0.5, 1.5, "切换到密码登录")
        except Exception:
            pass  # 可能已经在密码登录页

        # 清空并输入手机号
        phone_input = page.ele("#phone", timeout=5)
        if not phone_input:
            # 尝试其他选择器
            phone_input = page.ele("@name=phone", timeout=3)
        if not phone_input:
            phone_input = page.ele("tag:input@type=text", timeout=3)

        if phone_input:
            phone_input.clear()
            random_micro_delay()
            # 逐字符输入，模拟人类打字
            for char in phone:
                phone_input.input(char)
                random_micro_delay(50, 150)
            log.debug("📱 手机号已输入")
        else:
            log.error("❌ 找不到手机号输入框")
            return False

        human_delay(0.5, 1.0, "输入间隔")

        # 清空并输入密码
        pwd_input = page.ele("#pwd", timeout=5)
        if not pwd_input:
            pwd_input = page.ele("@name=pwd", timeout=3)
        if not pwd_input:
            pwd_input = page.ele("tag:input@type=password", timeout=3)

        if pwd_input:
            pwd_input.clear()
            random_micro_delay()
            for char in password:
                pwd_input.input(char)
                random_micro_delay(50, 150)
            log.debug("🔒 密码已输入")
        else:
            log.error("❌ 找不到密码输入框")
            return False

        human_delay(1.0, 2.0, "点击登录前等待")

        # 点击登录按钮
        login_btn = page.ele("#loginBtn", timeout=5)
        if not login_btn:
            login_btn = page.ele("text:登录", timeout=3)
        if not login_btn:
            login_btn = page.ele("tag:button", timeout=3)

        if login_btn:
            login_btn.click()
            log.info("🚀 已点击登录按钮，等待验证...")
        else:
            log.error("❌ 找不到登录按钮")
            return False

        # 等待登录完成
        human_delay(3.0, 5.0, "等待登录响应")

        # 检查是否有验证码弹窗
        _handle_captcha(page)

        # 验证登录结果
        time.sleep(2)
        current_url = page.url
        if "passport" not in current_url and "login" not in current_url:
            log.info("✅ 登录成功！")
            return True
        else:
            log.warning("⚠️ 登录可能未成功，请检查账号密码是否正确")
            # 再等一会看看
            time.sleep(3)
            current_url = page.url
            if "passport" not in current_url and "login" not in current_url:
                log.info("✅ 登录成功！（延迟确认）")
                return True
            return False

    except Exception as e:
        log.error(f"❌ 登录过程出错: {e}")
        return False


def _handle_captcha(page):
    """
    处理登录过程中可能出现的验证码
    目前采用等待用户手动处理的策略（滑块验证码无法自动化）
    """
    try:
        # 检查是否出现验证码
        captcha = page.ele("#captchaWrap", timeout=2)
        if not captcha:
            captcha = page.ele(".verify-wrap", timeout=1)

        if captcha:
            log.warning("⚠️ 检测到验证码！请在浏览器中手动完成验证...")
            log.warning("⚠️ 完成后脚本将自动继续")

            # 等待验证码消失或页面跳转
            for _ in range(60):  # 最多等待60秒
                time.sleep(1)
                current_url = page.url
                if "passport" not in current_url:
                    break
                try:
                    captcha_check = page.ele("#captchaWrap", timeout=0.5)
                    if not captcha_check:
                        break
                except Exception:
                    break

    except Exception:
        pass  # 没有验证码，正常流程


def perform_login(page, config: dict) -> bool:
    """
    执行完整登录流程
    
    Args:
        page: 浏览器页面对象
        config: CONFIG["login"] 配置
    
    Returns:
        True 表示登录成功
    """
    # 首先检查是否已登录（Cookie 持久化）
    if check_login_status(page):
        return True

    # 使用账号密码登录
    return login_with_password(
        page,
        config.get("phone", ""),
        config.get("password", ""),
    )
