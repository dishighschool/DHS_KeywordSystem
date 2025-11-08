"""SEO text helpers for keyword content generation."""
from typing import Optional
import logging


logger = logging.getLogger(__name__)

try:
    from pypinyin import pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    PYPINYIN_AVAILABLE = False
    pinyin = None  # type: ignore[assignment]
    Style = None  # type: ignore[assignment]
    logger.warning("pypinyin 未安裝,注音轉換功能將受限。請執行: pip install pypinyin")


def convert_bopomofo_to_keyboard(bopomofo: str) -> str:
    """
    將注音符號轉換為鍵盤上的英文字母
    
    Args:
        bopomofo: 注音符號字串 (如: ㄕˊㄇㄜ˙)
    
    Returns:
        對應的鍵盤英文字母 (如: g6ak7)
    """
    # 注音符號到英文鍵盤的完整映射表
    bopomofo_map = {
        'ㄅ': '1', 'ㄆ': 'q', 'ㄇ': 'a', 'ㄈ': 'z',
        'ㄉ': '2', 'ㄊ': 'w', 'ㄋ': 's', 'ㄌ': 'x',
        'ㄍ': 'e', 'ㄎ': 'd', 'ㄏ': 'c', 'ㄐ': 'r',
        'ㄑ': 'f', 'ㄒ': 'v', 'ㄓ': '5', 'ㄔ': 't',
        'ㄕ': 'g', 'ㄖ': 'b', 'ㄗ': 'y', 'ㄘ': 'h',
        'ㄙ': 'n', 'ㄧ': 'u', 'ㄨ': 'j', 'ㄩ': 'm',
        'ㄚ': '8', 'ㄛ': 'i', 'ㄜ': 'k', 'ㄝ': ',',
        'ㄞ': '9', 'ㄟ': 'o', 'ㄠ': 'l', 'ㄡ': '.',
        'ㄢ': '0', 'ㄣ': 'p', 'ㄤ': ';', 'ㄥ': '/',
        'ㄦ': '-', 'ˊ': '6', 'ˇ': '3', 'ˋ': '4', '˙': '7',
        ' ': ' ',  # 保留空格
    }
    
    result = []
    for char in bopomofo:
        if char in bopomofo_map:
            result.append(bopomofo_map[char])
        # 忽略未映射的字符
    
    return ''.join(result)


def generate_bopomofo_typo(text: str) -> str:
    """
    將中文轉換為注音輸入法忘記切換時的英文亂碼
    使用 pypinyin 庫進行轉換
    
    Args:
        text: 中文文字
    
    Returns:
        注音輸入法對應的英文字母
    """
    if not PYPINYIN_AVAILABLE or pinyin is None or Style is None:
        return ""
    
    try:
        assert pinyin is not None and Style is not None
        # 使用 pypinyin 獲取注音
        bopomofo_list = pinyin(text, style=Style.BOPOMOFO)
        
        # 展平列表並合併注音
        bopomofo_str = ''.join([item[0] for item in bopomofo_list])
        
        # 轉換為鍵盤字母
        return convert_bopomofo_to_keyboard(bopomofo_str)
    
    except Exception:
        logger.exception("pypinyin 轉換失敗")
        return ""


def generate_common_typos(keyword: str) -> list[str]:
    """
    生成常見的打字錯誤
    包括注音輸入法錯誤、相似音等
    """
    typos = []
    
    # 注音輸入法忘記切換
    bopomofo_typo = generate_bopomofo_typo(keyword)
    if bopomofo_typo and bopomofo_typo != keyword.lower():
        typos.append(bopomofo_typo)
    
    # 可以擴展更多類型的錯誤:
    # - 相似音
    # - 缺字
    # - 多字
    # - 順序錯誤
    
    return typos


def generate_search_questions(keyword: str, typos: Optional[list[str]] = None) -> list[str]:
    """
    生成常見的搜尋問句,包含注音輸入法錯誤
    
    Args:
        keyword: 關鍵字名稱
        typos: 注音輸入法錯誤列表
    
    Returns:
        問句列表 (包含注音輸入法錯誤)
    """
    typos = typos or []
    
    questions = [
        f"什麼是{keyword}",
        f"{keyword}是什麼",
        f"{keyword}的意思",
        f"{keyword}的定義",
        f"如何使用{keyword}",
        f"{keyword}怎麼用",
        f"{keyword}如何應用",
        f"怎麼學{keyword}",
        f"{keyword}教學",
        f"{keyword}入門",
        f"學習{keyword}",
        f"{keyword}基礎",
        f"{keyword}範例",
        f"{keyword}實例",
        f"{keyword}說明",
        f"{keyword}解釋",
        f"理解{keyword}",
        f"認識{keyword}",
    ]
    
    # 將注音輸入法錯誤加入問句列表 (作為常見搜尋錯誤)
    if typos:
        for typo in typos[:3]:  # 最多加入3個錯誤
            if typo and typo != keyword.lower():  # 避免重複
                questions.extend([
                    f"{typo}是什麼",
                    f"什麼是{typo}",
                ])
    
    return questions


def generate_seo_text(keyword: str, aliases: Optional[list[str]] = None) -> dict:
    """
    生成 SEO 優化文字
    
    Args:
        keyword: 關鍵字名稱
        aliases: 別名列表
    
    Returns:
        包含各種 SEO 元素的字典
    """
    aliases = aliases or []
    
    # 生成打字錯誤 (優先生成,因為需要用於問句)
    typos = generate_common_typos(keyword)
    
    # 生成問句 (包含打字錯誤)
    questions = generate_search_questions(keyword, typos)
    
    # 組合成自然的段落
    paragraphs = []
    
    # 第一段: 介紹和問句
    intro_questions = questions[:6]
    intro = f"想了解{keyword}嗎？許多人搜尋「{intro_questions[0]}」、「{intro_questions[1]}」等問題。"
    intro += f"本文將為您詳細說明{keyword}的相關知識，包含{intro_questions[4]}、{intro_questions[5]}等實用資訊。"
    paragraphs.append(intro)
    
    # 第二段: 別名
    if aliases:
        alias_text = f"{keyword}又稱為" + "、".join(aliases[:5])
        if len(aliases) > 5:
            alias_text += "等"
        alias_text += f"，這些都是指同一個概念。"
        paragraphs.append(alias_text)
    
    # 第三段: 常見錯誤 (注音輸入法) - 總是顯示
    if typos:
        typo_text = f"在搜尋時，{keyword}常被誤輸入為「{typos[0]}」"
        if len(typos) > 1:
            typo_text += f"、「{typos[1]}」"
        if len(typos) > 2:
            typo_text += f"或「{typos[2]}」"
        typo_text += "等形式（注音輸入法未切換）。"
        paragraphs.append(typo_text)
    else:
        # 即使沒有打字錯誤,也嘗試生成關鍵字的注音錯誤
        keyword_typo = generate_bopomofo_typo(keyword)
        if keyword_typo and keyword_typo != keyword.lower():
            typo_text = f"在搜尋時，{keyword}常被誤輸入為「{keyword_typo}」等形式（注音輸入法未切換）。"
            paragraphs.append(typo_text)
            typos = [keyword_typo]  # 更新 typos 列表
    
    # 第四段: 學習相關
    learning_questions = [q for q in questions if '學' in q or '教' in q or '入門' in q]
    if learning_questions:
        learning_text = f"想要{learning_questions[0]}？"
        learning_text += f"透過系統化的{keyword}教學，您可以快速掌握{keyword}的核心概念與應用方式。"
        paragraphs.append(learning_text)
    
    return {
        'keyword': keyword,
        'questions': questions,
        'typos': typos,
        'aliases': aliases,
        'paragraphs': paragraphs,
        'full_text': ' '.join(paragraphs)
    }


def generate_seo_html(keyword: str, aliases: Optional[list[str]] = None) -> str:
    """生成 SEO 優化的純文字內容."""
    seo_data = generate_seo_text(keyword, aliases)
    
    text_parts = []
    
    # 標題
    text_parts.append(f"關於「{keyword}」的常見問題\n")
    
    # 段落
    for paragraph in seo_data['paragraphs']:
        text_parts.append(paragraph)
    
    # 問句列表 (優化選擇邏輯,確保包含注音錯誤)
    if seo_data['questions']:
        # 智能選擇問句:
        # 1. 優先選擇前 6 個基本問句 (什麼是、如何使用等)
        # 2. 加入包含注音錯誤的問句 (如果有的話)
        selected_questions = []
        
        # 先加入基本問句
        basic_questions = [q for q in seo_data['questions'][:18] 
                          if not any(typo in q for typo in seo_data['typos'])]
        selected_questions.extend(basic_questions[::3][:6])  # 每3個取1個,最多6個
        
        # 再加入注音錯誤問句 (最多2個)
        if seo_data['typos']:
            typo_questions = [q for q in seo_data['questions'] 
                            if any(typo in q for typo in seo_data['typos'])]
            selected_questions.extend(typo_questions[:2])
        
        text_parts.append("\n相關搜尋：" + '、'.join(selected_questions))
    
    return '\n\n'.join(text_parts)
