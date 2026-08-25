"""翻译模块：中英双语互译，带降级策略。每日执行不消耗 AI Token。"""
import queue
import re
import threading
import sys
import time
from typing import Optional

from config import TRANSLATION_DELAY

TRANSLATION_TIMEOUT = 3  # 单次翻译超时秒数

# Argos 的中译英/英译中模型由 GitHub Actions 预先安装，翻译时不依赖在线额度。
_ARGOS_LOCK = threading.Lock()
_ARGOS_AVAILABLE = None

# 翻译服务偶尔会把错误页面内容当作“译文”返回，不能写入新闻数据。
ERROR_RESPONSE_MARKERS = (
    "error 500",
    "that's an error",
    "there was an error",
    "please try again later",
    "invalid source language",
)


def _has_chinese(text: str) -> bool:
    """检测文本是否包含中文字符（Unicode CJK 范围）。"""
    return bool(re.search(r"[一-鿿㐀-䶿]", text))


def _is_error_response(text: str) -> bool:
    """识别翻译服务返回的错误页面文本。"""
    normalized = re.sub(r"\s+", " ", str(text)).strip().lower().replace("’", "'")
    if "invalid source language" in normalized:
        return True
    return sum(marker in normalized for marker in ERROR_RESPONSE_MARKERS) >= 3


def _is_usable_translation(text: Optional[str], target: str) -> bool:
    """确认翻译结果不是错误页面，且中文目标确实含有中文。"""
    if not text or _is_error_response(text):
        return False
    return target != "zh-CN" or _has_chinese(text)


def _run_with_timeout(func, *args, timeout: int = TRANSLATION_TIMEOUT):
    """在线程中运行函数，带超时控制。

    这里使用守护线程，避免超时后主进程还要等后台翻译线程收尾。
    """
    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def _target():
        try:
            result_queue.put(("ok", func(*args)))
        except Exception as exc:  # noqa: BLE001
            result_queue.put(("err", exc))

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    try:
        status, payload = result_queue.get(timeout=timeout)
    except queue.Empty:
        return None

    if status == "ok":
        return payload
    return None


def _google_translate(text: str, target: str) -> Optional[str]:
    """通过 deep-translator 调用 Google Translate（免费，无需 API Key）。"""
    def _call():
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="auto", target=target).translate(text)
        return result if _is_usable_translation(result, target) else None

    return _run_with_timeout(_call)


def _argos_translate(text: str, target: str) -> Optional[str]:
    """使用已安装的 Argos 离线模型翻译英文标题为简体中文。"""
    global _ARGOS_AVAILABLE

    if target != "zh-CN":
        return None

    def _call():
        global _ARGOS_AVAILABLE
        try:
            import argostranslate.package
            import argostranslate.translate

            with _ARGOS_LOCK:
                if _ARGOS_AVAILABLE is None:
                    installed = argostranslate.package.get_installed_packages()
                    _ARGOS_AVAILABLE = any(
                        package.from_code == "en" and package.to_code == "zh"
                        for package in installed
                    )

            if not _ARGOS_AVAILABLE:
                return None

            result = argostranslate.translate.translate(text, "en", "zh")
            return result if _is_usable_translation(result, target) else None
        except Exception:  # noqa: BLE001
            _ARGOS_AVAILABLE = False
            return None

    return _run_with_timeout(_call)


def _mymemory_translate(text: str, target: str) -> Optional[str]:
    """通过 deep-translator 调用 MyMemory（免费，无需 API Key）。"""
    def _call():
        from deep_translator import MyMemoryTranslator
        source = "zh-CN" if _has_chinese(text) else "en"
        result = MyMemoryTranslator(source=source, target=target).translate(text)
        return result if _is_usable_translation(result, target) else None

    return _run_with_timeout(_call)


def _translate_fallback(text: str, target: str) -> Optional[str]:
    """备选翻译：使用 translate 库。"""
    def _call():
        from translate import Translator
        translator = Translator(to_lang=target)
        result = translator.translate(text)
        return result if _is_usable_translation(result, target) else None

    return _run_with_timeout(_call)


def translate_text(text: str, target_lang: str) -> tuple[str, str]:
    """
    翻译文本到目标语言。返回 (译文, 质量标记)。

    质量标记: "auto" = 翻译成功, "fallback" = 降级为原文

    翻译链:
        1. Argos 离线模型（英文 → 简体中文）
        2. deep-translator (GoogleTranslator)
        3. deep-translator (MyMemoryTranslator)
        4. translate 库
        5. 原文降级
    """
    # 英文标题优先使用离线模型，不受在线翻译服务额度影响。
    if target_lang == "zh-CN" and not _has_chinese(text):
        result = _argos_translate(text, target_lang)
        if _is_usable_translation(result, target_lang):
            return result, "offline"

    # 尝试主翻译方案
    result = _google_translate(text, target_lang)
    if _is_usable_translation(result, target_lang):
        return result, "auto"

    # 备用免费翻译服务
    result = _mymemory_translate(text, target_lang)
    if _is_usable_translation(result, target_lang):
        return result, "auto"

    # 尝试备选方案
    result = _translate_fallback(text, target_lang)
    if _is_usable_translation(result, target_lang):
        return result, "auto"

    # 全部失败，降级为原文
    print(f"[WARN] 翻译失败，使用原文: {text[:30]}...", file=sys.stderr)
    return text, "fallback"


def translate_articles(articles: list) -> list:
    """
    批量翻译文章列表。

    每条文章产生两个字段:
        - summary_zh: 中文摘要
        - summary_en: 英文摘要

    中文源文章 → summary_zh = 原文, summary_en = 翻译
    英文源文章 → summary_en = 原文, summary_zh = 翻译
    """
    count = 0
    for article in articles:
        title = article.summary
        is_zh = _has_chinese(title)

        if is_zh:
            article.summary_zh = title
            en_text, quality = translate_text(title, "en")
            article.summary_en = en_text
        else:
            article.summary_en = title
            zh_text, quality = translate_text(title, "zh-CN")
            article.summary_zh = zh_text

        article.translation_quality = quality
        count += 1

        # 翻译间隔，防止被限速
        time.sleep(TRANSLATION_DELAY)

    print(f"翻译完成: {count} 篇")
    return articles
