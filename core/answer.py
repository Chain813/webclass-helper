"""
DeepSeek AI 答题模块 - 自动识别题目并调用 AI 生成答案
Token 消耗极低：每题约 200-400 tokens，一门课全部题目约 1-2 万 tokens
"""
import json
import re
import time
import requests
from utils.logger import log
from utils.random_delay import human_delay, random_micro_delay


class AIAnswerer:
    """基于 DeepSeek 的 AI 自动答题器"""

    def __init__(self, config: dict):
        """
        Args:
            config: CONFIG["deepseek"] 配置
        """
        self.enabled = config.get("enabled", False)
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.deepseek.com")
        self.model = config.get("model", "deepseek-chat")
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.1)
        self.total_tokens_used = 0

        if self.enabled and not self.api_key:
            log.warning("⚠️ DeepSeek API Key 未配置，AI 答题已禁用")
            self.enabled = False

    def handle_quiz(self, page) -> bool:
        """
        检测当前页面是否有测验/作业，并尝试自动答题
        
        Args:
            page: 浏览器页面对象
        
        Returns:
            True 表示已处理或无需处理
        """
        if not self.enabled:
            log.debug("AI 答题未启用，跳过测验")
            return True

        try:
            # 检查是否存在测验表单
            quiz_form = page.ele(".questionLi", timeout=3)
            if not quiz_form:
                quiz_form = page.ele("#submitForm", timeout=2)
            if not quiz_form:
                quiz_form = page.ele(".Cy_TItle", timeout=2)

            if not quiz_form:
                return True  # 当前页面无测验

            log.info("📝 检测到测验/作业，开始 AI 答题...")

            # 获取所有题目
            questions = self._extract_questions(page)

            if not questions:
                log.warning("⚠️ 未能提取到题目")
                return True

            log.info(f"📝 共 {len(questions)} 道题目")

            # 逐题作答
            for i, q in enumerate(questions):
                log.info(f"  📌 第 {i + 1}/{len(questions)} 题: {q['type']} - {q['text'][:30]}...")
                answer = self._get_ai_answer(q)
                if answer:
                    self._fill_answer(page, q, answer)
                    human_delay(2.0, 5.0, "模拟思考间隔")

            # 提交答案
            human_delay(3.0, 6.0, "检查答案后提交")
            self._submit_quiz(page)

            log.info(f"✅ 答题完成，本次累计消耗 {self.total_tokens_used} tokens")
            return True

        except Exception as e:
            log.warning(f"⚠️ 答题过程出错: {e}")
            return True

    def _extract_questions(self, page) -> list:
        """
        从页面提取题目列表
        
        Returns:
            [{"index": 0, "type": "单选题", "text": "...", "options": [...], "element": ...}, ...]
        """
        questions = []

        try:
            # 查找所有题目容器
            q_elements = page.eles(".questionLi", timeout=5)
            if not q_elements:
                q_elements = page.eles(".Cy_TItle", timeout=3)
            if not q_elements:
                q_elements = page.eles(".TiMu", timeout=3)

            for idx, q_elem in enumerate(q_elements):
                try:
                    q_info = {"index": idx, "element": q_elem}

                    # 提取题目类型
                    type_elem = q_elem.ele(".colorDeep", timeout=1)
                    if not type_elem:
                        type_elem = q_elem.ele(".Cy_TItle .fb", timeout=1)
                    q_type = type_elem.text.strip() if type_elem else "未知"

                    # 规范化题型
                    if "单选" in q_type:
                        q_info["type"] = "单选题"
                    elif "多选" in q_type:
                        q_info["type"] = "多选题"
                    elif "判断" in q_type:
                        q_info["type"] = "判断题"
                    elif "填空" in q_type:
                        q_info["type"] = "填空题"
                    elif "简答" in q_type or "问答" in q_type:
                        q_info["type"] = "简答题"
                    else:
                        q_info["type"] = q_type

                    # 提取题目文本
                    text = q_elem.text.strip()
                    # 清理多余空白
                    text = re.sub(r'\s+', ' ', text)
                    q_info["text"] = text[:500]  # 限制长度

                    # 提取选项（选择题）
                    options = []
                    option_elements = q_elem.eles("tag:li@class:answer", timeout=2)
                    if not option_elements:
                        option_elements = q_elem.eles(".Cy_ulTxt li", timeout=2)
                    if not option_elements:
                        option_elements = q_elem.eles(".answerBg li", timeout=2)

                    for opt in option_elements:
                        try:
                            opt_text = opt.text.strip()
                            if opt_text:
                                options.append({
                                    "text": opt_text,
                                    "element": opt,
                                })
                        except Exception:
                            continue

                    q_info["options"] = options
                    questions.append(q_info)

                except Exception:
                    continue

        except Exception as e:
            log.warning(f"提取题目失败: {e}")

        return questions

    def _get_ai_answer(self, question: dict) -> str:
        """
        调用 DeepSeek API 获取答案
        
        Args:
            question: 题目信息字典
        
        Returns:
            AI 生成的答案文本
        """
        try:
            # 构建 prompt
            q_type = question["type"]
            q_text = question["text"]
            options = question.get("options", [])

            prompt = f"你是一个在线课程答题助手。请根据题目直接给出答案，不要解释。\n\n"
            prompt += f"题型：{q_type}\n"
            prompt += f"题目：{q_text}\n"

            if options:
                prompt += "选项：\n"
                for opt in options:
                    prompt += f"  {opt['text']}\n"

            if q_type == "单选题":
                prompt += "\n请只回答选项字母（如 A、B、C、D），不要其他内容。"
            elif q_type == "多选题":
                prompt += "\n请回答所有正确选项的字母，用逗号分隔（如 A,B,C），不要其他内容。"
            elif q_type == "判断题":
                prompt += "\n请只回答「对」或「错」，不要其他内容。"
            elif q_type == "填空题":
                prompt += "\n请直接给出填空答案，多个空用 | 分隔。"
            else:
                prompt += "\n请简洁回答，控制在 100 字以内。"

            # 调用 API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                answer = data["choices"][0]["message"]["content"].strip()
                tokens = data.get("usage", {}).get("total_tokens", 0)
                self.total_tokens_used += tokens
                log.debug(f"🤖 AI 答案: {answer} (消耗 {tokens} tokens)")
                return answer
            else:
                log.warning(f"⚠️ DeepSeek API 返回错误: {response.status_code}")
                return ""

        except Exception as e:
            log.warning(f"⚠️ AI 答题失败: {e}")
            return ""

    def _fill_answer(self, page, question: dict, answer: str):
        """
        将 AI 答案填入页面
        
        Args:
            page: 浏览器页面对象
            question: 题目信息
            answer: AI 生成的答案
        """
        try:
            q_type = question["type"]
            q_elem = question["element"]
            options = question.get("options", [])

            if q_type == "单选题":
                # 从答案中提取字母
                letter = re.search(r'[A-Da-d]', answer)
                if letter:
                    target_idx = ord(letter.group().upper()) - ord('A')
                    if 0 <= target_idx < len(options):
                        random_micro_delay()
                        options[target_idx]["element"].click()
                        log.debug(f"  ✓ 选择: {options[target_idx]['text'][:20]}")

            elif q_type == "多选题":
                # 提取所有字母
                letters = re.findall(r'[A-Da-d]', answer)
                for letter in letters:
                    target_idx = ord(letter.upper()) - ord('A')
                    if 0 <= target_idx < len(options):
                        random_micro_delay()
                        options[target_idx]["element"].click()
                        log.debug(f"  ✓ 选择: {options[target_idx]['text'][:20]}")

            elif q_type == "判断题":
                if "对" in answer or "正确" in answer or "true" in answer.lower():
                    # 点击"对"选项
                    if len(options) >= 1:
                        options[0]["element"].click()
                else:
                    # 点击"错"选项
                    if len(options) >= 2:
                        options[1]["element"].click()

            elif q_type in ("填空题", "简答题"):
                # 查找输入框
                inputs = q_elem.eles("tag:textarea", timeout=2)
                if not inputs:
                    inputs = q_elem.eles("tag:input@type=text", timeout=2)

                if inputs:
                    # 填空题可能有多个空
                    answers = answer.split("|") if "|" in answer else [answer]
                    for idx, inp in enumerate(inputs):
                        if idx < len(answers):
                            inp.clear()
                            random_micro_delay()
                            # 逐字输入模拟
                            for char in answers[idx].strip():
                                inp.input(char)
                                random_micro_delay(30, 100)

        except Exception as e:
            log.warning(f"⚠️ 填写答案失败: {e}")

    def _submit_quiz(self, page):
        """提交测验/作业"""
        try:
            submit_btn = page.ele("#submitBtn", timeout=3)
            if not submit_btn:
                submit_btn = page.ele("text:提交", timeout=3)
            if not submit_btn:
                submit_btn = page.ele(".Btn_blue_larger", timeout=3)

            if submit_btn:
                submit_btn.click()
                human_delay(1.0, 2.0)

                # 处理确认弹窗
                confirm_btn = page.ele("text:确定", timeout=3)
                if confirm_btn:
                    confirm_btn.click()

                log.info("📤 答案已提交")
            else:
                log.warning("⚠️ 未找到提交按钮，可能需要手动提交")

        except Exception as e:
            log.warning(f"⚠️ 提交答案失败: {e}")

    def get_token_summary(self) -> str:
        """获取 token 消耗摘要"""
        return f"累计消耗: {self.total_tokens_used} tokens"
