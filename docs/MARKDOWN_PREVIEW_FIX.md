# Markdown 渲染修正說明

## 問題描述

在前端關鍵字頁面與後台編輯器中，Markdown 表格語法無法正確渲染成 HTML `<table>` 元素，而是被包裹在 `<p>` 標籤中顯示為純文字。

**錯誤範例：**
```html
<div class="keyword-description">
  <div class="markdown-body">
    <p>| 標題1 | 標題2 | 標題3 |
    | ----- | ----- | ----- |
    | 內容1 | 內容2 | 內容3 |</p>
  </div>
</div>
```

**預期結果：**
```html
<table>
  <thead>
    <tr>
      <th>標題1</th>
      <th>標題2</th>
      <th>標題3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>內容1</td>
      <td>內容2</td>
      <td>內容3</td>
    </tr>
  </tbody>
</table>
```

## 根本原因

資料庫中儲存的 Markdown 內容可能包含 HTML 實體字元（例如 `&#124;` 代表 `|`、`&lt;` 代表 `<` 等）。當這些實體字元直接傳給 markdown2 處理器時，處理器無法識別表格語法中的管線符號 `|`，導致整段內容被當作普通段落處理。

## 解決方案

### 1. 前台頁面修正（`app/main/routes.py`）

在所有 `markdown()` 函式呼叫前，先使用 `html.unescape()` 將 HTML 實體轉回原始字元：

**修改前：**
```python
html_description = markdown(
    keyword.description_markdown,
    extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"],
    safe_mode="escape"
)
```

**修改後：**
```python
from html import unescape

html_description = markdown(
    unescape(keyword.description_markdown or ""),
    extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"],
    safe_mode="escape"
)
```

**影響範圍：**
- `keyword_detail()` 函式（主關鍵字頁面）
- `keyword_detail()` 函式（別名頁面）
- `api_search()` 函式（搜尋 API 的描述處理）

### 2. 後台編輯器預覽修正

#### 2.1 新增 Markdown 預覽 API（`app/admin/routes.py`）

建立專用的 API endpoint 來處理 Markdown 預覽，使用與前台相同的處理邏輯：

```python
@admin_bp.post("/api/markdown-preview")
@login_required
def markdown_preview():
    """API endpoint to render markdown preview with same processing as frontend."""
    from html import unescape
    from markdown2 import markdown
    
    # 取得 JSON 或 form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data or 'markdown' not in data:
        return jsonify({'error': 'No markdown content provided', 'success': False}), 400
    
    markdown_text = data.get('markdown', '')
    
    try:
        # Apply same processing as frontend: unescape then convert to HTML
        html = markdown(
            unescape(markdown_text),
            extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"],
            safe_mode="escape"
        )
        return jsonify({'html': html, 'success': True})
    except Exception as e:
        current_app.logger.error(f"Markdown preview error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500
```

#### 2.2 更新編輯器預覽函式（`app/templates/admin/keyword_form.html`）

修改 EasyMDE 編輯器的 `previewRender` 函式，透過 fetch API 呼叫後端 endpoint：

```javascript
previewRender: function(plainText, preview) {
  const previewElement = preview;
  
  if (previewElement && plainText) {
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken.value;
    }
    
    fetch('{{ url_for("admin.markdown_preview") }}', {
      method: 'POST',
      headers: headers,
      credentials: 'same-origin',
      body: JSON.stringify({ markdown: plainText })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success && data.html) {
        previewElement.innerHTML = data.html;
      }
    })
    .catch(error => {
      console.error('Markdown preview error:', error);
      // Fallback to built-in renderer
      previewElement.innerHTML = this.parent.markdown(plainText);
    });
  }
  
  // Return built-in result immediately (will be replaced by API response)
  return this.parent.markdown(plainText);
}
```

## 技術細節

### HTML Unescape 處理

`html.unescape()` 會將常見的 HTML 實體轉換回原始字元：

| HTML 實體 | 轉換後 | 用途 |
|----------|--------|------|
| `&#124;` | `|` | 表格分隔符號 |
| `&lt;` | `<` | 小於符號 |
| `&gt;` | `>` | 大於符號 |
| `&amp;` | `&` | And 符號 |
| `&quot;` | `"` | 雙引號 |

### XSS 安全性

即使使用 `unescape()`，XSS 保護仍然有效：

1. **unescape 階段**：將 HTML 實體轉回原始字元（包括 Markdown 語法需要的字元）
2. **markdown2 處理**：解析 Markdown 語法，將格式標記轉為 HTML 標籤
3. **safe_mode="escape" 保護**：markdown2 會自動跳脫使用者輸入的原始 HTML 標籤

**範例：**
```python
# 惡意輸入
malicious = '<script>alert("XSS")</script>\n\n**粗體**'

# 處理流程
unescaped = unescape(malicious)  # '<script>alert("XSS")</script>\n\n**粗體**'
html = markdown(unescaped, safe_mode="escape")
# 結果：'&lt;script&gt;alert("XSS")&lt;/script&gt;\n\n<strong>粗體</strong>'
# ✅ Script 被跳脫，但 Markdown 格式正常
```

## 驗證步驟

### 1. 前台頁面驗證

1. 在資料庫或管理介面新增/編輯關鍵字，描述內容包含表格：
   ```markdown
   | 標題1 | 標題2 | 標題3 |
   | ----- | ----- | ----- |
   | 內容1 | 內容2 | 內容3 |
   ```

2. 在前台關鍵字頁面查看，應該顯示為完整的表格（非純文字）

3. 使用瀏覽器開發者工具檢查 DOM，應包含 `<table>`, `<thead>`, `<tbody>` 等元素

### 2. 後台編輯器驗證（EasyMDE - keyword_form.html）

1. 登入管理介面，進入關鍵字編輯頁面（從關鍵字列表點擊「編輯」）

2. 在 EasyMDE Markdown 編輯器中輸入表格語法

3. 點擊工具列的「並排預覽」或「預覽」按鈕

4. 預覽區域應正確顯示表格（非純文字）

5. 檢查瀏覽器 Console，確認 API 請求成功：
   ```
   POST /admin/api/markdown-preview
   Status: 200 OK
   Response: {"success": true, "html": "<table>..."}
   ```

### 3. 後台內容編輯器驗證（marked.js - keyword_editor.html）

1. 登入管理介面，從內容管理器進入編輯模式

2. 在 Markdown 編輯區輸入表格語法

3. 點擊「並排預覽」按鈕

4. 預覽區域應正確顯示表格，且不應有 Console 錯誤

5. 檢查瀏覽器 Console，確認沒有：
   ```
   ❌ TypeError: Cannot read properties of undefined (reading 'header')
   ```

6. 應該看到：
   ```
   ✅ 表格正確渲染，無錯誤訊息
   ```

### 4. 自動化測試

執行新增的測試檔案：
```bash
pytest tests/test_markdown_preview_api.py -v
```

測試涵蓋：
- ✅ 表格渲染
- ✅ 程式碼區塊渲染
- ✅ HTML 實體反轉義
- ✅ 缺少內容的錯誤處理
- ✅ XSS 防護

## 支援的 Markdown 語法

修正後，以下所有語法都能正確渲染：

### 表格
```markdown
| 左對齊 | 置中 | 右對齊 |
| :--- | :---: | ---: |
| 內容 | 內容 | 內容 |
```

### 程式碼區塊
````markdown
```python
def hello():
    print("Hello")
```
````

### 任務清單
```markdown
- [x] 已完成項目
- [ ] 未完成項目
```

### 刪除線
```markdown
~~刪除的文字~~
```

### 其他標準語法
- 標題（# ## ###）
- 粗體、斜體（**粗體** *斜體*）
- 清單（有序、無序）
- 連結、圖片
- 引用區塊

## 效能考量

### 前台
- `unescape()` 是輕量級操作，對效能影響微乎其微
- 已有的 markdown 快取機制（如果有）仍然有效

### 後台編輯器
- 預覽請求採用非同步 fetch，不會阻塞 UI
- 編輯器先顯示內建渲染結果（即時），再用後端結果覆蓋（確保準確）
- 如果 API 失敗，自動回退到內建渲染器

### 2.3 修正 keyword-editor.js 的表格渲染錯誤

**問題：** `keyword-editor.js` 中使用 marked.js 的自訂 renderer 時，`tablerow` 和 `tablecell` 函式嘗試訪問 `flags.header`，但在某些情況下 `flags` 可能是 `undefined`，導致錯誤：

```
TypeError: Cannot read properties of undefined (reading 'header')
```

**原因：** marked.js 在不同版本中 API 有變化，`flags` 參數的結構或傳遞方式可能不同。

**解決方案：** 在訪問 `flags` 屬性前加入防禦性檢查：

```javascript
// 修改前
renderer.tablerow = function(content, flags) {
  const style = flags.header ? 'background: #667eea; ...' : 'background: #f8f9fa;';
  return `<tr style="${style}">${content}</tr>\n`;
};

// 修改後
renderer.tablerow = function(content, flags) {
  // flags 可能是 undefined 或缺少 header 屬性
  const isHeader = flags && flags.header === true;
  const style = isHeader ? 'background: #667eea; ...' : 'background: #f8f9fa;';
  return `<tr style="${style}">${content}</tr>\n`;
};

renderer.tablecell = function(content, flags) {
  // 安全地訪問 flags 屬性
  const align = (flags && flags.align) ? `text-align: ${flags.align};` : 'text-align: left;';
  const isHeader = flags && flags.header === true;
  // ... rest of the code
};
```

## 相關檔案

### 修改的檔案
- `app/main/routes.py` - 前台 Markdown 渲染邏輯
- `app/admin/routes.py` - 新增預覽 API endpoint
- `app/templates/admin/keyword_form.html` - EasyMDE 編輯器預覽函式
- `app/static/js/keyword-editor.js` - marked.js renderer 防禦性檢查

### 新增的檔案
- `tests/test_markdown_preview_api.py` - API 測試
- `docs/MARKDOWN_PREVIEW_FIX.md` - 本文件

## 後續改進建議

1. **快取優化**：考慮在 API endpoint 加入快取機制（例如 Redis），減少重複渲染相同內容

2. **關鍵字自動連結**：目前在 HTML 層級處理，可考慮改為在 Markdown 階段處理，避免 regex 處理 HTML 的複雜度

3. **預覽延遲處理**：編輯器預覽可加入 debounce，避免每次按鍵都觸發 API 請求

4. **離線模式**：可考慮在前端也實作 unescape + markdown2 邏輯（使用 marked.js），在網路不穩定時作為備援

## 參考資料

- [markdown2 官方文檔](https://github.com/trentm/python-markdown2)
- [EasyMDE 編輯器](https://github.com/Ionaru/easy-markdown-editor)
- [HTML Entities Reference](https://developer.mozilla.org/en-US/docs/Glossary/Entity)
