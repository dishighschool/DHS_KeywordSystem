"""YouTube URL 處理工具"""
import re
from urllib.parse import urlparse, parse_qs


def extract_youtube_video_id(url: str) -> str | None:
    """
    從各種 YouTube URL 格式中提取 video ID
    
    支援的格式:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/watch?v=VIDEO_ID&feature=share
    - https://youtu.be/VIDEO_ID
    - https://youtu.be/VIDEO_ID?t=123
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    
    Args:
        url: YouTube URL 字串
        
    Returns:
        str | None: 11 字元的 video ID,如果無法提取則返回 None
    """
    if not url:
        return None
    
    # 正規表達式模式列表
    patterns = [
        # youtu.be/VIDEO_ID
        r'(?:https?:)?(?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        
        # youtube.com/watch?v=VIDEO_ID
        r'(?:https?:)?(?://)?(?:www\.)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        
        # youtube.com/embed/VIDEO_ID
        r'(?:https?:)?(?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        
        # youtube.com/v/VIDEO_ID
        r'(?:https?:)?(?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
        
        # youtube.com/shorts/VIDEO_ID
        r'(?:https?:)?(?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    
    # 嘗試所有模式
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # 嘗試解析 query string (用於處理帶其他參數的 URL)
    try:
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if parsed.path == '/watch':
                query_params = parse_qs(parsed.query)
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                    if len(video_id) == 11:
                        return video_id
    except Exception:
        pass
    
    return None


def get_youtube_embed_url(url: str, autoplay: bool = False, start_time: int | None = None) -> str:
    """
    將 YouTube URL 轉換為嵌入 URL
    
    Args:
        url: 原始 YouTube URL
        autoplay: 是否自動播放 (預設 False)
        start_time: 開始時間(秒),從 URL 參數或手動指定
        
    Returns:
        str: YouTube 嵌入 URL,如果無法解析則返回原 URL
    """
    video_id = extract_youtube_video_id(url)
    
    if not video_id:
        # 無法解析,返回原 URL
        return url
    
    # 建立嵌入 URL
    embed_url = f"https://www.youtube.com/embed/{video_id}"
    
    # 處理額外參數
    params = []
    
    if autoplay:
        params.append("autoplay=1")
    
    # 嘗試從原 URL 提取開始時間
    if not start_time:
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 't' in query_params:
                # youtu.be/?t=123 格式
                start_time = int(query_params['t'][0])
            elif 'start' in query_params:
                # 某些 URL 使用 start 參數
                start_time = int(query_params['start'][0])
        except (ValueError, IndexError):
            pass
    
    if start_time:
        params.append(f"start={start_time}")
    
    # 加入參數
    if params:
        embed_url += "?" + "&".join(params)
    
    return embed_url


def is_youtube_url(url: str) -> bool:
    """
    檢查 URL 是否為 YouTube URL
    
    Args:
        url: 要檢查的 URL
        
    Returns:
        bool: 如果是 YouTube URL 返回 True
    """
    if not url:
        return False
    
    youtube_domains = [
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'youtu.be',
        'www.youtu.be'
    ]
    
    try:
        parsed = urlparse(url)
        return parsed.hostname in youtube_domains
    except Exception:
        return False
