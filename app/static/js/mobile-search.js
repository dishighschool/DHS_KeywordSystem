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
  
  function normalizeText(value) {
    return typeof value === 'string' ? value.toLowerCase().trim() : '';
  }

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function highlightText(text, query) {
    if (typeof text !== 'string' || !query) {
      return typeof text === 'string' ? text : '';
    }
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark class="bg-warning bg-opacity-25 px-1 rounded">$1</mark>');
  }

  function buildSnippet(text, normalizedQuery, limit = 100) {
    if (typeof text !== 'string' || !text.length) {
      return '';
    }
    if (!normalizedQuery) {
      return text.length > limit ? `${text.slice(0, limit - 3).trimEnd()}...` : text;
    }

    const lowerText = text.toLowerCase();
    const index = lowerText.indexOf(normalizedQuery);

    if (index === -1) {
      return text.length > limit ? `${text.slice(0, limit - 3).trimEnd()}...` : text;
    }

    const half = Math.floor(limit / 2);
    let start = Math.max(0, index - half);
    if (start > 0) {
      const prevSpace = text.lastIndexOf(' ', index);
      if (prevSpace > start) {
        start = prevSpace + 1;
      }
    }
    const end = Math.min(text.length, start + limit);
    const snippet = text.slice(start, end).trim();
    const prefix = start > 0 ? '...' : '';
    const suffix = end < text.length ? '...' : '';

    return `${prefix}${snippet}${suffix}`;
  }
  
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
      
      const normalizedQuery = normalizeText(query);
      const filteredResults = allData.filter(item => {
        const titleMatch = normalizeText(item.title).includes(normalizedQuery);
  const descriptionMatch = normalizeText(item.description_full || item.description).includes(normalizedQuery);
        const categoryMatch = normalizeText(item.category).includes(normalizedQuery);
        const seoMatch = item.seo_text && normalizeText(item.seo_text).includes(normalizedQuery);
        const aliasMatch = item.main_keyword && normalizeText(item.main_keyword).includes(normalizedQuery);

        return titleMatch || descriptionMatch || categoryMatch || seoMatch || aliasMatch;
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
        mobileSearchResultsList.innerHTML = filteredResults
          .map(result => {
            const titleHtml = highlightText(result.title, query);
            const categoryHtml = highlightText(result.category || '', query);
            const aliasHtml = result.main_keyword ? highlightText(result.main_keyword, query) : '';

            const descriptionSource = result.description_full || result.description || '';
            const descriptionMatch = normalizeText(descriptionSource).includes(normalizedQuery);
            const snippetSource = descriptionMatch || !result.seo_text ? descriptionSource : result.seo_text || '';
            const snippetPlainRaw = buildSnippet(snippetSource, normalizedQuery, 100);
            const snippetPlain = snippetPlainRaw || result.description || '';
            const snippetHtml = highlightText(snippetPlain, query);
            const shouldShowSnippet = snippetPlain.trim().length > 0;

            return `
              <a href="${result.url}" class="search-result-item text-decoration-none d-block">
                <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
                  <h6 class="mb-0 fw-semibold flex-grow-1" style="min-width: 0;">${titleHtml}</h6>
                  <span class="badge bg-primary">${result.type === 'keyword' ? '關鍵字' : result.type === 'alias' ? '別名' : '分類'}</span>
                </div>
                ${shouldShowSnippet ? `<p class="small text-muted mb-1">${snippetHtml}</p>` : ''}
                ${result.type === 'alias' && aliasHtml ? `<div class="small text-muted mb-1"><i class="bi bi-link-45deg me-1"></i>${aliasHtml}</div>` : ''}
                ${categoryHtml ? `<div class="small text-muted"><i class="bi bi-folder me-1"></i>${categoryHtml}</div>` : ''}
              </a>
            `;
          })
          .join('');
      
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
