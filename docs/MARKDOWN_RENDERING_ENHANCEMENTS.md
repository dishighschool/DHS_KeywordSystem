# Markdown 渲染增強文檔

## 概述

本文檔記錄了對關鍵字編輯器和關鍵字詳情頁面 Markdown 渲染的增強改進，包括 XSS 安全防護和視覺效果優化。

## 更改內容

### 1. 編輯器預覽增強 (`app/static/js/keyword-editor.js`)

#### Markdown 渲染器自訂配置
- **啟用 GFM (GitHub Flavored Markdown)**：支持表格、刪除線、自動連結等高級功能
- **自訂渲染器**：為所有 Markdown 元素提供自訂的 HTML 渲染邏輯

#### 支持的 Markdown 功能

##### 1. 標題 (Headings)
- 支持 H1-H6 級別的標題
- H1 和 H2 帶有底部邊框，視覺層次清晰
- 自動生成 ID，方便錨點連結

**示例：**
```markdown
# 一級標題
## 二級標題
### 三級標題
```

##### 2. 表格 (Tables)
- 完整支持 GitHub Flavored Markdown 表格語法
- 自動應用優雅的樣式：
  - 漸變色表頭 (從藍色到紫色)
  - 行懸停效果
  - 響應式設計

**示例：**
```markdown
| 欄位1 | 欄位2 | 欄位3 |
|------|------|------|
| 內容1| 內容2| 內容3|
| 內容4| 內容5| 內容6|
```

##### 3. 代碼塊 (Code Blocks)
- 支持多行代碼塊，可指定語言
- 左側邊框強調，漸變背景
- 行內代碼 (inline code) 使用紅色著色

**示例：**
```markdown
    ```python
    def hello():
        print("Hello, World!")
    ```
    
    或行內代碼：`const x = 10;`
```

##### 4. 列表 (Lists)
- 無序列表 (Unordered Lists)：圓點、圓形、方形等多層級
- 有序列表 (Ordered Lists)：數字編號
- 自動化縮進和間距

**示例：**
```markdown
- 無序項目1
  - 子項目1.1
    - 子項目1.1.1
  - 子項目1.2
- 無序項目2

1. 有序項目1
2. 有序項目2
3. 有序項目3
```

##### 5. 引用塊 (Blockquotes)
- 左側邊框標記
- 淡灰色背景，斜體文字
- 適合強調重要訊息或引用

**示例：**
```markdown
> 這是一個引用塊
> 可以包含多行內容
```

##### 6. 強調效果 (Emphasis)
- **粗體** (Bold)：使用 `**text**` 或 `__text__`
- *斜體* (Italic)：使用 `*text*` 或 `_text_`
- ~~刪除線~~ (Strikethrough)：使用 `~~text~~`

**示例：**
```markdown
**粗體文字**
*斜體文字*
***粗斜體***
~~刪除線~~
```

##### 7. 連結 (Links)
- 自動設置 `target="_blank"` 和 `rel="noopener noreferrer"`
- XSS 防護：驗證 URL，移除 `javascript:` 協議
- 懸停效果：背景著色和顏色變化

**示例：**
```markdown
[連結文字](https://example.com)
[帶標題的連結](https://example.com "標題")
```

##### 8. 圖片 (Images)
- 自動縮放以適應容器寬度
- 添加陰影效果，增強視覺層次
- 支持標題說明文字
- 響應式設計

**示例：**
```markdown
![替代文字](https://example.com/image.jpg)
![帶標題的圖片](https://example.com/image.jpg "圖片標題")
```

##### 9. 水平線 (Horizontal Lines)
- 漸變效果的分隔線
- 自動間距

**示例：**
```markdown
---
```

### 2. XSS 安全防護

#### 防護機制
1. **HTML 標籤轉義**：所有直接的 HTML 標籤都被顯示為純文本
   - 在 `<pre><code>` 區塊中顯示
   - 使用 `escapeHtml()` 函數進行轉義

2. **事件監聽移除**：清除所有 `on*` 事件屬性
   - `onclick`, `onmouseover`, `onerror` 等

3. **危險 URL 過濾**：
   - 驗證連結 URL 的有效性
   - 移除 `javascript:` 協議連結
   - 驗證圖片 URL 的有效性

4. **DOM 清理**：遞歸清理 DOM 節點中的危險屬性

#### 範例：防護效果
```markdown
<img src=x onerror="alert('XSS')">
```
上述代碼會被安全地顯示為純文本，而不是執行 JavaScript。

### 3. 樣式優化

#### 編輯器預覽樣式 (`app/static/css/keyword-editor.css`)
- 預覽區域配置了完整的 Markdown 樣式
- 滾動條美化：藍紫色主題
- 響應式設計支持

#### 詳情頁面樣式 (`app/static/css/keyword-detail.css`)
- 與編輯器預覽保持一致的樣式
- 適配主題色 (藍紫色漸變)
- 優化移動設備顯示
- 表格、代碼塊等元素的視覺層次清晰

## 技術實現細節

### marked.js 配置
```javascript
marked.setOptions({
  breaks: true,        // 啟用換行支持
  gfm: true,          // GitHub Flavored Markdown
  headerIds: true,    // 自動生成標題 ID
  mangle: false,      // 不轉義郵件地址
  pedantic: false     // 不遵循 CommonMark 規範
});
```

### Renderer 覆蓋清單
- `heading()` - 標題
- `paragraph()` - 段落
- `codespan()` - 行內代碼
- `code()` - 代碼塊
- `list()` / `listitem()` - 列表
- `blockquote()` - 引用塊
- `hr()` - 水平線
- `table()` / `tablerow()` / `tablecell()` - 表格
- `strong()` - 粗體
- `em()` - 斜體
- `del()` - 刪除線
- `html()` - HTML 標籤 (安全轉義)
- `image()` - 圖片
- `link()` - 連結

## 測試建議

1. **表格渲染測試**
   - 創建包含複雜表格的關鍵字
   - 驗證表格是否正確顯示，包括表頭樣式和行懸停效果

2. **代碼塊測試**
   - 測試多行代碼塊，驗證格式化
   - 測試行內代碼著色

3. **XSS 防護測試**
   - 嘗試在 Markdown 中插入惡意 HTML
   - 驗證這些內容被安全地顯示為文本

4. **連結和圖片測試**
   - 驗證外部連結能正確打開
   - 驗證圖片正確縮放並添加陰影效果

5. **列表和引用測試**
   - 測試多層級嵌套列表
   - 測試複雜的引用塊內容

6. **響應式測試**
   - 在不同設備寬度下測試 Markdown 渲染
   - 驗證表格和圖片在小屏幕上的顯示

## 使用者指南

### 在編輯器中編寫 Markdown

1. **基本格式**：使用頂部工具欄或直接輸入 Markdown 語法
2. **預覽模式**：切換到「預覽」或「分割」模式查看效果
3. **表格建立**：點擊表格圖標自動插入表格框架
4. **支持的語言高亮**：雖然預覽不顯示語法高亮，但代碼塊結構被保留

### 在前台查看內容

- 所有 Markdown 元素都被渲染為美觀的 HTML
- 表格具有交互式懸停效果
- 連結自動在新選項卡中打開
- 所有內容都經過 XSS 防護檢查

## 性能考慮

- Markdown 解析在用戶輸入時進行，使用 300ms 的防抖延遲
- 預覽只在分割或預覽模式下更新
- DOM 節點清理使用遞歸方式，對於大型文檔仍然高效

## 瀏覽器兼容性

- 支援所有現代瀏覽器 (Chrome, Firefox, Safari, Edge)
- marked.js 庫提供廣泛的兼容性
- CSS 使用標準屬性，兼容所有現代瀏覽器

## 未來改進方向

1. **語法高亮**：集成 Prism.js 或 Highlight.js 用於代碼塊語法高亮
2. **Emoji 支持**：添加 Emoji 表情支持
3. **數學公式**：集成 MathJax 或 KaTeX 用於渲染 LaTeX 公式
4. **腳注支持**：實現 Markdown 腳注功能
5. **目錄生成**：自動生成基於標題的目錄

## 相關文件

- `app/static/js/keyword-editor.js` - 編輯器邏輯和 Markdown 渲染
- `app/static/css/keyword-editor.css` - 編輯器樣式
- `app/static/css/keyword-detail.css` - 詳情頁面樣式
- `app/templates/admin/keyword_editor.html` - 編輯器模板

