# 初始狀態下隱藏必填欄位指示器

## 需求

在新建關鍵字時，進入編輯頁面不應立即顯示紅色「此分頁含必填欄位」徽章和警告提示。應該只在提交失敗時才顯示這些指示器。

## 問題

原先的實現在頁面載入時就呼叫 `checkRequiredFields()`，導致即使沒有提交，側邊欄也會立即顯示紅色徽章。

## 解決方案

### 修改 `checkRequiredFields()` 函式

引入 `isSubmitted` 狀態檢查，控制何時顯示指示器。

**修改前：**
```javascript
function checkRequiredFields() {
  const missingFields = {};
  // ... 檢查邏輯 ...
  
  // ❌ 無條件顯示警告和徽章
  updateRequiredFieldsAlert(missingFields);
  updateNavigationIndicators(missingFields);
}
```

**修改後：**
```javascript
function checkRequiredFields() {
  const missingFields = {};
  const form = document.getElementById('keywordForm');
  const isSubmitted = form?.classList.contains('has-submitted');
  
  // ... 檢查欄位邏輯 ...
  
  // ✅ 只在提交後顯示警告
  if (isSubmitted) {
    updateRequiredFieldsAlert(missingFields);
  } else {
    const alertBox = document.getElementById('required-fields-alert');
    if (alertBox) {
      alertBox.style.display = 'none';
    }
  }
  
  // ✅ 只在提交後顯示徽章
  if (isSubmitted) {
    updateNavigationIndicators(missingFields);
  } else {
    // 未提交時隱藏所有徽章
    const navItems = document.querySelectorAll('.editor-nav-item');
    navItems.forEach(item => {
      const badge = item.querySelector('.nav-required-badge');
      if (badge) {
        badge.style.display = 'none';
      }
      item.classList.remove('has-required-missing');
    });
  }
}
```

## 行為流程

### 新建關鍵字

```
進入編輯頁面
├─ 欄位：無色（無驗證指示）
├─ 導航徽章：隱藏（無 has-submitted）
└─ 警告框：隱藏

✨ 用戶看到乾淨的編輯介面，沒有紅色標記
```

### 提交時

```
用戶點擊「儲存」
├─ form.classList.add('has-submitted')
├─ checkRequiredFields() 重新執行
└─ isSubmitted === true

顯示驗證指示
├─ 缺失欄位 → 紅色邊框
├─ 側邊欄 → 顯示紅色「此分頁含必填欄位」徽章
└─ 頁面頂部 → 顯示「必填欄位提示」警告框

⚠️ 用戶看到清晰的錯誤指示
```

### 填寫後

```
用戶開始填寫缺失欄位
├─ form.classList.remove('has-submitted')
├─ checkRequiredFields() 重新執行
└─ isSubmitted === false

隱藏驗證指示
├─ 已填欄位 → 移除紅色，顯示無色
├─ 側邊欄 → 隱藏該分頁的紅色徽章
└─ 警告框 → 隱藏（因為 isSubmitted === false）

✨ 返回乾淨的無色狀態
```

## 修改的檔案

- **app/static/js/keyword-editor.js**
  - Line 104-152: 完整重寫 `checkRequiredFields()` 函式
  - 新增 `isSubmitted` 狀態檢查邏輯

## 測試清單

- [ ] 新建關鍵字
  - [ ] 進入編輯頁面，側邊欄徽章應**隱藏**
  - [ ] 頁面頂部警告框應**隱藏**
  - [ ] 所有欄位應**無色**
- [ ] 直接點擊「儲存」（不填寫任何內容）
  - [ ] 側邊欄「基本資訊」和「內容描述」應顯示紅色徽章
  - [ ] 頁面頂部應顯示「必填欄位提示」
  - [ ] 必填欄位應顯示紅色邊框
- [ ] 開始填寫欄位
  - [ ] 填寫後該欄位應回到無色
  - [ ] 如果所有該分頁的必填欄位都已填，紅色徽章應隱藏
  - [ ] 如果所有必填欄位都已填，警告框應隱藏
- [ ] 編輯已存在的關鍵字
  - [ ] 如果所有必填欄位都已填，進入時應無任何紅色標記
  - [ ] 如果有缺失欄位... **等等**，這種情況不應出現（編輯時總是有完整的內容）

## 相關邏輯總結

### 三個驗證狀態

| 狀態 | `has-submitted` | 顯示指示器 | 使用者體驗 |
|------|-----------------|----------|----------|
| 初始 | ❌ 否 | ❌ 否 | 乾淨的無色介面 |
| 提交驗證失敗 | ✅ 是 | ✅ 是 | 清晰的紅色錯誤提示 |
| 填寫中 | ❌ 否（移除） | ❌ 否 | 乾淨的無色介面 |

### 兩個檢查點

1. **提交時**：`saveKeyword()` 添加 `has-submitted`
2. **編輯時**：表單 `change`/`input` 事件移除 `has-submitted`

### 三層驗證顯示

1. **欄位邊框**：只有 `has-submitted && 欄位無效` 時才顯示紅色
2. **側邊欄徽章**：只有 `has-submitted && 該分頁有缺失` 時才顯示
3. **警告框**：只有 `has-submitted && 有缺失欄位` 時才顯示

## 對比總結

### 修改前 ❌
- 進入編輯頁面 → 立即顯示紅色徽章
- 用戶困惑：「我還沒開始編輯，為什麼就有紅色提示？」

### 修改後 ✅
- 進入編輯頁面 → 無色介面
- 提交失敗 → 顯示紅色錯誤
- 開始填寫 → 紅色自動消失
- 用戶友善：「只在需要時提示，不會搶先打擾」
