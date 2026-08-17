import json
import asyncio
import time
from google import genai
from google.genai import types
from PIL import Image
from config import settings

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.max_retries = 3

    def _retry_with_backoff(self, func, *args, **kwargs):
        """帶指數退避的重試機制 (Retry with exponential backoff)"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e)
                # 如果是 429 限流錯誤，等待後重試 (If rate limited, wait and retry)
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                    print(f"[AI] Rate limited, waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}...")
                    time.sleep(wait_time)
                else:
                    # 非限流錯誤，直接拋出 (Non-rate-limit error, raise immediately)
                    raise e
        raise last_error

    def _analyze_image_sync(self, image_path: str) -> str:
        img = Image.open(image_path)
        prompt = """
        【植物病理专家 AI】指令：
        你是一位专业的农业与植物病理学专家。请分析这张农作物/农场照片。
        请回传一个包含以下键值的 JSON 字串：
        - "status": 健康状态，必须是 "healthy" (健康), "warning" (轻微问题/需注意), 或 "critical" (严重病害/危急)
        - "notes": 详细诊断结果与具体用药或处置建议（使用繁体中文）
        - "confidence": 信心分数 (0.0 到 1.0)
        只回传 JSON，不要其他文字。
        """
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[img, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
        return self._retry_with_backoff(_call)

    async def analyze_image(self, image_path: str) -> str:
        # 執行分析並返回 JSON 字串
        return await asyncio.to_thread(self._analyze_image_sync, image_path)

    def _analyze_data_sync(self, inventory: list, tasks: list) -> str:
        prompt = f"""
        【数据分析师 AI】指令：
        你是一位农业数据分析专家。请根据以下目前的「农场库存档案」与「今日任务状况」，分析出重点洞察，例如：
        1. 哪些资材即将耗尽（数量极低），需要进货？
        2. 任务执行效率如何？
        请产出一段简短精准的分析报告（繁体中文）。
        
        库存: {inventory}
        任务: {tasks}
        """
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[prompt]
            )
            return response.text
        return self._retry_with_backoff(_call)

    async def analyze_data(self, inventory: list, tasks: list) -> str:
        return await asyncio.to_thread(self._analyze_data_sync, inventory, tasks)

    def _generate_daily_summary_sync(self, date_str: str, analyst_report: str, tasks: list, photos: list) -> str:
        prompt = f"""
        【农场大管家 AI】指令：
        你是农场的最高管理核心 AI。现在是 {date_str} 的傍晚。
        你刚刚召开了每日营运会议，收到了【数据分析师 AI】与【植物病理专家 AI】的汇整资料。
        请将以下资讯，统整成一篇结构清晰、排版精美（可使用 Emoji 与 Markdown）的《每日营运摘要》报告给老板。
        
        【数据分析师的报告】:
        {analyst_report}
        
        【今日任务完成状况】:
        {tasks}
        
        【今日照片病理诊断纪录 (只列出重点问题)】:
        {photos}
        
        报告架构建议：
        1. 今日概况 (总评)
        2. 任务达成进度
        3. 异常警报 (若照片有 warning/critical)
        4. 资材补货建议 (依分析师报告)
        """
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[prompt]
            )
            return response.text
        return self._retry_with_backoff(_call)

    async def generate_daily_summary(self, date_str: str, analyst_report: str, tasks: list, photos: list) -> str:
        return await asyncio.to_thread(self._generate_daily_summary_sync, date_str, analyst_report, tasks, photos)

    def _parse_bot_intent_sync(self, text: str) -> str:
        prompt = f"""
        使用者傳送了一條指令：「{text}」
        請判斷這是否是一條關於「消耗庫存」或「新增庫存」的指令。
        請回傳 JSON 格式：
        {{
            "intent": "inventory_consume" (如果是消耗/使用), "inventory_add" (如果是買入/新增), 或 "unknown" (如果不是庫存相關),
            "item_name": "物品名稱 (例如：有機農藥、種子等)",
            "quantity": 數字 (例如 5),
            "unit": "單位 (例如 罐、包、kg)"
        }}
        只回傳 JSON，不要其他文字。
        """
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
        return self._retry_with_backoff(_call)

    async def parse_bot_intent(self, text: str) -> str:
        return await asyncio.to_thread(self._parse_bot_intent_sync, text)

    def _translate_to_chinese_sync(self, text: str) -> str:
        prompt = f"""
        You are a professional translator for a farm management system.
        Detect the source language of the following text (it might be Burmese, Indonesian, Bengali, Malay, etc.) 
        and translate it into clear, professional Traditional Chinese (or Simplified, but stay consistent).
        Only output the translated Chinese text. Do NOT include any conversational filler or the source language name.
        
        Text to translate:
        {text}
        """
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[prompt]
            )
            return response.text.strip()
        return self._retry_with_backoff(_call)

    async def translate_to_chinese(self, text: str) -> str:
        return await asyncio.to_thread(self._translate_to_chinese_sync, text)

    def _generate_generic_content_sync(self, prompt: str) -> str:
        def _call():
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )
            return response.text
        return self._retry_with_backoff(_call)

    async def generate_generic_content(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_generic_content_sync, prompt)

ai_service = AIService()
