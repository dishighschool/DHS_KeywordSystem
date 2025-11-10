"""
測試關鍵字編輯器的換行保留功能
"""
import pytest
from app import create_app, db
import app.models as models


class TestNewlinePreservation:
    """測試 Markdown 內容中的換行是否被正確保存"""

    @pytest.fixture
    def app(self):
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_markdown_with_newlines_preserved(self, app):
        """測試包含換行的 Markdown 內容是否被正確保存"""
        with app.app_context():
            # 創建測試用戶和分類
            user = models.User(
                username="test_user",
                discord_id="123456",
                is_admin=False,
                is_active=True
            )
            db.session.add(user)
            
            category = models.Category(name="測試分類", icon="📚", slug="test-category")
            db.session.add(category)
            db.session.commit()

            # 測試不同類型的換行
            markdown_content = """第一行內容
第二行內容

第三行內容（上面有空行）

- 列表項目 1
- 列表項目 2

這是一段
包含多個
單行換行的內容"""

            keyword = models.LearningKeyword(
                title="測試關鍵字",
                slug="test-keyword",
                description_markdown=markdown_content,
                category_id=category.id,
                author_id=user.id,
                is_public=True
            )
            db.session.add(keyword)
            db.session.commit()

            # 重新查詢並檢查
            saved_keyword = models.LearningKeyword.query.filter_by(slug="test-keyword").first()
            assert saved_keyword is not None
            assert "第一行內容\n第二行內容" in saved_keyword.description_markdown
            assert "第三行內容（上面有空行）" in saved_keyword.description_markdown
            assert "- 列表項目 1\n- 列表項目 2" in saved_keyword.description_markdown
            
            # 驗證換行數量
            assert saved_keyword.description_markdown.count('\n') == markdown_content.count('\n')
            
    def test_strikethrough_in_markdown(self, app):
        """測試刪除線語法是否被正確保存"""
        with app.app_context():
            user = models.User(
                username="test_user",
                discord_id="123456",
                is_admin=False,
                is_active=True
            )
            db.session.add(user)
            
            category = models.Category(name="測試分類", icon="📚", slug="test-category")
            db.session.add(category)
            db.session.commit()

            markdown_with_strike = """這是~~刪除的文字~~正常文字

~~整行刪除~~

**粗體**~~刪除~~*斜體*"""

            keyword = models.LearningKeyword(
                title="測試刪除線",
                slug="test-strike",
                description_markdown=markdown_with_strike,
                category_id=category.id,
                author_id=user.id,
                is_public=True
            )
            db.session.add(keyword)
            db.session.commit()

            saved_keyword = models.LearningKeyword.query.filter_by(slug="test-strike").first()
            assert saved_keyword is not None
            assert "~~刪除的文字~~" in saved_keyword.description_markdown
            assert "~~整行刪除~~" in saved_keyword.description_markdown
            assert "**粗體**~~刪除~~*斜體*" in saved_keyword.description_markdown
