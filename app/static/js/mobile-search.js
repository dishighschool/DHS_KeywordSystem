document.addEventListener('DOMContentLoaded', function() {
  'use strict';
  
  const mobileSearchBtn = document.getElementById('mobileSearchBtn');
  const mobileSearchModal = document.getElementById('mobileSearchModal');
  const closeMobileSearch = document.getElementById('closeMobileSearch');
  const mobileSearchInput = document.getElementById('mobileSearchInput');
  const mobileSearchResultsList = document.getElementById('mobileSearchResultsList');
  const mobileSearchLoading = document.getElementById('mobileSearchLoading');
  
  if (!mobileSearchBtn || !mobileSearchModal || !closeMobileSearch) {
    console.error('Mobile search elements not found', {
      mobileSearchBtn: !!mobileSearchBtn,
      mobileSearchModal: !!mobileSearchModal,
      closeMobileSearch: !!closeMobileSearch
    });
    return;
  }
  
  
  if (mobileSearchLoading) {
    mobileSearchLoading.style.display = 'none';
  }
  
  let searchTimeout = null;
  
  function openSearchModal() {
    
    mobileSearchModal.classList.add('active');
    document.body.classList.add('mobile-search-open');
    
    mobileSearchInput.value = '';
    mobileSearchResultsList.innerHTML = '';
    mobileSearchLoading.style.display = 'none';
    
    
    setTimeout(() => {
      mobileSearchInput.focus();
    }, 100);
  }
  
  function closeSearchModal() {
    mobileSearchModal.classList.remove('active');
    document.body.classList.remove('mobile-search-open');
    mobileSearchInput.value = '';
    mobileSearchResultsList.innerHTML = '';
    mobileSearchLoading.style.display = 'none';
  }
  
  async function performSearch(query) {
    if (!query || query.trim().length < 1) {
      mobileSearchResultsList.innerHTML = '';
      mobileSearchLoading.style.display = 'none';
      return;
    }
    
    mobileSearchLoading.style.display = 'block';
    mobileSearchResultsList.innerHTML = '';
    
    try {
      const response = await fetch(`/api/search`);
      const allData = await response.json();
      
      mobileSearchLoading.style.display = 'none';
      
      const queryLower = query.toLowerCase();
      const filteredResults = allData.filter(item => {
        return item.title.toLowerCase().includes(queryLower) ||
               (item.description && item.description.toLowerCase().includes(queryLower)) ||
               (item.category && item.category.toLowerCase().includes(queryLower));
      });
      
      if (!filteredResults || filteredResults.length === 0) {
        mobileSearchResultsList.innerHTML = `
          <div class="p-4 text-center text-muted">
            <i class="bi bi-search fs-1 mb-3 d-block"></i>
            <p class="mb-0">找不到相關結果</p>
          </div>
        `;
        return;
      }
      
      mobileSearchResultsList.innerHTML = filteredResults.map(result => `
        <a href="${result.url}" class="search-result-item text-decoration-none d-block">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
            <h6 class="mb-0 fw-semibold flex-grow-1" style="min-width: 0;">${highlightText(result.title, query)}</h6>
            <span class="badge bg-primary">${result.type === 'keyword' ? '關鍵字' : result.type === 'alias' ? '別名' : '分類'}</span>
          </div>
          ${result.description ? `<p class="small text-muted mb-1">${truncateText(highlightText(result.description, query), 80)}</p>` : ''}
          ${result.category ? `<div class="small text-muted"><i class="bi bi-folder me-1"></i>${result.category}</div>` : ''}
        </a>
      `).join('');
      
    } catch (error) {
      console.error('搜索錯誤:', error);
      mobileSearchLoading.style.display = 'none';
      mobileSearchResultsList.innerHTML = `
        <div class="p-4 text-center text-danger">
          <i class="bi bi-exclamation-triangle fs-1 mb-3 d-block"></i>
          <p class="mb-0">搜索出錯，請稍後再試</p>
        </div>
      `;
    }
  }
  
  function highlightText(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark class="bg-warning bg-opacity-25 px-1 rounded">$1</mark>');
  }
  
  function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
  }
  
  mobileSearchBtn.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    openSearchModal();
  });
  
  closeMobileSearch.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    closeSearchModal();
  });
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileSearchModal.classList.contains('active')) {
      closeSearchModal();
    }
  });
  
  mobileSearchModal.addEventListener('click', (e) => {
    if (e.target === mobileSearchModal) {
      closeSearchModal();
    }
  });
  
  mobileSearchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    searchTimeout = setTimeout(() => {
      performSearch(query);
    }, 300);
  });
  
  mobileSearchInput.addEventListener('blur', (e) => {
  });
  
});
