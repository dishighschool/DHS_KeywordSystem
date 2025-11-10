# 關鍵字編輯器換行與刪除線渲染修復報告

## 問題描述

用戶回報兩個問題：
1. ❌ 刪除線無法正確渲染
2. ❌ 編輯時的換行在保存後可能丟失，導致版面跑版

## 已完成的修復

### 1. 刪除線渲染修復 ✅

**問題根源**：
- Markdown2 使用的 extra 名稱是 `strike` 而不是 `strikethrough`
- CSS 樣式不夠明確

**修復內容**：

#### 後端 (app/main/routes.py)
```python
# 修改前
extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"]

# 修改後
extras=["fenced-code-blocks", "tables", "strike", "task_lists", "break-on-newline"]
```

在以下位置進行了修改：
- Line 267-270: keyword_detail 路由
- Line 458-461: search_data 路由 (keywords)
- Line 500-503: search_data 路由 (aliases)

#### CSS (app/static/css/keyword-detail.css)
```css
/* 修改前 */
.markdown-body del {
  text-decoration: line-through;
  color: #999;
  opacity: 0.7;
}

/* 修改後 - 支持多種刪除線標籤 */
.markdown-body del,
.markdown-body s,
.markdown-body strike {
  text-decoration: line-through;
  text-decoration-thickness: 2px;
  text-decoration-color: #dc3545;
  color: #999;
  opacity: 0.7;
}
```

### 2. 換行保留修復 ✅

**問題根源**：
- Markdown2 默認不會將單個換行符轉換為 `<br>` 標籤
- 需要啟用 `break-on-newline` extra

**修復內容**：

#### 後端渲染
在所有 markdown 渲染處添加 `break-on-newline` extra：
```python
html = markdown(
    raw_markdown,
    extras=["fenced-code-blocks", "tables", "strike", "task_lists", "break-on-newline"],
    safe_mode="escape",
)
```

#### CSS (app/static/css/keyword-detail.css)
```css
/* 段落樣式 - 保留換行 */
.markdown-body p {
  margin: 1rem 0;
  line-height: 1.8;
  color: #444;
  white-space: pre-wrap;  /* 保留換行符 */
  word-wrap: break-word;  /* 避免超長單字破版 */
}

/* 確保單行換行（<br>）正確顯示 */
.markdown-body br {
  display: block;
  content: "";
  margin-top: 0.5em;
}
```

### 3. 測試更新 ✅

更新了 `tests/test_markdown_rendering.py`：
- 修正所有測試使用 `strike` extra
- 修正刪除線測試斷言（使用 `<s>` 標籤而非 `<del>`）
- 修正 XSS 測試的預期行為
- 新增測試：
  - `test_strikethrough()` - 測試刪除線渲染
  - `test_break_on_newline()` - 測試單行換行
  - `test_complex_strike_with_chinese()` - 測試中文刪除線

**測試結果**：✅ 16/16 通過

## 可能仍需注意的問題

### 1. 前端編輯器 (keyword_editor.html)

**當前狀態**：需要檢查
- 使用了 `marked.js` 作為預覽渲染器
- `marked` 的配置與後端 `markdown2` 可能不一致

**潛在問題**：
```javascript
// keyword-editor.js Line 234
marked.setOptions({
  breaks: true,  // GFM 換行模式
  gfm: true
});
```

這可能導致：
- 預覽時看到的換行效果與實際渲染不同
- 用戶認為換行會保留，但實際上後端處理可能不同

**建議修復**：
確保前端預覽使用與後端一致的 API：

```html
<!-- keyword_form.html 已經在使用後端 API 進行預覽 -->
<script>
previewRender: function(plainText, preview) {
  fetch('{{ url_for("admin.markdown_preview") }}', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken.value
    },
    body: JSON.stringify({ markdown: plainText })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success && data.html) {
      previewElement.innerHTML = data.html;
    }
  });
}
</script>
```

### 2. 數據保存流程

**當前狀態**：已檢查，看起來正常
- `app/admin/routes.py` Line 376: 使用 `form.description_markdown.data`（不會 strip）
- `app/admin/routes.py` Line 526: 同樣使用 `form.description_markdown.data`

**快速創建路由**：
- Line 440: 使用 `.strip()` **可能會移除前後空白**

```python
description_markdown = request.form.get('description_markdown', '').strip()
```

**建議**：移除 `.strip()` 或只移除前後的空行而非所有空白：
```python
# 選項 1: 不 strip
description_markdown = request.form.get('description_markdown', '')

# 選項 2: 只移除前後完全空白的行
description_markdown = request.form.get('description_markdown', '')
if description_markdown:
    lines = description_markdown.splitlines()
    # 移除開頭的空行
    while lines and not lines[0].strip():
        lines.pop(0)
    # 移除結尾的空行
    while lines and not lines[-1].strip():
        lines.pop()
    description_markdown = '\n'.join(lines)
```

### 3. HTML Textarea 渲染

**當前狀態**：需要檢查
- `keyword_form.html` Line 27: 使用 `{{ form.description_markdown.data or '' }}`

**潛在問題**：
Jinja2 模板中的換行符可能會被瀏覽器解釋為 HTML 空白。

**建議**：確保 textarea 內容正確渲染：
```html
<!-- 確保沒有額外的空白 -->
<textarea>{{ form.description_markdown.data or '' }}</textarea>

<!-- 而不是 -->
<textarea>
  {{ form.description_markdown.data or '' }}
</textarea>
```

## 測試建議

### 手動測試清單

1. **刪除線測試** ✅
   ```markdown
   這是~~刪除的文字~~正常文字
   ~~整行刪除~~
   **粗體**~~刪除~~*斜體*
   ```

2. **換行測試** ⚠️ 需要測試
   ```markdown
   第一行
   第二行
   第三行

   上面有空行

   - 列表1
   - 列表2
   ```

3. **混合測試** ⚠️ 需要測試
   ```markdown
   # 標題

   這是第一段
   包含換行

   這是~~刪除的~~第二段
   也包含換行

   **重要**：測試~~舊方法~~新方法
   ```

### 自動化測試

已創建 `tests/test_newline_preservation.py`：
- `test_markdown_with_newlines_preserved` - 測試換行保留
- `test_strikethrough_in_markdown` - 測試刪除線保存

**執行測試**：
```bash
pytest tests/test_newline_preservation.py -v
pytest tests/test_markdown_rendering.py -v
```

## 總結

### 已修復 ✅
1. 刪除線渲染（使用 `strike` extra）
2. CSS 刪除線樣式增強
3. 添加 `break-on-newline` extra
4. CSS 段落保留換行樣式
5. 所有測試更新並通過

### 待驗證 ⚠️
1. 前端編輯器預覽與後端渲染的一致性
2. 快速創建路由的 `.strip()` 行為
3. 實際編輯器中的換行保留測試

### 建議後續行動
1. 執行手動測試驗證換行保留
2. 考慮修改 `quick_create_keyword` 的 `.strip()` 邏輯
3. 確保 `keyword_editor.html` 使用後端 preview API
4. 添加端到端測試驗證完整流程

## 相關檔案

- ✅ `app/main/routes.py` - 後端渲染邏輯
- ✅ `app/static/css/keyword-detail.css` - 前端樣式
- ✅ `tests/test_markdown_rendering.py` - 渲染測試
- ✅ `tests/test_newline_preservation.py` - 換行測試
- ⚠️ `app/admin/routes.py` - 表單處理（需要檢查 strip）
- ⚠️ `app/templates/admin/keyword_editor.html` - 編輯器模板
- ⚠️ `app/static/js/keyword-editor.js` - 編輯器 JS

## 更新日期

2025-11-10
