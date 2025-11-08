# Python Module Maintenance & Development Guide

> 本指南涵蓋專案中每一個 Python 檔案的功能定位、開發注意事項與維護工作。請在進行修改或部署前，先參考對應章節以確保一致性與穩定性。

---

## 根目錄模組
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| wsgi.py | WSGI 入口，提供伺服器載入 `create_app()` 的鉤子。 | 保持僅匯入並呼叫 `create_app`，自訂配置請轉往 `config.py` 或環境變數。 | 部屬後確認 WSGI 伺服器 (gunicorn/uwsgi) 指向正確模組；監控啟動日誌是否有匯入例外。 | `tests/test_main.py` 冒煙涵蓋核心路由。 |
| rename_users_to_members.py | 一次性腳本，批次將文案由「用戶」改為「成員」。 | 更新置換規則時注意 `EXCLUDE_PATTERNS` 以免破壞程式變數；保留 UTF-8 編碼。 | 僅在大規模文案調整時執行，完成後重新檢查 git diff；避免在 production 執行未測試腳本。 | 無自動測試；建議手動驗證替換結果。 |

---

## `app/` 封裝層
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| app/__init__.py | Flask 應用工廠、Blueprint/Extensions 註冊、錯誤處理與 CLI。 | 新增元件請透過 `_register_extensions`/`_register_blueprints`；保留 CLI 使用 `click`。 | 每次升級 Flask/擴充套件前檢查初始化流程；監看 `LegacyAPIWarning` 轉換為 `db.session.get`。 | `tests/conftest.py` 建立 app fixture；多數整合測試皆涵蓋。 |
| app/config.py | 設定類別與環境變數對應。 | 新設定以類別屬性維護；敏感值使用環境變數，不寫死預設密鑰。 | 部屬時驗證必要環境變數是否存在；審視是否有過期設定。 | 間接被所有測試使用。 |
| app/extensions.py | 初始化 Flask 擴充。 | 僅建立擴充執行個體，不做邏輯；擴充更新需同步更新 requirements。 | 定期升級擴充版本並跑測試；注意初始化順序符合依賴。 | 由 `tests/conftest.py` 間接涵蓋。 |
| app/forms.py | WTForms 表單定義。 | 新表單遵循 CSRF 與驗證器配置；避免商業邏輯放入表單。 | 更新欄位後同步調整模板與翻譯；執行 `pytest` 確認。 | 表單使用路由對應測試，例如 `tests/test_admin` (若後續新增)。 |
| app/keyword_linker.py | 關鍵字自動連結邏輯與快取。 | 調整演算法時維持 `KeywordLinker` 公開 API；新增規則需更新測試。 | 定期重建快取以反映新關鍵字；監控效能。 | `tests/test_keyword_linking.py`。 |
| app/models.py | SQLAlchemy 模型與常數。 | 模型更新需加 migration；避免循環匯入；保持 `slugify` 與 mixin 工具。 | 檢視資料庫欄位與模型同步；執行 alembic 遷移。 | 多數測試操作模型，包括 `tests/test_main.py`、`tests/test_keyword_linking.py`。 |
| app/seed.py | 初始資料填充服務。 | 新增種子流程請使用 `SeedService` 方法，保持 idempotent。 | 部屬後執行 `flask seed` 並確認 edit log；避免重複撰寫資料。 | 若有自定測試須在 `tests` 目錄擴增。 |
| app/sitemap.py | Sitemap 產生與快取管理。 | 更新 sitemap 結構時注意 blueprint route；保留 `sitemap_manager`. | 定期檢視 sitemap 快取是否更新；監控 Search Console。 | `tests/test_sitemap.py`。 |

### `app/admin/`
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| app/admin/__init__.py | 建立 admin Blueprint。 | 保持輕量，僅含 `Blueprint` 定義。 | 若調整匯入路徑請更新 `__all__`。 | 間接由 `tests/test_keyword_linking.py`。 |
| app/admin/routes.py | 管理後台路由與 JSON API。 | 新增 API 請沿用 `admin_required`、回傳 `{success: bool}`；表單提交保持 CSRF。 | 定期審查檔案上傳與權限；記錄 edit log。 | `tests/test_json_api_fix.py`、`tests/test_keyword_linking.py`。 |

### `app/auth/`
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| app/auth/__init__.py | Auth Blueprint 註冊。 | 保持初始化簡潔。 | 調整路徑時同步更新 URL。 | `tests/test_main.py` 間接覆蓋登入流程。 |
| app/auth/discord.py | Discord OAuth 客戶端設定。 | 修改 scope 或 API 時保持錯誤處理；勿透露 client secret。 | 憑證更新後測試登入流程；監控 OAuth 回呼。 | 手動或 `tests/test_main` (需擴充)。 |
| app/auth/routes.py | 登入、登出與授權流程。 | 導向需驗證 redirect URL；保留 CSRF 保護。 | 定期檢視登入失敗記錄；測試 refresh token 邏輯。 | 建議擴充 pytest (目前未覆蓋，需手動測)。 |

### `app/main/`
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| app/main/__init__.py | Main Blueprint 定義。 | 保持匯入簡潔。 | 調整 blueprint 名稱需同步模板路徑。 | `tests/test_main.py`。 |
| app/main/routes.py | 公開頁面、搜尋、API。 | 新增路由時確保 SEO meta、使用 `keyword_linker`；API 請處理快取。 | 監控熱門頁面效能；更新 sitemap 時同步。 | `tests/test_main.py`、`tests/test_keyword_linking.py`。 |

### `app/utils/`
| 路徑 | 功能定位 | 開發指引 | 維護工作 | 關聯測試 |
| --- | --- | --- | --- | --- |
| app/utils/__init__.py | 公用方法封裝匯出。 | 僅用於命名空間管理。 | 調整匯出時同步檢查依賴模組。 | 間接涵蓋。 |
| app/utils/edit_logger.py | 編輯操作記錄工具。 | 新增事件時保持結構化 payload；使用 SQLAlchemy session。 | 定期清理日誌資料表，避免膨脹。 | 若新增事件請補測試。 |
| app/utils/seo.py | SEO 文字、注音錯誤生成。 | 注音功能須處理 `pypinyin` 缺失；避免 `print`，統一 `logging`. | 監控 `logger.warning`；更新後重新生成內容。 | `tests/test_seo_generation.py`、`tests/test_chinese_seo.py`、`tests/test_bopomofo.py`、`tests/test_pypinyin_api.py`、`tests/test_plain_text_seo.py`。 |
| app/utils/theme.py | 主題設定與配色工具。 | 修改時確保與模板一致；提供預設值。 | 部屬前確認顏色常數符合設計稿。 | 手動檢視或補測。 |
| app/utils/youtube.py | YouTube URL 驗證與 embed 生成。 | 更新時保持正則覆蓋常見格式；避免外部 API 依賴。 | 檢查嵌入網址是否符合 CSP；監控失效案例。 | `tests/test_youtube_utils.py`。 |

---

## `migrations/` 遷移腳本
| 路徑 | 功能定位 | 開發指引 | 維護工作 |
| --- | --- | --- | --- |
| migrations/env.py | Alembic 環境設定。 | 調整 metadata 匯入時確保指向 `app.models`. | 更新 SQLAlchemy/Alembic 版本後檢查相容性。 |
| migrations/script.py.mako | 遷移模板。 | 自訂模板請保持 idempotent。 | 升級 Alembic 後同步調整模板語法。 |
| migrations/versions/15eb065b21d5_add_is_public_and_view_count_fields.py | 為 `LearningKeyword` 新增公開與瀏覽欄位。 | 勿更動已套用遷移；若需更改請建立新版本。 | 確保 production 已套用。 |
| migrations/versions/27109bc650ef_add_slug_and_icon_fields_to_.py | 補分類 slug 與 icon。 | 同上。 | 同上。 |
| migrations/versions/506437f20ef8_add_seo_content_fields_to_learning_.py | 為關鍵字加入 SEO 內容欄位。 | 同上。 | 同上。 |
| migrations/versions/5292fb690208_add_user_active_flag.py | 新增使用者啟用旗標。 | 同上。 | 同上。 |
| migrations/versions/6e03639fa06a_add_icon_field_to_announcement_banner.py | 新增公告 icon 欄位。 | 同上。 | 同上。 |
| migrations/versions/7b9267aaa234_add_position_field_to_categories_and_.py | 增加排序欄位。 | 同上。 | 同上。 |
| migrations/versions/968a630e8785_remove_avatar_url_from_users.py | 移除使用者 avatar url 欄位。 | 同上。 | 同上。 |
| migrations/versions/981fd5472dd3_add_theme_settings.py | 加入主題設定資料表。 | 同上。 | 同上。 |
| migrations/versions/af1030b6210e_add_announcement_banner_table.py | 建立公告資料表。 | 同上。 | 同上。 |
| migrations/versions/be122269608d_add_keyword_goal_lists.py | 增加學習目標清單。 | 同上。 | 同上。 |
| migrations/versions/c61ec0b75ed4_add_keyword_aliases_table.py | 建立別名資料表。 | 同上。 | 同上。 |
| migrations/versions/d41921e1bb50_add_edit_logs_table.py | 建立編輯日誌資料表。 | 同上。 | 同上。 |
| migrations/versions/dc7d633ddd50_init.py | 初始 schema。 | 同上。 | 同上。 |
| migrations/versions/f5902a954927_remove_color_columns_from_announcement_.py | 調整公告顏色欄位。 | 同上。 | 同上。 |

> 備註：所有版本檔案請保持不可變；若需修改歷史結構，透過新遷移處理。

---

## 測試套件 (`tests/`)
| 路徑 | 功能定位 | 開發指引 | 維護工作 |
| --- | --- | --- | --- |
| tests/conftest.py | pytest 基礎 fixture。 | 新增 fixture 時確保作用域與資源釋放；避免全域狀態污染。 | 每次調整資料庫模型後確認 fixture 更新。 |
| tests/check_seo.py | 檢查 SEO 欄位持久化。 | 若 schema 改變需更新查驗內容。 | 可定期執行以驗證資料品質。 |
| tests/test_bopomofo.py | 注音鍵盤轉換測試。 | 新增符號映射時擴充測試。 | 當 `pypinyin` 升級後重跑以確保行為一致。 |
| tests/test_chinese_seo.py | 中文 SEO 文案輸出。 | 擴充新增案例請更新參數化資料。 | 重大改動後驗證結果呈現。 |
| tests/test_json_api_fix.py | 管理後台 JSON API 回應格式。 | 新增 API 時補測驗成功/失敗情境。 | 持續監控權限回傳碼。 |
| tests/test_keyword_linking.py | 關鍵字自動連結與別名頁面。 | 調整模板或 linking 時更新斷言。 | 每次更動 `keyword_linker` 後必跑。 |
| tests/test_main.py | 主站關鍵頁面行為。 | 擴充頁面需新增測試案例。 | 冒煙測試部署前必跑。 |
| tests/test_plain_text_seo.py | 確認 SEO HTML 為純文字輸出。 | 若輸出格式更動需同步調整。 | 維持零 XSS 風險。 |
| tests/test_pypinyin_api.py | 注音生成擴充與搜尋問句。 | 新增打字錯誤邏輯時更新。 | 當依賴缺失時確保 fallback 生效。 |
| tests/test_seo_generation.py | SEO 生成核心流程。 | 調整 `generate_seo_text` 邏輯時更新預期。 | 保持問題列表與別名驗證。 |
| tests/test_sitemap.py | Sitemap 端點與保護。 | 新增 sitemap 結構需擴充。 | 部屬前驗證 sitemap 生成功能。 |
| tests/test_updated_seo.py | 強化問句選擇行為。 | 調整問句策略同步更新測試。 | 確保注音問句依然存在。 |
| tests/test_youtube_utils.py | YouTube URL 處理函式。 | 支援新網址格式時新增測試。 | 定期覆蓋真實案例。 |

---

## 其他 Python 專案檔
| 路徑 | 功能定位 | 開發指引 | 維護工作 |
| --- | --- | --- | --- |
| pyproject.toml *(非 .py，但管理 Python 套件)* | Poetry/依賴設定。 | 更新依賴版本時同步鎖定。 | `poetry lock` 後跑測試。 |

> 若未來新增 Python 檔案，請第一時間將對應資訊補入本指南，保持文件與程式碼同步。