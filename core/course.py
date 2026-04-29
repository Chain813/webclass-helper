"""
课程导航模块 - 获取课程列表、解析章节任务点
"""
import time
import re
from utils.logger import log
from utils.random_delay import human_delay
from core.anti_detect import inject_on_new_page


# 学习通课程列表页
COURSE_LIST_URL = "https://mooc2-ans.chaoxing.com/visit/courses/list?v=0&rss=1&start=0&size=500&catalogId=0&superstarClass=0"
COURSE_PAGE_URL = "https://mooc1.chaoxing.com/visit/courses"


class CourseManager:
    """课程管理器 - 获取、筛选、导航课程"""

    def __init__(self, page, target_courses: list = None):
        """
        Args:
            page: 浏览器页面对象
            target_courses: 指定课程名称列表（模糊匹配），为空则全部
        """
        self.page = page
        self.target_courses = target_courses or []
        self.courses = []

    def fetch_courses(self) -> list:
        """
        获取课程列表
        
        Returns:
            课程信息列表 [{"name": ..., "url": ..., "progress": ...}, ...]
        """
        log.info("📚 正在获取课程列表...")

        self.page.get(COURSE_PAGE_URL)
        time.sleep(3)
        inject_on_new_page(self.page)
        human_delay(2.0, 4.0, "等待课程列表加载")

        courses = []

        try:
            # 方案1: 如果页面中有 iframe，切换到 iframe
            frame = self.page.get_frame("#frame_content")
            target_page = frame if frame else self.page
            
            # 查找课程卡片
            course_elements = target_page.eles(".course-info", timeout=5)

            if not course_elements:
                # 尝试其他选择器
                course_elements = target_page.eles(".course", timeout=5)

            if not course_elements:
                # 尝试 li 列表形式
                course_elements = target_page.eles("tag:li@class=course", timeout=5)

            # 方案2: 直接访问课程列表接口
            if not course_elements:
                log.warning("⚠️ 未能在主页/iframe找到课程，尝试直接访问课程列表接口...")
                self.page.get(COURSE_LIST_URL)
                time.sleep(2)
                inject_on_new_page(self.page)
                target_page = self.page
                
                course_elements = target_page.eles(".course-info", timeout=5)
                if not course_elements:
                    course_elements = target_page.eles(".course", timeout=5)
                if not course_elements:
                    course_elements = target_page.eles("tag:li@class=course", timeout=5)
                
            if not course_elements:
                log.warning("⚠️ 未能通过常规选择器找到课程，尝试链接方式...")
                # 尝试从链接中提取课程
                links = target_page.eles("tag:a@href:courseId", timeout=5)
                for link in links:
                    try:
                        name = link.text.strip()
                        url = link.attr("href")
                        if name and url:
                            courses.append({
                                "name": name,
                                "url": url if url.startswith("http") else f"https://mooc1.chaoxing.com{url}",
                                "progress": "未知",
                            })
                    except Exception:
                        continue

            else:
                for elem in course_elements:
                    try:
                        # 提取课程名称
                        name_elem = elem.ele(".course-name", timeout=1)
                        if not name_elem:
                            name_elem = elem.ele("tag:h3", timeout=1)
                        if not name_elem:
                            name_elem = elem.ele("tag:a", timeout=1)

                        name = name_elem.text.strip() if name_elem else ""

                        # 提取课程链接
                        link_elem = elem.ele("tag:a@href:courseId", timeout=1)
                        if not link_elem:
                            link_elem = elem.ele("tag:a", timeout=1)

                        url = link_elem.attr("href") if link_elem else ""
                        if url and not url.startswith("http"):
                            url = f"https://mooc1.chaoxing.com{url}"

                        if name:
                            courses.append({
                                "name": name,
                                "url": url,
                                "progress": "未知",
                            })
                    except Exception:
                        continue

        except Exception as e:
            log.error(f"❌ 获取课程列表失败: {e}")

        log.info(f"📋 共找到 {len(courses)} 门课程")

        # 筛选目标课程
        if self.target_courses:
            filtered = []
            for course in courses:
                for target in self.target_courses:
                    if target.lower() in course["name"].lower():
                        filtered.append(course)
                        log.info(f"  ✓ 匹配课程: {course['name']}")
                        break
            courses = filtered
            log.info(f"🎯 筛选后: {len(courses)} 门目标课程")

        self.courses = courses
        return courses

    def get_chapters(self, course_url: str) -> list:
        """
        进入课程页面，获取章节列表
        
        Args:
            course_url: 课程 URL
        
        Returns:
            章节信息列表 [{"name": ..., "url": ..., "completed": bool}, ...]
        """
        log.info("📖 正在获取章节列表...")

        self.page.get(course_url)
        time.sleep(3)
        inject_on_new_page(self.page)
        human_delay(2.0, 3.0, "等待课程页加载")

        chapters = []

        try:
            frame = self.page.get_frame("#frame_content")
            target_page = frame if frame else self.page
            
            # 查找章节列表
            chapter_elements = target_page.eles(".chapter_unit", timeout=10)

            if not chapter_elements:
                chapter_elements = target_page.eles(".prev_ul li", timeout=5)

            if not chapter_elements:
                chapter_elements = target_page.eles(".posCatalog_select li", timeout=5)

            if not chapter_elements:
                # 通用查找：所有包含章节链接的元素
                chapter_elements = target_page.eles("tag:a@href:knowledge", timeout=5)

            for elem in chapter_elements:
                try:
                    if hasattr(elem, 'text'):
                        name = elem.text.strip()
                    else:
                        name = str(elem)

                    url = ""
                    if hasattr(elem, 'attr'):
                        url = elem.attr("href") or ""
                    
                    if hasattr(elem, 'ele'):
                        link = elem.ele("tag:a", timeout=1)
                        if link:
                            url = link.attr("href") or url
                            if not name:
                                name = link.text.strip()

                    # 检查是否已完成
                    completed = False
                    try:
                        check_icon = elem.ele(".icon-finish", timeout=0.5)
                        if not check_icon:
                            check_icon = elem.ele(".roundpoint_yes", timeout=0.5)
                        completed = check_icon is not None
                    except Exception:
                        pass

                    if name and len(name) < 200:
                        chapters.append({
                            "name": name[:50],
                            "url": url,
                            "completed": completed,
                            "element": elem,
                        })

                except Exception:
                    continue

        except Exception as e:
            log.error(f"❌ 获取章节列表失败: {e}")

        total = len(chapters)
        completed = sum(1 for c in chapters if c["completed"])
        log.info(f"📋 共 {total} 个章节，已完成 {completed}，待完成 {total - completed}")

        return chapters

    def navigate_to_chapter(self, chapter: dict) -> bool:
        """
        导航到指定章节
        
        Args:
            chapter: 章节信息字典
        
        Returns:
            True 表示导航成功
        """
        try:
            log.info(f"📖 进入章节: {chapter['name']}")

            if chapter.get("url"):
                url = chapter["url"]
                if not url.startswith("http"):
                    url = f"https://mooc1.chaoxing.com{url}"
                self.page.get(url)
            elif chapter.get("element"):
                # 直接点击元素
                chapter["element"].click()
            else:
                log.warning(f"⚠️ 无法导航到章节: {chapter['name']}")
                return False

            time.sleep(3)
            inject_on_new_page(self.page)
            human_delay(2.0, 4.0, "等待章节页加载")
            return True

        except Exception as e:
            log.error(f"❌ 导航到章节失败: {e}")
            return False
