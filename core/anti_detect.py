"""
反检测模块 - 消除所有自动化痕迹
核心策略：让浏览器看起来完全像人类操作
"""
from utils.logger import log


# ============================================================
# 可见性伪装 JS - 让页面始终认为窗口可见且获得焦点
# ============================================================
VISIBILITY_HACK_JS = """
(function() {
    // 1. 覆盖 document.visibilityState 始终返回 'visible'
    Object.defineProperty(document, 'visibilityState', {
        get: function() { return 'visible'; },
        configurable: true
    });

    // 2. 覆盖 document.hidden 始终返回 false
    Object.defineProperty(document, 'hidden', {
        get: function() { return false; },
        configurable: true
    });

    // 3. 拦截 visibilitychange 事件，阻止触发
    document.addEventListener('visibilitychange', function(e) {
        e.stopImmediatePropagation();
    }, true);

    // 4. 覆盖 document.hasFocus() 始终返回 true
    Document.prototype.hasFocus = function() { return true; };

    // 5. 阻止 blur 事件（窗口失焦）
    window.addEventListener('blur', function(e) {
        e.stopImmediatePropagation();
    }, true);

    // 6. 让 focus 事件持续触发
    window.addEventListener('focus', function(e) {
        // 允许正常传播
    }, true);

    console.log('[AntiDetect] Visibility hack injected');
})();
"""

# ============================================================
# 播放速率保护 JS - 防止意外修改播放速度
# ============================================================
SPEED_PROTECT_JS = """
(function() {
    // 监控所有 video 和 audio 元素的 playbackRate
    var observer = new MutationObserver(function(mutations) {
        var medias = document.querySelectorAll('video, audio');
        medias.forEach(function(media) {
            if (media.playbackRate !== 1.0) {
                console.warn('[AntiDetect] Playback rate reset from ' + media.playbackRate + ' to 1.0');
                media.playbackRate = 1.0;
            }
        });
    });

    observer.observe(document.body || document.documentElement, {
        childList: true,
        subtree: true
    });

    // 定期检查
    setInterval(function() {
        var medias = document.querySelectorAll('video, audio');
        medias.forEach(function(media) {
            if (media.playbackRate !== 1.0) {
                media.playbackRate = 1.0;
            }
        });
    }, 5000);

    console.log('[AntiDetect] Speed protection active');
})();
"""

# ============================================================
# 指纹自检 JS - 检查是否存在自动化痕迹
# ============================================================
FINGERPRINT_CHECK_JS = """
(function() {
    var issues = [];

    // 检查 webdriver 标志
    if (navigator.webdriver === true) {
        issues.push('navigator.webdriver = true');
    }

    // 检查 Chrome DevTools Protocol 痕迹
    if (window.cdc_adoQpoasnfa76pfcZLmcfl_Array ||
        window.cdc_adoQpoasnfa76pfcZLmcfl_Promise ||
        window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol) {
        issues.push('CDC variables detected');
    }

    // 检查 Selenium 痕迹
    if (document.$cdc_asdjflasutopfhvcZLmcfl_ ||
        document.__webdriver_evaluate ||
        document.__selenium_evaluate ||
        document.__fxdriver_evaluate ||
        document.__driver_evaluate) {
        issues.push('Selenium traces detected');
    }

    // 检查 Phantom 痕迹
    if (window._phantom || window.__nightmare || window.callPhantom) {
        issues.push('Phantom/Nightmare traces detected');
    }

    return {
        safe: issues.length === 0,
        issues: issues
    };
})();
"""


def inject_anti_detect(page):
    """
    向页面注入所有反检测脚本
    
    Args:
        page: DrissionPage 的 Tab/Page 对象
    """
    try:
        # 注入可见性伪装
        page.run_js(VISIBILITY_HACK_JS)
        log.debug("🛡️ 可见性伪装已注入")

        # 注入播放速率保护
        page.run_js(SPEED_PROTECT_JS)
        log.debug("🛡️ 播放速率保护已注入")

    except Exception as e:
        log.warning(f"⚠️ 反检测注入部分失败: {e}")


def verify_fingerprint(page) -> bool:
    """
    自检浏览器指纹是否安全
    
    Args:
        page: DrissionPage 的 Tab/Page 对象
    
    Returns:
        True 表示安全，False 表示存在风险
    """
    try:
        result = page.run_js(FINGERPRINT_CHECK_JS)
        if result and result.get("safe"):
            log.info("✅ 浏览器指纹自检通过 - 未检测到自动化痕迹")
            return True
        else:
            issues = result.get("issues", []) if result else ["检查失败"]
            for issue in issues:
                log.warning(f"⚠️ 指纹风险: {issue}")
            return False
    except Exception as e:
        log.warning(f"⚠️ 指纹自检异常: {e}")
        return False


def inject_on_new_page(page):
    """
    为新加载的页面注入反检测脚本
    应在每次页面导航后调用
    
    Args:
        page: DrissionPage 的 Tab/Page 对象
    """
    inject_anti_detect(page)
