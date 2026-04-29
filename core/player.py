"""
视频播放模块 - 自动播放视频并等待完成
核心防检测逻辑：让浏览器原生播放，不模拟心跳包
"""
import time
from utils.logger import log
from utils.random_delay import human_delay, random_micro_delay
from core.anti_detect import inject_on_new_page


class VideoPlayer:
    """视频播放控制器"""

    def __init__(self, page, safety_config: dict):
        """
        Args:
            page: 浏览器页面对象
            safety_config: CONFIG["safety"] 安全配置
        """
        self.page = page
        self.safety = safety_config

    def play_current_page(self) -> bool:
        """
        处理当前页面中的所有视频/音频任务点
        
        Returns:
            True 表示所有任务点已完成
        """
        inject_on_new_page(self.page)
        human_delay(1.0, 2.0, "页面加载后等待")

        # 处理 iframe 嵌套（学习通视频通常在 iframe 中）
        iframes = self._find_task_iframes()

        if not iframes:
            log.debug("📄 当前页面无视频任务点")
            return True

        for i, iframe_info in enumerate(iframes):
            log.info(f"🎬 处理第 {i + 1}/{len(iframes)} 个任务点")
            self._handle_task_point(iframe_info)

        return True

    def _find_task_iframes(self) -> list:
        """
        查找页面中的任务点 iframe
        学习通的视频通常嵌套在 iframe[id^='iframe'] 中
        
        Returns:
            iframe 信息列表
        """
        iframes = []

        try:
            # 方式1：查找任务点 iframe
            iframe_elements = self.page.eles("tag:iframe@id:iframe", timeout=5)

            if not iframe_elements:
                # 方式2：查找 class 包含 ans-attach-online 的 iframe
                iframe_elements = self.page.eles("tag:iframe@class:ans-attach-online", timeout=3)

            if not iframe_elements:
                # 方式3：查找所有可能包含视频的 iframe
                iframe_elements = self.page.eles("tag:iframe", timeout=3)

            for iframe in iframe_elements:
                try:
                    src = iframe.attr("src") or ""
                    # 只处理包含视频/文档的 iframe
                    if any(kw in src for kw in ["ananas", "video", "audio", "document", "pdf"]):
                        iframes.append({"element": iframe, "src": src})
                    elif not src:
                        # src 为空也可能是动态加载的视频
                        iframes.append({"element": iframe, "src": ""})
                except Exception:
                    continue

        except Exception as e:
            log.debug(f"查找 iframe 时出错: {e}")

        return iframes

    def _handle_task_point(self, iframe_info: dict):
        """
        处理单个任务点（视频/音频/文档）
        
        Args:
            iframe_info: iframe 信息字典
        """
        try:
            # 切换到 iframe 内部
            iframe_elem = iframe_info["element"]

            # 进入 iframe
            frame = self.page.get_frame(iframe_elem)
            if not frame:
                log.debug("无法进入 iframe，跳过")
                return

            # 检查是否有视频元素
            video = frame.ele("tag:video", timeout=5)
            audio = frame.ele("tag:audio", timeout=2) if not video else None

            if video:
                self._play_video(frame, video)
            elif audio:
                self._play_audio(frame, audio)
            else:
                log.debug("📄 非视频任务点，可能是文档/PPT")
                # 文档类任务点 - 等待几秒模拟阅读
                human_delay(5.0, 10.0, "模拟文档阅读")

        except Exception as e:
            log.warning(f"⚠️ 处理任务点时出错: {e}")

    def _play_video(self, frame, video_element):
        """
        播放视频并等待完成
        
        Args:
            frame: iframe 页面对象
            video_element: video 元素
        """
        try:
            # 获取视频总时长
            duration = frame.run_js("return document.querySelector('video').duration;")
            if not duration or duration <= 0:
                time.sleep(2)
                duration = frame.run_js("return document.querySelector('video').duration;")

            if not duration or duration <= 0:
                log.warning("⚠️ 无法获取视频时长，跳过")
                return

            log.info(f"🎬 视频时长: {self._format_time(duration)}")

            # 确保播放速率为 1.0
            frame.run_js("document.querySelector('video').playbackRate = 1.0;")

            # 设置静音（不影响心跳上报）
            frame.run_js("document.querySelector('video').muted = true;")

            # 检查当前播放进度
            current_time = frame.run_js("return document.querySelector('video').currentTime;") or 0
            if current_time > 0:
                log.info(f"📊 已有进度: {self._format_time(current_time)} / {self._format_time(duration)}")

            # 检查是否已完成
            if current_time >= duration - 2:
                log.info("✅ 该视频已完成")
                return

            # 点击播放按钮
            self._click_play(frame)

            # 等待视频播放完成
            remaining = duration - current_time
            log.info(f"⏳ 预计剩余: {self._format_time(remaining)}")

            self._wait_for_completion(frame, duration)

            log.info("✅ 视频播放完成")

        except Exception as e:
            log.warning(f"⚠️ 视频播放出错: {e}")

    def _play_audio(self, frame, audio_element):
        """
        播放音频并等待完成
        """
        try:
            duration = frame.run_js("return document.querySelector('audio').duration;")
            if not duration or duration <= 0:
                time.sleep(2)
                duration = frame.run_js("return document.querySelector('audio').duration;")

            if not duration or duration <= 0:
                log.warning("⚠️ 无法获取音频时长，跳过")
                return

            log.info(f"🎵 音频时长: {self._format_time(duration)}")

            # 播放
            frame.run_js("document.querySelector('audio').playbackRate = 1.0;")
            frame.run_js("document.querySelector('audio').muted = true;")
            frame.run_js("document.querySelector('audio').play();")

            # 等待完成
            self._wait_for_media_end(frame, "audio", duration)

            log.info("✅ 音频播放完成")

        except Exception as e:
            log.warning(f"⚠️ 音频播放出错: {e}")

    def _click_play(self, frame):
        """点击播放按钮"""
        try:
            # 尝试直接 JS 播放
            frame.run_js("document.querySelector('video').play();")
            time.sleep(1)

            # 检查是否真的在播放
            paused = frame.run_js("return document.querySelector('video').paused;")
            if paused:
                # JS 播放可能被浏览器拦截，尝试点击播放按钮
                play_btn = frame.ele(".vjs-big-play-button", timeout=2)
                if not play_btn:
                    play_btn = frame.ele(".vjs-play-control", timeout=2)
                if not play_btn:
                    play_btn = frame.ele("tag:button@title=播放", timeout=2)

                if play_btn:
                    random_micro_delay()
                    play_btn.click()
                    log.debug("▶️ 已点击播放按钮")
                else:
                    # 直接点击视频区域
                    video = frame.ele("tag:video", timeout=2)
                    if video:
                        video.click()

            time.sleep(1)

            # 最终确认
            paused = frame.run_js("return document.querySelector('video').paused;")
            if not paused:
                log.info("▶️ 视频已开始播放")
            else:
                log.warning("⚠️ 视频可能未能自动播放，请检查浏览器窗口")

        except Exception as e:
            log.warning(f"⚠️ 点击播放出错: {e}")

    def _wait_for_completion(self, frame, total_duration: float):
        """
        等待视频播放完成，定期检查进度
        
        Args:
            frame: iframe 页面对象
            total_duration: 视频总时长（秒）
        """
        check_interval = 30  # 每30秒检查一次进度
        stall_count = 0
        last_time = 0

        while True:
            try:
                time.sleep(check_interval)

                current = frame.run_js("return document.querySelector('video').currentTime;")
                paused = frame.run_js("return document.querySelector('video').paused;")

                if current is None:
                    stall_count += 1
                    if stall_count > 5:
                        log.warning("⚠️ 多次无法获取进度，跳过此视频")
                        break
                    continue

                # 播放进度
                progress = (current / total_duration * 100) if total_duration > 0 else 0
                log.info(f"📊 播放进度: {self._format_time(current)} / {self._format_time(total_duration)} ({progress:.1f}%)")

                # 检查是否完成
                if current >= total_duration - 2:
                    break

                # 检查是否暂停
                if paused:
                    log.warning("⏸️ 视频暂停，尝试重新播放...")
                    frame.run_js("document.querySelector('video').play();")
                    human_delay(1.0, 2.0)

                # 检查是否卡住
                if abs(current - last_time) < 1:
                    stall_count += 1
                    if stall_count > 3:
                        log.warning("⚠️ 视频疑似卡住，尝试恢复...")
                        frame.run_js("document.querySelector('video').play();")
                        stall_count = 0
                else:
                    stall_count = 0

                last_time = current

                # 重新注入反检测（防止页面刷新后失效）
                try:
                    from core.anti_detect import VISIBILITY_HACK_JS
                    frame.run_js(VISIBILITY_HACK_JS)
                except Exception:
                    pass

            except Exception as e:
                log.debug(f"进度检查异常: {e}")
                stall_count += 1
                if stall_count > 10:
                    log.warning("⚠️ 过多异常，跳过此视频")
                    break

    def _wait_for_media_end(self, frame, media_type: str, duration: float):
        """等待媒体播放结束"""
        check_interval = 15
        while True:
            try:
                time.sleep(check_interval)
                current = frame.run_js(f"return document.querySelector('{media_type}').currentTime;")
                if current is None or current >= duration - 2:
                    break
            except Exception:
                break

    @staticmethod
    def _format_time(seconds: float) -> str:
        """将秒数格式化为 MM:SS"""
        if not seconds or seconds < 0:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
