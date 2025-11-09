// 簡化版 Icon Picker - 直接在輸入框上操作
const BOOTSTRAP_ICONS = [
  'house', 'home', 'info-circle', 'info-circle-fill', 'question-circle', 'exclamation-circle',
  'check-circle', 'x-circle', 'plus-circle', 'dash-circle', 'star', 'star-fill', 'heart', 'heart-fill',
  'bell', 'bell-fill', 'bookmark', 'bookmark-fill', 'calendar', 'calendar-fill', 'clock', 'clock-fill',
  'envelope', 'envelope-fill', 'file', 'file-fill', 'folder', 'folder-fill', 'gear', 'search',
  'person', 'person-fill', 'chat', 'chat-fill', 'camera', 'camera-fill', 'image', 'images',
  'book', 'book-fill', 'pencil', 'pencil-fill', 'trash', 'trash-fill', 'download', 'upload',
  'cloud', 'cloud-fill', 'sun', 'sun-fill', 'moon', 'moon-fill', 'globe', 'map', 'pin', 'pin-fill',
  'tag', 'tag-fill', 'tags', 'tags-fill', 'trophy', 'trophy-fill', 'gift', 'gift-fill',
  'facebook', 'twitter', 'twitter-x', 'instagram', 'youtube', 'github', 'discord', 'linkedin',
  'megaphone', 'megaphone-fill', 'layout-text-window', 'layout-text-window-reverse',
  'activity', 'alarm', 'award', 'bag', 'basket', 'battery', 'bicycle', 'box', 'briefcase',
  'broadcast', 'bug', 'building', 'calculator', 'camera-video', 'cart', 'cup', 'database',
  'device-hdd', 'display', 'door-closed', 'door-open', 'emoji-smile', 'eye', 'eye-slash',
  'file-earmark', 'file-text', 'filter', 'flag', 'flower1', 'flower2', 'globe-americas',
  'globe-asia-australia', 'globe-europe-africa', 'grid', 'hammer', 'hand-thumbs-up',
  'headphones', 'hospital', 'hourglass', 'journal', 'key', 'laptop', 'lightbulb',
  'lightning', 'link', 'list', 'lock', 'mailbox', 'mic', 'music-note', 'newspaper',
  'palette', 'paperclip', 'peace', 'pen', 'phone', 'printer', 'puzzle', 'rocket',
  'shield', 'shop', 'shuffle', 'signpost', 'speedometer', 'stopwatch', 'table',
  'tablet', 'telephone', 'terminal', 'thermometer', 'tools', 'tv', 'umbrella',
  'wallet', 'watch', 'wifi', 'wrench', 'arrow-up', 'arrow-down', 'arrow-left', 'arrow-right',
  'arrow-up-circle', 'arrow-down-circle', 'arrow-left-circle', 'arrow-right-circle',
  'chevron-up', 'chevron-down', 'chevron-left', 'chevron-right', 'caret-up', 'caret-down',
  'caret-left', 'caret-right', 'plus', 'dash', 'x', 'check', 'check-lg', 'x-lg'
];

class SimpleIconPicker {
  constructor(input) {
    this.input = input;
    
    // 確保父元素有相對定位
    if (this.input.parentElement.style.position !== 'relative') {
      this.input.parentElement.style.position = 'relative';
    }
    
    // 創建包裝容器
    this.wrapper = document.createElement('div');
    this.wrapper.className = 'icon-picker-wrapper';
    this.wrapper.style.position = 'relative';
    this.wrapper.style.display = 'block';
    
    // 將 input 包裝起來
    this.input.parentNode.insertBefore(this.wrapper, this.input);
    this.wrapper.appendChild(this.input);
    
    // 創建圖示預覽元素
    this.preview = document.createElement('span');
    this.preview.className = 'icon-preview-badge';
    this.wrapper.appendChild(this.preview);
    
    // 創建下拉選單
    this.createDropdown();
    
    // 綁定事件
    this.input.addEventListener('click', (e) => {
      e.preventDefault();
      this.toggle();
    });
    
    // 點擊外部關閉
    document.addEventListener('click', (e) => {
      if (!this.dropdown.contains(e.target) && e.target !== this.input && e.target !== this.preview) {
        this.close();
      }
    });
    
    // 允許手動輸入
    this.input.addEventListener('input', () => {
      this.updateInputPreview();
    });
    
    // 更新預覽
    this.updateInputPreview();
  }
  
  createDropdown() {
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'icon-picker-dropdown-simple';
    this.dropdown.style.display = 'none';
    
    // 提示文字
    const hint = document.createElement('small');
    hint.className = 'text-muted d-block mb-2';
    hint.textContent = '💡 提示：可直接在輸入框輸入自訂圖示代碼（如 bi-house）';
    
    // 搜尋框
    const searchBox = document.createElement('input');
    searchBox.type = 'text';
    searchBox.className = 'form-control form-control-sm mb-2';
    searchBox.placeholder = '搜尋圖示...';
    searchBox.addEventListener('input', (e) => this.filter(e.target.value));
    searchBox.addEventListener('click', (e) => e.stopPropagation());
    
    // 圖示網格
    this.grid = document.createElement('div');
    this.grid.className = 'icon-picker-grid-simple';
    
    // 按鈕區
    const btnGroup = document.createElement('div');
    btnGroup.className = 'd-flex gap-2 mt-2';
    
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-sm btn-secondary flex-fill';
    clearBtn.innerHTML = '<i class="bi bi-x-lg"></i> 清除';
    clearBtn.addEventListener('click', () => {
      this.select('');
      this.close();
    });
    
    const customBtn = document.createElement('button');
    customBtn.type = 'button';
    customBtn.className = 'btn btn-sm btn-primary flex-fill';
    customBtn.innerHTML = '<i class="bi bi-pencil"></i> 自訂輸入';
    customBtn.addEventListener('click', () => {
      this.close();
      this.input.readOnly = false;
      this.input.focus();
      this.input.select();
    });
    
    btnGroup.appendChild(clearBtn);
    btnGroup.appendChild(customBtn);
    
    this.dropdown.appendChild(hint);
    this.dropdown.appendChild(searchBox);
    this.dropdown.appendChild(this.grid);
    this.dropdown.appendChild(btnGroup);
    
    // 添加到 body
    document.body.appendChild(this.dropdown);
    
    // 渲染所有圖示
    this.renderIcons(BOOTSTRAP_ICONS);
  }
  
  renderIcons(icons) {
    this.grid.innerHTML = '';
    icons.slice(0, 100).forEach(icon => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'icon-picker-item-simple';
      btn.innerHTML = `<i class="bi bi-${icon}"></i>`;
      btn.title = icon;
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.select(`bi-${icon}`);
        this.close();
      });
      this.grid.appendChild(btn);
    });
  }
  
  filter(query) {
    const filtered = BOOTSTRAP_ICONS.filter(icon => 
      icon.toLowerCase().includes(query.toLowerCase())
    );
    this.renderIcons(filtered);
  }
  
  select(iconClass) {
    this.input.value = iconClass;
    this.input.readOnly = true;
    this.updateInputPreview();
    
    // 觸發 change 事件
    const event = new Event('change', { bubbles: true });
    this.input.dispatchEvent(event);
  }
  
  updateInputPreview() {
    const iconClass = this.input.value.trim();
    if (iconClass) {
      this.input.style.paddingLeft = '2.5rem';
      this.preview.innerHTML = `<i class="${iconClass}"></i>`;
      this.preview.style.display = 'inline-flex';
    } else {
      this.preview.style.display = 'none';
      this.input.style.paddingLeft = '';
    }
  }
  
  toggle() {
    if (this.dropdown.style.display === 'none') {
      this.open();
    } else {
      this.close();
    }
  }
  
  open() {
    // 定位下拉選單
    const rect = this.input.getBoundingClientRect();
    this.dropdown.style.display = 'block';
    this.dropdown.style.position = 'fixed';
    this.dropdown.style.left = rect.left + 'px';
    this.dropdown.style.top = (rect.bottom + 5) + 'px';
    this.dropdown.style.width = Math.max(rect.width, 300) + 'px';
    this.dropdown.style.zIndex = '9999';
    
    // 聚焦搜尋框
    const searchBox = this.dropdown.querySelector('input[type="text"]');
    if (searchBox) {
      setTimeout(() => searchBox.focus(), 100);
    }
  }
  
  close() {
    this.dropdown.style.display = 'none';
  }
}

// 自動初始化函式
function initIconPickers() {
  document.querySelectorAll('.icon-picker-input').forEach(input => {
    // 檢查是否已經初始化（避免重複）
    if (!input.dataset.iconPickerInit && !input.closest('.icon-picker-wrapper')) {
      new SimpleIconPicker(input);
      input.dataset.iconPickerInit = 'true';
    }
  });
}

// 頁面載入時自動初始化
document.addEventListener('DOMContentLoaded', initIconPickers);

// 導出供外部使用
window.SimpleIconPicker = SimpleIconPicker;
window.initIconPickers = initIconPickers;
