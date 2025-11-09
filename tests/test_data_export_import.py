"""測試系統資料匯出和匯入功能"""
import json
from io import BytesIO

import pytest
from flask import url_for

from app.models import (
    KeywordCategory,
    LearningKeyword,
    User,
    Role,
    SiteSetting,
    SiteSettingKey,
)


@pytest.fixture
def admin_user(client):
    """創建管理員用戶並登入"""
    from app.extensions import db
    
    # 創建管理員
    admin = User(
        discord_id="admin_test_123",
        username="Test Admin",
        role=Role.ADMIN,
        active=True
    )
    db.session.add(admin)
    db.session.commit()
    
    # 模擬登入
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
    
    yield admin
    
    # 清理
    db.session.delete(admin)
    db.session.commit()


@pytest.fixture
def sample_data(client):
    """創建測試資料"""
    from app.extensions import db
    
    # 創建分類
    category = KeywordCategory(
        name="測試分類",
        slug="test-category",
        description="測試用分類",
        icon="bi-test"
    )
    db.session.add(category)
    db.session.flush()
    
    # 創建用戶
    user = User(
        discord_id="test_user_456",
        username="Test User",
        role=Role.USER,
        active=True
    )
    db.session.add(user)
    db.session.flush()
    
    # 創建關鍵字
    keyword = LearningKeyword(
        title="測試關鍵字",
        slug="test-keyword",
        description_markdown="# 測試內容",
        category_id=category.id,
        author_id=user.id,
        is_public=True
    )
    db.session.add(keyword)
    
    # 設定網站設定
    SiteSetting.set(SiteSettingKey.SITE_TITLE, "測試網站")
    
    db.session.commit()
    
    yield {
        'category': category,
        'user': user,
        'keyword': keyword
    }
    
    # 清理
    db.session.delete(keyword)
    db.session.delete(category)
    db.session.delete(user)
    db.session.commit()


def test_data_management_page_access(client, admin_user):
    """測試資料管理頁面訪問權限"""
    response = client.get(url_for('admin.data_management'))
    assert response.status_code == 200
    assert '系統資料管理' in response.get_data(as_text=True)


def test_export_system_data(client, admin_user, sample_data):
    """測試系統資料匯出"""
    response = client.get(url_for('admin.export_system_data'))
    
    assert response.status_code == 200
    assert response.content_type == 'application/json; charset=utf-8'
    
    # 解析匯出的資料
    data = json.loads(response.get_data(as_text=True))
    
    # 驗證基本結構
    assert 'export_info' in data
    assert 'users' in data
    assert 'categories' in data
    assert 'keywords' in data
    
    # 驗證匯出資訊
    assert data['export_info']['version'] == '1.0'
    assert data['export_info']['exported_by'] == admin_user.username
    
    # 驗證資料內容
    assert len(data['categories']) >= 1
    assert len(data['keywords']) >= 1
    assert len(data['users']) >= 2  # admin + test user
    
    # 驗證分類資料
    exported_category = next((c for c in data['categories'] if c['name'] == '測試分類'), None)
    assert exported_category is not None
    assert exported_category['slug'] == 'test-category'
    
    # 驗證關鍵字資料
    exported_keyword = next((k for k in data['keywords'] if k['title'] == '測試關鍵字'), None)
    assert exported_keyword is not None
    assert exported_keyword['slug'] == 'test-keyword'


def test_import_system_data_merge_mode(client, admin_user):
    """測試系統資料匯入 - 合併模式"""
    from app.extensions import db
    
    # 準備匯入資料
    import_data = {
        'export_info': {
            'version': '1.0',
            'exported_at': '2024-01-01T00:00:00',
            'exported_by': 'Test',
            'exported_by_id': 1
        },
        'users': [
            {
                'id': 9999,
                'discord_id': 'import_user_789',
                'username': 'Import User',
                'avatar_hash': None,
                'role': 'user',
                'is_active': True,
                'created_at': '2024-01-01T00:00:00'
            }
        ],
        'categories': [
            {
                'id': 9999,
                'name': '匯入分類',
                'slug': 'import-category',
                'description': '匯入測試',
                'position': 0,
                'icon': 'bi-import',
                'is_public': True,
                'created_at': '2024-01-01T00:00:00'
            }
        ],
        'keywords': [],
        'aliases': [],
        'videos': [],
        'navigation_links': [],
        'footer_links': [],
        'announcements': [],
        'site_settings': [],
        'goal_lists': [],
        'goal_items': []
    }
    
    # 創建 JSON 檔案
    json_data = json.dumps(import_data, ensure_ascii=False)
    file_data = BytesIO(json_data.encode('utf-8'))
    
    # 執行匯入
    response = client.post(
        url_for('admin.import_system_data'),
        data={
            'import_file': (file_data, 'test_import.json'),
            'import_mode': 'merge',
            'import_users': 'on',
            'import_categories': 'on',
            'import_keywords': 'on'
        },
        content_type='multipart/form-data',
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert '匯入成功' in response.get_data(as_text=True)
    
    # 驗證資料已匯入
    imported_user = User.query.filter_by(discord_id='import_user_789').first()
    assert imported_user is not None
    assert imported_user.username == 'Import User'
    
    imported_category = KeywordCategory.query.filter_by(slug='import-category').first()
    assert imported_category is not None
    assert imported_category.name == '匯入分類'
    
    # 清理
    db.session.delete(imported_user)
    db.session.delete(imported_category)
    db.session.commit()


def test_import_invalid_file_format(client, admin_user):
    """測試匯入無效格式的檔案"""
    # 創建無效的 JSON 檔案
    file_data = BytesIO(b'This is not valid JSON')
    
    response = client.post(
        url_for('admin.import_system_data'),
        data={
            'import_file': (file_data, 'invalid.json'),
            'import_mode': 'merge',
            'import_users': 'on'
        },
        content_type='multipart/form-data',
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert 'JSON 格式錯誤' in response.get_data(as_text=True)


def test_import_non_json_file(client, admin_user):
    """測試匯入非 JSON 檔案"""
    file_data = BytesIO(b'test content')
    
    response = client.post(
        url_for('admin.import_system_data'),
        data={
            'import_file': (file_data, 'test.txt'),
            'import_mode': 'merge'
        },
        content_type='multipart/form-data',
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert '只能匯入 JSON 檔案' in response.get_data(as_text=True)


def test_export_import_roundtrip(client, admin_user, sample_data):
    """測試完整的匯出-匯入循環"""
    from app.extensions import db
    
    # 1. 匯出資料
    export_response = client.get(url_for('admin.export_system_data'))
    assert export_response.status_code == 200
    
    export_data = json.loads(export_response.get_data(as_text=True))
    
    # 2. 刪除測試資料
    keyword = sample_data['keyword']
    category = sample_data['category']
    user = sample_data['user']
    
    keyword_title = keyword.title
    category_name = category.name
    
    db.session.delete(keyword)
    db.session.delete(category)
    db.session.delete(user)
    db.session.commit()
    
    # 3. 匯入資料
    json_data = json.dumps(export_data, ensure_ascii=False)
    file_data = BytesIO(json_data.encode('utf-8'))
    
    import_response = client.post(
        url_for('admin.import_system_data'),
        data={
            'import_file': (file_data, 'roundtrip.json'),
            'import_mode': 'merge',
            'import_users': 'on',
            'import_categories': 'on',
            'import_keywords': 'on'
        },
        content_type='multipart/form-data',
        follow_redirects=True
    )
    
    assert import_response.status_code == 200
    assert '匯入成功' in import_response.get_data(as_text=True)
    
    # 4. 驗證資料已恢復
    restored_category = KeywordCategory.query.filter_by(name=category_name).first()
    assert restored_category is not None
    
    restored_keyword = LearningKeyword.query.filter_by(title=keyword_title).first()
    assert restored_keyword is not None
    
    # 清理
    if restored_keyword:
        db.session.delete(restored_keyword)
    if restored_category:
        db.session.delete(restored_category)
    restored_user = User.query.filter_by(discord_id='test_user_456').first()
    if restored_user:
        db.session.delete(restored_user)
    db.session.commit()
