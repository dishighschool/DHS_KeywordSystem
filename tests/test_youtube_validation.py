"""Test YouTube URL validation in forms and database storage."""

import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.forms import validate_youtube_url
from app.admin.routes import _apply_video_updates
from app.models import LearningKeyword, YouTubeVideo
from wtforms import StringField
from wtforms.validators import ValidationError


def test_youtube_url_validator():
    """Test the YouTube URL validator function directly."""
    app = create_app()

    with app.app_context():
        # Create a mock field
        field = StringField()
        
        # Test valid YouTube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            field.data = url
            # Should not raise ValidationError
            try:
                validate_youtube_url(None, field)
                # If we get here, validation passed
            except ValidationError as e:
                pytest.fail(f"Valid YouTube URL {url} should not raise validation error: {e}")
        
        # Test invalid URLs
        invalid_urls = [
            "https://google.com",
            "https://vimeo.com/123",
            "not-a-url",
            "https://youtube.com/channel/UC123",
            "https://www.youtube.com/playlist?list=PL123"
        ]
        
        for url in invalid_urls:
            field.data = url
            with pytest.raises(ValidationError) as exc_info:
                validate_youtube_url(None, field)
            assert "必須是有效的 YouTube 影片連結" in str(exc_info.value)
        
        # Test empty string (should not raise error due to Optional validator)
        field.data = ""
        try:
            validate_youtube_url(None, field)
            # Should not raise error for empty string
        except ValidationError:
            pytest.fail("Empty string should not raise validation error")


def test_video_updates_filters_invalid_urls():
    """Test that _apply_video_updates filters out invalid YouTube URLs."""
    app = create_app()

    with app.app_context():
        # Create a mock keyword with videos relationship
        keyword = LearningKeyword(
            title="Test Keyword",
            description_markdown="Test content",
            category_id=1,
            author_id=1
        )
        # Initialize videos relationship
        keyword.videos = []
        
        # Create a mock form data structure
        class MockEntry:
            def __init__(self, data):
                self.data = data
        
        class MockFormFieldList:
            def __init__(self, entries_data):
                self.entries = [MockEntry(data) for data in entries_data]
        
        # Create form with mixed valid/invalid URLs
        form_data = [
            {"title": "Valid Video", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            {"title": "Invalid Video", "url": "https://google.com"},
            {"title": "Another Valid Video", "url": "https://youtu.be/dQw4w9WgXcQ"},
            {"title": "Empty URL", "url": ""},
            {"title": "None URL", "url": None}
        ]
        mock_form = MagicMock()
        mock_form.videos = MockFormFieldList(form_data)
        
        # Mock the is_youtube_url function to return True for valid URLs
        def mock_extract_youtube_video_id(url):
            if not url:
                return None
            if url.startswith("https://www.youtube.com/watch?v=") or url.startswith("https://youtu.be/"):
                return "dQw4w9WgXcQ"  # Mock video ID
            return None
        
        # Apply video updates with mocked is_youtube_url
        with patch('app.utils.youtube.extract_youtube_video_id', side_effect=mock_extract_youtube_video_id):
            _apply_video_updates(keyword, mock_form)  # type: ignore
        
        # Should only have 2 valid videos
        assert len(keyword.videos) == 2
        assert keyword.videos[0].title == "Valid Video"
        assert keyword.videos[0].url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert keyword.videos[1].title == "Another Valid Video"
        assert keyword.videos[1].url == "https://youtu.be/dQw4w9WgXcQ"