"""
安全的 Markdown 渲染工具

使用 markdown2 進行 Markdown 解析，使用 bleach 進行 HTML 清理，
確保輸出的 HTML 安全且符合標準。
"""
from html import unescape
from typing import Optional

import bleach
from markdown2 import markdown


# 允許的 HTML 標籤
ALLOWED_TAGS = [
    # 標題
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # 段落和文本格式
    'p', 'br', 'hr',
    # 強調
    'strong', 'b', 'em', 'i', 'u', 's', 'del', 'strike', 'mark',
    # 列表
    'ul', 'ol', 'li',
    # 連結和圖片
    'a', 'img',
    # 引用和代碼
    'blockquote', 'code', 'pre',
    # 表格
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
    # 其他
    'div', 'span', 'sup', 'sub',
    # 待辦清單
    'input',
]

# 允許的屬性
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
    'code': ['class'],
    'pre': ['class'],
    'table': ['class'],
    'th': ['align', 'colspan', 'rowspan'],
    'td': ['align', 'colspan', 'rowspan'],
    'input': ['type', 'checked', 'disabled'],
}

# 允許的協議
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# Markdown2 extras
MARKDOWN_EXTRAS = [
    'fenced-code-blocks',  # 代碼塊 ```
    'tables',              # 表格
    'strike',              # 刪除線 ~~text~~
    'task_lists',          # 待辦清單 - [ ]
    'break-on-newline',    # 單個換行轉為 <br>
    'code-friendly',       # 改進代碼塊處理
    'cuddled-lists',       # 改進列表處理
    'header-ids',          # 標題自動生成 ID
    # 注意：不使用 smarty-pants，因為它會轉換引號導致 HTML 屬性問題
    # 注意：不使用 numbering，避免影響標題
]


def render_markdown_safe(
    markdown_text: str,
    extras: Optional[list[str]] = None,
    strip: bool = True,
) -> str:
    """
    安全地渲染 Markdown 為 HTML
    
    Args:
        markdown_text: Markdown 格式的文本
        extras: 要啟用的 markdown2 extras，默認使用 MARKDOWN_EXTRAS
        strip: 是否移除不允許的標籤（True）或轉義（False）
        
    Returns:
        清理後的安全 HTML
    """
    if not markdown_text:
        return ""
    
    # 1. 解碼 HTML 實體（如果有的話）
    decoded_text = unescape(markdown_text)
    
    # 2. 使用 markdown2 渲染 Markdown
    if extras is None:
        extras = MARKDOWN_EXTRAS
    
    # 注意：不使用 safe_mode，因為我們會用 bleach 做更徹底的清理
    html = markdown(decoded_text, extras=extras)
    
    # 3. 使用 bleach 清理 HTML
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=strip,  # True: 移除不允許的標籤, False: 轉義為文本
    )
    
    # 4. 為連結添加安全屬性
    clean_html = bleach.linkify(
        clean_html,
        callbacks=[_add_nofollow_noopener],
        skip_tags=['pre', 'code'],
    )
    
    return clean_html


def _add_nofollow_noopener(attrs, new=False):
    """
    為外部連結添加 rel="noopener noreferrer" 屬性
    防止 tabnabbing 攻擊
    """
    href = attrs.get((None, 'href'), '')
    
    # 只處理 http/https 連結
    if href.startswith('http://') or href.startswith('https://'):
        # 設置 target="_blank"
        attrs[(None, 'target')] = '_blank'
        
        # 設置 rel 屬性
        rel_values = ['noopener', 'noreferrer']
        existing_rel = attrs.get((None, 'rel'), '')
        if existing_rel:
            rel_values.append(existing_rel)
        attrs[(None, 'rel')] = ' '.join(rel_values)
    
    return attrs


def render_markdown_for_preview(markdown_text: str) -> dict:
    """
    渲染 Markdown 用於預覽
    返回包含 HTML 和純文本的字典
    
    Args:
        markdown_text: Markdown 格式的文本
        
    Returns:
        {
            'html': 清理後的 HTML,
            'text': 純文本版本,
            'word_count': 字數統計
        }
    """
    html = render_markdown_safe(markdown_text)
    
    # 提取純文本用於統計
    text = bleach.clean(html, tags=[], strip=True)
    word_count = len(text.split()) if text else 0
    
    return {
        'html': html,
        'text': text,
        'word_count': word_count,
    }


def strip_markdown_to_text(markdown_text: str) -> str:
    """
    將 Markdown 轉換為純文本，移除所有格式
    
    Args:
        markdown_text: Markdown 格式的文本
        
    Returns:
        純文本字符串
    """
    if not markdown_text:
        return ""
    
    # 先渲染為 HTML
    html = markdown(markdown_text, extras=MARKDOWN_EXTRAS)
    
    # 移除所有 HTML 標籤
    text = bleach.clean(html, tags=[], strip=True)
    
    # 清理多餘的空白
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)
