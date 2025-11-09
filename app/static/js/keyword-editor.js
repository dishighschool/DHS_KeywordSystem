let formChanged = false;

// 定義必填欄位及其驗證規則
const REQUIRED_FIELDS = {
  title: {
    fieldId: 'title',
    name: '標題',
    section: 'basic',
    validate: function(value) {
      return value && value.trim().length > 0;
    },
    errorMessage: '標題不能為空'
  },
  category_id: {
    fieldId: 'category_id',
    name: '分類',
    section: 'basic',
    validate: function(value) {
      return value && value !== '';
    },
    errorMessage: '請選擇分類'
  },
  description_markdown: {
    fieldId: 'description_markdown',
    name: '內容描述',
    section: 'content',
    validate: function(value) {
      return value && value.trim().length > 0;
    },
    errorMessage: '內容描述不能為空'
  }
};

function initKeywordEditor() {
  const navItems = document.querySelectorAll('.editor-nav-item');
  const sections = document.querySelectorAll('.editor-section');

  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetSection = this.dataset.section;
      
      navItems.forEach(nav => nav.classList.remove('active'));
      this.classList.add('active');
      
      sections.forEach(section => {
        if (section.id === `section-${targetSection}`) {
          section.classList.add('active');
          document.querySelector('.editor-content').scrollTop = 0;
        } else {
          section.classList.remove('active');
        }
      });
      
      window.location.hash = targetSection;
    });
  });

  const hash = window.location.hash.substring(1);
  if (hash) {
    const targetNav = document.querySelector(`[data-section="${hash}"]`);
    if (targetNav) {
      targetNav.click();
    }
  }

  initMarkdownEditor();
  checkRequiredFields();
  setupRequiredFieldsMonitoring();

  const form = document.getElementById('keywordForm');
  if (form) {
    form.addEventListener('change', function() {
      formChanged = true;
      // 當用戶修改表單後，移除已提交標籤，返回無色狀態
      form.classList.remove('has-submitted');
      checkRequiredFields();
    });
    
    form.addEventListener('input', function() {
      formChanged = true;
      // 當用戶修改表單後，移除已提交標籤，返回無色狀態
      form.classList.remove('has-submitted');
      checkRequiredFields();
    });

    window.addEventListener('beforeunload', function(e) {
      if (formChanged) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    });
  }
}

/**
 * 驗證必填欄位並更新UI提示
 */
function checkRequiredFields() {
  const missingFields = {};
  const form = document.getElementById('keywordForm');
  const isSubmitted = form?.classList.contains('has-submitted');
  
  // 逐個檢查必填欄位
  for (const [key, config] of Object.entries(REQUIRED_FIELDS)) {
    const element = document.getElementById(config.fieldId);
    if (!element) continue;
    
    const value = element.value || '';
    const isValid = config.validate(value);
    
    if (!isValid) {
      missingFields[key] = config;
    }
    
    // 更新欄位的視覺反饋
    // 只在提交後（has-submitted 標籤存在時）才顯示紅色
    // 正常狀態下保持無色，不顯示綠色勾勾
    if (isValid) {
      element.classList.remove('is-invalid');
      // 移除 is-valid 類別，不顯示綠色勾勾
      element.classList.remove('is-valid');
    } else {
      // 只有在已提交時才顯示紅色錯誤
      if (isSubmitted) {
        element.classList.add('is-invalid');
      } else {
        element.classList.remove('is-invalid');
      }
      element.classList.remove('is-valid');
    }
  }
  
  // 更新必填欄位提示警告 - 只在提交後才顯示
  if (isSubmitted) {
    updateRequiredFieldsAlert(missingFields);
  } else {
    // 未提交時隱藏警告
    const alertBox = document.getElementById('required-fields-alert');
    if (alertBox) {
      alertBox.style.display = 'none';
    }
  }
  
  // 更新側邊欄導航指示器 - 只在提交後才顯示
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

/**
 * 更新必填欄位警告提示
 */
function updateRequiredFieldsAlert(missingFields) {
  const alertBox = document.getElementById('required-fields-alert');
  const fieldsList = document.getElementById('required-fields-list');
  
  if (!alertBox || !fieldsList) return;
  
  if (Object.keys(missingFields).length === 0) {
    alertBox.style.display = 'none';
  } else {
    alertBox.style.display = 'block';
    
    let html = '<ul class="mb-0" style="padding-left: 1.5rem;">';
    for (const [key, config] of Object.entries(missingFields)) {
      const sectionName = getSectionDisplayName(config.section);
      html += `<li class="mb-1"><strong>${config.name}</strong> (在「${sectionName}」分頁) - ${config.errorMessage}</li>`;
    }
    html += '</ul>';
    
    fieldsList.innerHTML = html;
  }
}

/**
 * 更新導航側邊欄中必填欄位的指示器
 */
function updateNavigationIndicators(missingFields) {
  // 找出哪些分頁有未填的必填欄位
  const sectionsWithMissing = new Set();
  
  for (const [key, config] of Object.entries(missingFields)) {
    sectionsWithMissing.add(config.section);
  }
  
  // 更新所有導航項目
  const navItems = document.querySelectorAll('.editor-nav-item');
  navItems.forEach(item => {
    const section = item.dataset.section;
    const badge = item.querySelector('.nav-required-badge');
    
    if (badge) {
      if (sectionsWithMissing.has(section)) {
        badge.style.display = 'inline-block';
        item.classList.add('has-required-missing');
      } else {
        badge.style.display = 'none';
        item.classList.remove('has-required-missing');
      }
    }
  });
}

/**
 * 獲取分頁的顯示名稱
 */
function getSectionDisplayName(sectionKey) {
  const names = {
    'basic': '基本資訊',
    'content': '內容描述',
    'videos': '影片資源',
    'aliases': '別名標籤',
    'seo': 'SEO 優化',
    'visibility': '顯示設定'
  };
  return names[sectionKey] || sectionKey;
}

/**
 * 設定必填欄位變更監聽
 */
function setupRequiredFieldsMonitoring() {
  for (const [key, config] of Object.entries(REQUIRED_FIELDS)) {
    const element = document.getElementById(config.fieldId);
    if (!element) continue;
    
    element.addEventListener('input', function() {
      checkRequiredFields();
    });
    
    element.addEventListener('change', function() {
      checkRequiredFields();
    });
    
    // 對 Markdown 編輯器添加特殊監聽
    if (config.fieldId === 'description_markdown') {
      element.addEventListener('blur', function() {
        checkRequiredFields();
      });
    }
  }
}

/**
 * 驗證必填欄位並導航到第一個缺失的欄位
 * @returns {boolean} 所有必填欄位都已填寫返回 true,否則返回 false
 */
function validateAndNavigateToMissing() {
  const missingFields = {};
  
  // 逐個檢查必填欄位
  for (const [key, config] of Object.entries(REQUIRED_FIELDS)) {
    const element = document.getElementById(config.fieldId);
    if (!element) continue;
    
    const value = element.value || '';
    const isValid = config.validate(value);
    
    if (!isValid) {
      missingFields[key] = config;
    }
  }
  
  // 如果沒有缺失欄位,返回 true
  if (Object.keys(missingFields).length === 0) {
    return true;
  }
  
  // 找到第一個缺失的欄位,導航到該分頁
  const firstMissing = Object.values(missingFields)[0];
  if (firstMissing) {
    navigateToSection(firstMissing.section);
    
    // 高亮該欄位
    setTimeout(() => {
      const element = document.getElementById(firstMissing.fieldId);
      if (element) {
        element.focus();
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // 添加閃爍效果
        element.classList.add('highlight-field');
        setTimeout(() => {
          element.classList.remove('highlight-field');
        }, 2000);
      }
    }, 300);
    
    showNotification(`請先填寫「${firstMissing.name}」(${firstMissing.errorMessage})`, 'warning');
    
    return false;
  }
  
  return true;
}

/**
 * 導航到指定的分頁
 */
function navigateToSection(sectionName) {
  const navItem = document.querySelector(`[data-section="${sectionName}"]`);
  if (navItem) {
    navItem.click();
  }
}

function initMarkdownEditor() {
  const textarea = document.getElementById('description_markdown');
  const container = document.getElementById('markdown-container');
  const previewContent = document.querySelector('.preview-content');
  
  if (!textarea || !container || !previewContent) return;

  if (typeof marked !== 'undefined') {
    // 設置 marked 選項並啟用安全模式
    marked.setOptions({
      breaks: true,
      gfm: true,  // 啟用 GitHub Flavored Markdown (支持表格、刪除線等)
      headerIds: true,
      mangle: false,
      pedantic: false
    });
    
    // 創建一個自訂的 renderer 來防止 XSS 並增強渲染效果
    const renderer = new marked.Renderer();
    
    // 覆蓋標題渲染,添加樣式
    renderer.heading = function(text, level) {
      const id = text.toLowerCase().replace(/\s+/g, '-');
      const className = `markdown-h${level}`;
      return `<h${level} id="${id}" class="${className}" style="margin-top: 1.5rem; margin-bottom: 0.5rem; font-weight: 600; border-bottom: ${level === 1 ? '2px solid #e9ecef;' : 'none'} padding-bottom: ${level === 1 ? '0.5rem;' : '0;'}">${text}</h${level}>\n`;
    };
    
    // 覆蓋段落渲染
    renderer.paragraph = function(text) {
      return `<p style="margin-bottom: 1rem; line-height: 1.6; color: #333;">${text}</p>\n`;
    };
    
    // 覆蓋代碼塊渲染,添加語言高亮提示
    renderer.codespan = function(code) {
      return `<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; color: #c7254e; font-family: 'Courier New', monospace; font-size: 0.9em;">${escapeHtml(code)}</code>`;
    };
    
    // 覆蓋代碼塊 (多行)
    renderer.code = function(code, language) {
      const highlighted = language ? `<pre><code class="language-${escapeHtml(language)}" style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #667eea; overflow-x: auto;">${escapeHtml(code)}</code></pre>` 
                                    : `<pre><code style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #667eea; overflow-x: auto;">${escapeHtml(code)}</code></pre>`;
      return highlighted + '\n';
    };
    
    // 覆蓋無序列表
    renderer.list = function(body, ordered) {
      const type = ordered ? 'ol' : 'ul';
      const style = ordered ? 'list-style-type: decimal; margin-left: 2rem;' : 'list-style-type: disc; margin-left: 2rem;';
      return `<${type} style="margin-bottom: 1rem; line-height: 1.8; ${style}">${body}</${type}>\n`;
    };
    
    // 覆蓋列表項
    renderer.listitem = function(text) {
      return `<li style="margin-bottom: 0.5rem;">${text}</li>\n`;
    };
    
    // 覆蓋區塊引用
    renderer.blockquote = function(quote) {
      return `<blockquote style="border-left: 4px solid #667eea; padding-left: 1rem; margin-left: 0; margin-bottom: 1rem; color: #666; font-style: italic;">${quote}</blockquote>\n`;
    };
    
    // 覆蓋水平線
    renderer.hr = function() {
      return `<hr style="border: none; height: 2px; background: linear-gradient(to right, transparent, #e9ecef, transparent); margin: 2rem 0;">`;
    };
    
    // 覆蓋表格 - 添加 Bootstrap 樣式
    renderer.table = function(header, body) {
      return `<div style="overflow-x: auto; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 5px; overflow: hidden;">
          <thead>
            ${header}
          </thead>
          <tbody>
            ${body}
          </tbody>
        </table>
      </div>\n`;
    };
    
    // 覆蓋表頭 - 加入防禦性檢查以避免 undefined 錯誤
    renderer.tablerow = function(content, flags) {
      // flags 可能是 undefined 或缺少 header 屬性（取決於 marked.js 版本）
      const isHeader = flags && flags.header === true;
      const style = isHeader ? 'background: #667eea; color: white; font-weight: 600;' : 'background: #f8f9fa;';
      return `<tr style="${style}">${content}</tr>\n`;
    };
    
    // 覆蓋表格單元格 - 加入防禦性檢查
    renderer.tablecell = function(content, flags) {
      // 安全地訪問 flags 屬性，避免 undefined 錯誤
      const align = (flags && flags.align) ? `text-align: ${flags.align};` : 'text-align: left;';
      const isHeader = flags && flags.header === true;
      const style = isHeader
        ? `padding: 12px 15px; ${align} border-bottom: 2px solid #e9ecef; font-weight: 600;`
        : `padding: 10px 15px; ${align} border-bottom: 1px solid #e9ecef;`;
      const tag = isHeader ? 'th' : 'td';
      return `<${tag} style="${style}">${content}</${tag}>`;
    };
    
    // 覆蓋強調 (粗體)
    renderer.strong = function(text) {
      return `<strong style="font-weight: 700; color: #212529;">${text}</strong>`;
    };
    
    // 覆蓋強調 (斜體)
    renderer.em = function(text) {
      return `<em style="font-style: italic; color: #666;">${text}</em>`;
    };
    
    // 覆蓋刪除線
    renderer.del = function(text) {
      return `<del style="text-decoration: line-through; color: #999;">${text}</del>`;
    };
    
    // 覆蓋危險的 HTML 標籤
    renderer.html = function(text) {
      // 將 HTML 標籤作為純文本顯示,而不是執行
      // 逃逸 HTML 字符,使其以文本形式顯示
      const escaped = escapeHtml(text);
      return `<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;"><code>${escaped}</code></pre>`;
    };
    
    // 覆蓋圖片渲染,添加沙盒屬性
    renderer.image = function(href, title, text) {
      if (!href || !isValidImageUrl(href)) {
        return '';
      }
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
      return `<figure style="margin: 1rem 0; text-align: center;">
        <img src="${escapeHtml(href)}" alt="${escapeHtml(text)}"${titleAttr} loading="lazy" style="max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        ${title ? `<figcaption style="color: #666; font-size: 0.9em; margin-top: 0.5rem;">${escapeHtml(title)}</figcaption>` : ''}
      </figure>`;
    };
    
    // 覆蓋連結渲染,添加安全屬性
    renderer.link = function(href, title, text) {
      if (!href || !isValidUrl(href)) {
        return text;
      }
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
      return `<a href="${escapeHtml(href)}"${titleAttr} target="_blank" rel="noopener noreferrer" style="color: #667eea; text-decoration: none; border-bottom: 1px solid #667eea; transition: all 0.2s;">${escapeHtml(text)}</a>`;
    };
    
    // 設置自訂 renderer
    marked.setOptions({ renderer: renderer });
  }

  const modeEdit = document.getElementById('mode-edit');
  const modeSplit = document.getElementById('mode-split');
  const modePreview = document.getElementById('mode-preview');

  if (modeEdit) {
    modeEdit.addEventListener('change', function() {
      if (this.checked) {
        container.classList.remove('split-mode', 'preview-mode');
      }
    });
  }

  if (modeSplit) {
    modeSplit.addEventListener('change', function() {
      if (this.checked) {
        container.classList.add('split-mode');
        container.classList.remove('preview-mode');
        updatePreview();
      }
    });
  }

  if (modePreview) {
    modePreview.addEventListener('change', function() {
      if (this.checked) {
        container.classList.add('preview-mode');
        container.classList.remove('split-mode');
        updatePreview();
      }
    });
  }

  let updateTimer;
  textarea.addEventListener('input', function() {
    clearTimeout(updateTimer);
    updateTimer = setTimeout(() => {
      updatePreview();
      updateStats();
    }, 300);
  });

  updatePreview();
  updateStats();

  function updatePreview() {
    if (!container.classList.contains('split-mode') && 
        !container.classList.contains('preview-mode')) {
      return;
    }

    const markdown = textarea.value;
    if (typeof marked !== 'undefined') {
      try {
        // 使用 marked 解析 markdown
        const html = marked.parse(markdown);
        
        // 清理 HTML: 移除所有 HTML 標籤,只保留純文本和 Markdown 結構
        const cleanHtml = sanitizeHtmlToPlainText(html);
        
        // 使用 textContent 防止 XSS - 將所有內容作為純文本顯示
        previewContent.innerHTML = '';
        
        // 保留基本的 Markdown 樣式但防止 HTML 執行
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cleanHtml;
        
        // 遍歷節點並清理任何潛在的 XSS
        cleanDOMNodes(tempDiv);
        
        previewContent.appendChild(tempDiv);
      } catch (error) {
        console.error('Markdown 解析錯誤:', error);
        previewContent.textContent = '無法解析 Markdown 內容';
      }
    } else {
      previewContent.innerHTML = '<p class="text-muted">載入 Markdown 解析器中...</p>';
    }
  }

  function updateStats() {
    const text = textarea.value;
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    const lineCount = text.split('\n').length;

    const charElement = document.getElementById('char-count');
    const wordElement = document.getElementById('word-count');
    const lineElement = document.getElementById('line-count');

    if (charElement) charElement.textContent = charCount;
    if (wordElement) wordElement.textContent = wordCount;
    if (lineElement) lineElement.textContent = lineCount;
  }

  textarea.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;
      const value = this.value;
      
      this.value = value.substring(0, start) + '  ' + value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
      
      this.dispatchEvent(new Event('input'));
    }
  });

  textarea.addEventListener('scroll', function() {
    if (container.classList.contains('split-mode')) {
      const previewPane = document.querySelector('.markdown-preview-pane');
      if (previewPane) {
        const scrollPercentage = this.scrollTop / (this.scrollHeight - this.clientHeight);
        previewPane.scrollTop = scrollPercentage * (previewPane.scrollHeight - previewPane.clientHeight);
      }
    }
  });
}

function saveKeyword() {
  // 首先驗證必填欄位
  const form = document.getElementById('keywordForm');
  if (!form) return;
  
  // 標記表單已提交，用於顯示驗證錯誤
  form.classList.add('has-submitted');
  
  // 重新檢查必填欄位以顯示錯誤指示
  checkRequiredFields();
  
  if (!validateAndNavigateToMissing()) {
    showNotification('請先填寫所有必填欄位', 'warning');
    return;
  }

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  formChanged = false;

  showLoadingOverlay('正在儲存...');

  form.submit();
}

function addVideoEntry() {
  const container = document.getElementById('videos-container');
  if (!container) return;
  
  const entries = container.querySelectorAll('.video-entry');
  const newIndex = entries.length;

  const videoHTML = `
    <div class="video-entry card mb-3">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <h5 class="card-title mb-0">影片 #${newIndex + 1}</h5>
          <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeVideoEntry(this)">
            <i class="bi bi-trash"></i>
          </button>
        </div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">YouTube 網址</label>
            <input type="text" name="videos-${newIndex}-url" class="form-control" placeholder="https://www.youtube.com/watch?v=...">
          </div>
          <div class="col-md-6">
            <label class="form-label">影片標題</label>
            <input type="text" name="videos-${newIndex}-title" class="form-control" placeholder="影片標題">
          </div>
        </div>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', videoHTML);
  
  const newEntry = container.lastElementChild;
  newEntry.style.opacity = '0';
  newEntry.style.transform = 'translateY(-10px)';
  setTimeout(() => {
    newEntry.style.transition = 'all 0.3s ease';
    newEntry.style.opacity = '1';
    newEntry.style.transform = 'translateY(0)';
  }, 10);
}

function removeVideoEntry(button) {
  const entry = button.closest('.video-entry');
  if (!entry) return;

  if (confirm('確定要移除這個影片嗎?')) {
    entry.style.transition = 'all 0.3s ease';
    entry.style.opacity = '0';
    entry.style.transform = 'translateX(-20px)';
    setTimeout(() => {
      entry.remove();
      updateVideoNumbers();
    }, 300);
  }
}

function updateVideoNumbers() {
  const entries = document.querySelectorAll('.video-entry');
  entries.forEach((entry, index) => {
    const title = entry.querySelector('.card-title');
    if (title) {
      title.textContent = `影片 #${index + 1}`;
    }
  });
}

function addAliasEntry() {
  const container = document.getElementById('aliases-container');
  const entries = container.querySelectorAll('.alias-entry');
  const newIndex = entries.length;

  const aliasHTML = `
    <div class="alias-entry mb-2">
      <input type="hidden" name="aliases-${newIndex}-alias_id" value="">
      <div class="input-group">
        <input type="text" name="aliases-${newIndex}-title" class="form-control" placeholder="輸入別名">
        <button type="button" class="btn btn-outline-danger" onclick="removeAliasEntry(this)">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', aliasHTML);
  
  const newInput = container.lastElementChild.querySelector('input[type="text"]');
  if (newInput) {
    newInput.focus();
  }
}

function removeAliasEntry(button) {
  const entry = button.closest('.alias-entry');
  if (!entry) return;

  entry.style.transition = 'all 0.2s ease';
  entry.style.opacity = '0';
  entry.style.transform = 'translateX(-10px)';
  setTimeout(() => {
    entry.remove();
  }, 200);
}

function insertMarkdown(prefix, suffix) {
  const textarea = document.getElementById('description_markdown');
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = textarea.value.substring(start, end);
  const beforeText = textarea.value.substring(0, start);
  const afterText = textarea.value.substring(end);

  const newText = beforeText + prefix + selectedText + suffix + afterText;
  textarea.value = newText;

  const newCursorPos = start + prefix.length + selectedText.length;
  textarea.setSelectionRange(newCursorPos, newCursorPos);
  textarea.focus();
  
  textarea.dispatchEvent(new Event('input'));
}

function insertTable() {
  const tableMarkdown = `
| 標題1 | 標題2 | 標題3 |
| ----- | ----- | ----- |
| 內容1 | 內容2 | 內容3 |
| 內容4 | 內容5 | 內容6 |
`;
  
  const textarea = document.getElementById('description_markdown');
  if (!textarea) return;

  const start = textarea.selectionStart;
  const beforeText = textarea.value.substring(0, start);
  const afterText = textarea.value.substring(start);

  textarea.value = beforeText + tableMarkdown + afterText;
  textarea.setSelectionRange(start, start + tableMarkdown.length);
  textarea.focus();
  
  textarea.dispatchEvent(new Event('input'));
}

function regenerateSEO() {
  const isCreating = window.location.pathname.includes('/create');
  
  if (isCreating) {
    showNotification('請先儲存關鍵字後再生成 SEO 內容', 'warning');
    return;
  }
  
  if (!confirm('確定要重新生成 SEO 內容嗎?這將覆蓋現有的自訂內容。')) {
    return;
  }

  showLoadingOverlay('正在生成 SEO 內容...');

  const keywordId = window.location.pathname.split('/').filter(Boolean).slice(-2, -1)[0];
  
  fetch(`/admin/keywords/${keywordId}/regenerate-seo`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
    }
  })
  .then(response => response.json())
  .then(data => {
    hideLoadingOverlay();
    if (data.success) {
      const seoContent = document.getElementById('seo_content');
      if (seoContent && data.seo_content) {
        seoContent.value = data.seo_content;
      }
      
      const autoGenerate = document.getElementById('seo_auto_generate');
      if (autoGenerate) {
        autoGenerate.checked = true;
        autoGenerate.dispatchEvent(new Event('change'));
      }
      
      showNotification('SEO 內容已重新生成', 'success');
    } else {
      showNotification(data.message || '生成失敗', 'error');
    }
  })
  .catch(error => {
    hideLoadingOverlay();
    console.error('Error:', error);
    showNotification('生成 SEO 內容時發生錯誤', 'error');
  });
}

function showLoadingOverlay(message = '載入中...') {
  let overlay = document.querySelector('.loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
      <div class="text-center">
        <div class="loading-spinner mx-auto mb-3"></div>
        <p class="loading-message text-muted">${message}</p>
      </div>
    `;
    document.body.appendChild(overlay);
  } else {
    const messageEl = overlay.querySelector('.loading-message');
    if (messageEl) {
      messageEl.textContent = message;
    }
    overlay.style.display = 'flex';
  }
}

function hideLoadingOverlay() {
  const overlay = document.querySelector('.loading-overlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

function showNotification(message, type = 'info') {
  const alertClass = {
    'success': 'alert-success',
    'error': 'alert-danger',
    'warning': 'alert-warning',
    'info': 'alert-info'
  }[type] || 'alert-info';

  const notification = document.createElement('div');
  notification.className = `alert ${alertClass} alert-dismissible fade show`;
  notification.style.position = 'fixed';
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.zIndex = '10000';
  notification.style.minWidth = '300px';
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveKeyword();
  }

  if (e.key === 'Escape') {
    const backButton = document.querySelector('.btn-back');
    if (backButton) {
      if (formChanged) {
        if (confirm('確定要離開編輯頁面嗎?未儲存的變更將會遺失。')) {
          formChanged = false;
          backButton.click();
        }
      } else {
        backButton.click();
      }
    }
  }
});

let autoSaveTimer;
function enableAutoSave() {
  const form = document.getElementById('keywordForm');
  if (!form) return;

  form.addEventListener('input', function() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
      saveDraft();
    }, 30000);
  });
}

function saveDraft() {
  const form = document.getElementById('keywordForm');
  if (!form) return;

  const formData = new FormData(form);
  const keywordId = window.location.pathname.split('/').filter(Boolean).slice(-2, -1)[0];

  fetch(`/admin/keywords/${keywordId}/save-draft`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
    }
  })
  .catch(error => {
    console.error('自動儲存失敗:', error);
  });
}

window.keywordEditor = {
  init: initKeywordEditor,
  save: saveKeyword,
  addVideo: addVideoEntry,
  removeVideo: removeVideoEntry,
  addAlias: addAliasEntry,
  removeAlias: removeAliasEntry,
  insertMarkdown: insertMarkdown,
  regenerateSEO: regenerateSEO
};

/**
 * HTML 轉義函數,防止 XSS 注入
 */
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, char => map[char]);
}

/**
 * 驗證 URL 是否安全
 */
function isValidUrl(url) {
  if (!url) return false;
  
  try {
    const urlObj = new URL(url, window.location.origin);
    // 只允許 http, https, mailto 協議
    return ['http:', 'https:', 'mailto:'].includes(urlObj.protocol);
  } catch {
    // 相對 URL
    return /^[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]*$/.test(url);
  }
}

/**
 * 驗證圖片 URL 是否安全
 */
function isValidImageUrl(url) {
  if (!isValidUrl(url)) return false;
  
  // 確保不是 javascript: 協議
  if (url.toLowerCase().includes('javascript:')) return false;
  if (url.toLowerCase().includes('data:text/html')) return false;
  
  return true;
}

/**
 * 手動清理和設置 HTML 內容(DOMPurify 備用方案)
 */
function sanitizeAndSetContent(element, html) {
  // 創建一個臨時容器
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  
  // 遞歸清理所有不安全的標籤和屬性
  cleanElement(tempDiv);
  
  // 設置清理後的內容
  element.innerHTML = '';
  while (tempDiv.firstChild) {
    element.appendChild(tempDiv.firstChild);
  }
}

/**
 * 遞歸清理元素中的不安全內容
 */
function cleanElement(element) {
  const allowedTags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'u', 'del', 'code', 'pre', 'ol', 'ul', 'li', 'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'span', 'div'];
  const allowedAttrs = ['href', 'title', 'alt', 'src', 'loading', 'style', 'target', 'rel', 'class'];
  
  // 使用 NodeList 的複製來避免在遍歷時修改 DOM
  const children = Array.from(element.childNodes);
  
  for (const child of children) {
    if (child.nodeType === Node.ELEMENT_NODE) {
      const tagName = child.tagName.toLowerCase();
      
      if (!allowedTags.includes(tagName)) {
        // 移除不允許的標籤,但保留文本內容
        const textContent = child.textContent;
        const textNode = document.createTextNode(textContent);
        child.parentNode.replaceChild(textNode, child);
      } else {
        // 清理屬性
        const attrs = Array.from(child.attributes);
        for (const attr of attrs) {
          if (!allowedAttrs.includes(attr.name.toLowerCase())) {
            child.removeAttribute(attr.name);
          } else {
            // 驗證屬性值
            if (attr.name === 'href') {
              if (!isValidUrl(attr.value)) {
                child.removeAttribute('href');
              }
            } else if (attr.name === 'src') {
              if (!isValidImageUrl(attr.value)) {
                child.removeAttribute('src');
              }
            } else if (attr.name === 'onclick' || attr.name.startsWith('on')) {
              child.removeAttribute(attr.name);
            }
          }
        }
        
        // 遞歸清理子元素
        cleanElement(child);
      }
    }
  }
}

/**
 * 將 HTML 轉換為純文本形式,防止 XSS 攻擊
 * 會移除所有可能危險的 HTML 標籤
 */
function sanitizeHtmlToPlainText(html) {
  // 創建一個臨時 DOM 元素來解析 HTML
  const temp = document.createElement('div');
  temp.innerHTML = html;
  
  // 移除所有可能危險的標籤
  const dangerousTags = ['script', 'style', 'iframe', 'object', 'embed', 'link', 'meta', 'form'];
  dangerousTags.forEach(tag => {
    const elements = temp.querySelectorAll(tag);
    elements.forEach(el => el.remove());
  });
  
  // 移除所有事件監聽屬性
  const allElements = temp.querySelectorAll('*');
  allElements.forEach(el => {
    // 移除 on* 屬性
    Array.from(el.attributes).forEach(attr => {
      if (attr.name.startsWith('on') || attr.name === 'href' && attr.value.startsWith('javascript:')) {
        el.removeAttribute(attr.name);
      }
    });
  });
  
  return temp.innerHTML;
}

/**
 * 清理 DOM 節點,移除所有事件監聽和危險屬性
 */
function cleanDOMNodes(node) {
  if (!node) return;
  
  if (node.nodeType === Node.ELEMENT_NODE) {
    // 移除所有 on* 事件屬性
    const attrs = Array.from(node.attributes);
    attrs.forEach(attr => {
      if (attr.name.startsWith('on') || 
          attr.name === 'href' && attr.value.startsWith('javascript:') ||
          attr.name === 'style' && /expression|javascript|behavior|binding/i.test(attr.value)) {
        node.removeAttribute(attr.name);
      }
    });
    
    // 遞歸清理子節點
    Array.from(node.childNodes).forEach(child => {
      cleanDOMNodes(child);
    });
  }
}

