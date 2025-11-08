"""測試 YouTube URL 處理工具"""
import pytest
from app.utils.youtube import (
    extract_youtube_video_id,
    get_youtube_embed_url,
    is_youtube_url,
)


class TestExtractYoutubeVideoId:
    """測試 extract_youtube_video_id 函數"""

    def test_standard_watch_url(self):
        """測試標準 watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_watch_url_with_params(self):
        """測試帶其他參數的 watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        """測試 youtu.be 短網址"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url_with_timestamp(self):
        """測試帶時間戳的短網址"""
        url = "https://youtu.be/dQw4w9WgXcQ?t=123"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        """測試嵌入 URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_v_url(self):
        """測試 /v/ 格式 URL"""
        url = "https://www.youtube.com/v/dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        """測試 Shorts URL"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        """測試行動版 URL"""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_without_protocol(self):
        """測試沒有協議的 URL"""
        url = "//www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_without_www(self):
        """測試沒有 www 的 URL"""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        """測試無效 URL"""
        url = "https://example.com/video"
        assert extract_youtube_video_id(url) is None

    def test_empty_url(self):
        """測試空字串"""
        assert extract_youtube_video_id("") is None

    def test_none_url(self):
        """測試 None"""
        assert extract_youtube_video_id(None) is None  # type: ignore[arg-type]


class TestGetYoutubeEmbedUrl:
    """測試 get_youtube_embed_url 函數"""

    def test_standard_watch_url(self):
        """測試標準 watch URL 轉換"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_short_url(self):
        """測試短網址轉換"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_embed_url_unchanged(self):
        """測試已經是嵌入 URL 的情況"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_with_autoplay(self):
        """測試添加自動播放參數"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_youtube_embed_url(url, autoplay=True)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"

    def test_with_start_time_from_url(self):
        """測試從 URL 提取開始時間"""
        url = "https://youtu.be/dQw4w9WgXcQ?t=123"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ?start=123"

    def test_with_manual_start_time(self):
        """測試手動指定開始時間"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_youtube_embed_url(url, start_time=456)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ?start=456"

    def test_with_autoplay_and_start_time(self):
        """測試同時添加自動播放和開始時間"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_youtube_embed_url(url, autoplay=True, start_time=789)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&start=789"

    def test_shorts_url(self):
        """測試 Shorts URL 轉換"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_invalid_url_returns_original(self):
        """測試無效 URL 返回原始 URL"""
        url = "https://example.com/video"
        result = get_youtube_embed_url(url)
        assert result == url

    def test_with_other_query_params(self):
        """測試帶其他查詢參數的 URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxxxxx&index=1"
        result = get_youtube_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"


class TestIsYoutubeUrl:
    """測試 is_youtube_url 函數"""

    def test_standard_youtube_url(self):
        """測試標準 YouTube URL"""
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_short_url(self):
        """測試短網址"""
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_mobile_url(self):
        """測試行動版 URL"""
        assert is_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_embed_url(self):
        """測試嵌入 URL"""
        assert is_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ") is True

    def test_shorts_url(self):
        """測試 Shorts URL"""
        assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True

    def test_non_youtube_url(self):
        """測試非 YouTube URL"""
        assert is_youtube_url("https://example.com/video") is False

    def test_empty_url(self):
        """測試空字串"""
        assert is_youtube_url("") is False

    def test_none_url(self):
        """測試 None"""
        assert is_youtube_url(None) is False  # type: ignore[arg-type]


class TestRealWorldUrls:
    """測試真實世界的 URL 範例"""

    def test_watch_url_with_playlist(self):
        """測試帶播放清單的 watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        video_id = extract_youtube_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
        
        embed_url = get_youtube_embed_url(url)
        assert embed_url == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_watch_url_with_timestamp(self):
        """測試帶時間戳的 watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
        video_id = extract_youtube_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_shared_short_url(self):
        """測試分享的短網址"""
        url = "https://youtu.be/dQw4w9WgXcQ?si=xxxxxxxxxxxxxxxx"
        video_id = extract_youtube_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_nocookie_embed(self):
        """測試 no-cookie 嵌入 URL (注意: 當前實現不支援)"""
        # 這個測試說明了一個限制,可以在未來改進
        url = "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
        # 當前實現不支援 youtube-nocookie.com
        video_id = extract_youtube_video_id(url)
        # 這應該是 None,因為我們沒有處理這種格式
        assert video_id is None
