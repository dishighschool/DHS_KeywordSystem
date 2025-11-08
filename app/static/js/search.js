document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector("#keywordSearch");
  const categoryButtons = document.querySelectorAll("#categoryFilters button");
  const keywordCards = document.querySelectorAll(".keyword-card-item");
  const categorySections = document.querySelectorAll(".keyword-category-section");
  const searchResultsSection = document.getElementById("searchResultsSection");
  const searchResultsGrid = document.getElementById("searchResultsGrid");
  const clearSearchBtn = document.getElementById("clearSearch");
  const keywordGrid = document.getElementById("keywordGrid");
  const showAliasesToggle = document.getElementById("showAliasesToggle");
  const resultCount = document.getElementById("resultCount");

  let activeCategory = "all";
  let showAliases = false;
  let allKeywords = [];

  keywordCards.forEach(card => {
    allKeywords.push({
      element: card,
      title: card.dataset.title || "",
      category: card.dataset.category || "",
      categoryName: card.closest('.keyword-category-section')?.querySelector('.category-section-title')?.textContent.trim() || "",
      description: card.dataset.description || "",
      isAlias: card.dataset.isAlias === "true",
      html: card.innerHTML,
      link: card.querySelector('.keyword-card-link')?.href || ""
    });
  });

  const normalize = (text) =>
    text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");

  const showSearchResults = (query) => {
    const normalizedQuery = normalize(query);
    
    const results = allKeywords.filter(kw => {
      const matchesQuery = normalize(kw.title).includes(normalizedQuery) || 
                          normalize(kw.description).includes(normalizedQuery);
      const matchesCategory = activeCategory === "all" || activeCategory === kw.category;
      return matchesQuery && matchesCategory;
    });

    searchResultsGrid.innerHTML = "";

    if (results.length > 0) {
      results.forEach(kw => {
        const resultCard = document.createElement('article');
        resultCard.className = 'keyword-card-item-flat';
        resultCard.innerHTML = `
          <a href="${kw.link}" class="keyword-card-link-flat">
            <div class="keyword-card-content-flat">
              <div class="keyword-card-category-badge">
                <i class="bi bi-folder2"></i>
                ${kw.categoryName}
              </div>
              <h3 class="keyword-card-title-flat">${kw.title}</h3>
              ${kw.isAlias ? '<span class="keyword-alias-badge"><i class="bi bi-link-45deg"></i> 別名</span>' : ''}
            </div>
          </a>
        `;
        searchResultsGrid.appendChild(resultCard);
      });
      
      if (window.RippleEffect) {
        const ripple = new window.RippleEffect();
        ripple.addRippleToElements('.keyword-card-link-flat');
      }
      
      searchResultsSection.classList.remove('d-none');
      keywordGrid.classList.add('d-none');
    } else {
      searchResultsGrid.innerHTML = '<div class="empty-state-search"><i class="bi bi-search"></i><p>未找到符合的關鍵字</p></div>';
      searchResultsSection.classList.remove('d-none');
      keywordGrid.classList.add('d-none');
    }
  };

  const clearSearch = () => {
    searchInput.value = "";
    searchResultsSection.classList.add('d-none');
    keywordGrid.classList.remove('d-none');
    
    keywordCards.forEach(card => {
      const isAlias = card.dataset.isAlias === "true";
      const categoryId = card.dataset.category || "";
      const matchesCategory = activeCategory === "all" || activeCategory === categoryId;
      const shouldShow = matchesCategory && (showAliases || !isAlias);
      
      if (shouldShow) {
        card.classList.remove("d-none");
      } else {
        card.classList.add("d-none");
      }
    });
    
    updateCategorySectionsVisibility();
    updateResultCount();
  };

  const applyFilters = (skipToggleUpdate = false) => {
    const query = searchInput.value.trim();
    
    if (query.length > 0) {
      if (showAliasesToggle && !showAliases && !skipToggleUpdate) {
        showAliases = true;
        showAliasesToggle.checked = true;
        localStorage.setItem('showAliases', 'true');
      }
      
      showSearchResults(query);
    } else {
      clearSearch();
      
      keywordCards.forEach((card) => {
        const categoryId = card.dataset.category || "";
        const isAlias = card.dataset.isAlias === "true";
        const matchesCategory = activeCategory === "all" || activeCategory === categoryId;
        const matchesAliasFilter = showAliases || !isAlias;
        
        if (matchesCategory && matchesAliasFilter) {
          card.classList.remove("d-none");
        } else {
          card.classList.add("d-none");
        }
      });

      updateCategorySectionsVisibility();
      updateResultCount();
    }
  };

  const updateCategorySectionsVisibility = () => {
    categorySections.forEach((section) => {
      const visibleCards = section.querySelectorAll(".keyword-card-item:not(.d-none)");
      if (visibleCards.length === 0) {
        section.classList.add("d-none");
      } else {
        section.classList.remove("d-none");
      }
    });
  };

  const updateResultCount = () => {
    if (!resultCount) return;
    
    const visibleCards = document.querySelectorAll(".keyword-card-item:not(.d-none)");
    const count = visibleCards.length;
    resultCount.innerHTML = `<i class="bi bi-file-text me-1"></i>共 ${count} 筆`;
  };

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", clearSearch);
  }

  if (showAliasesToggle) {
    showAliasesToggle.addEventListener("change", (event) => {
      showAliases = event.target.checked;
      
      localStorage.setItem('showAliases', showAliases);
      
      applyFilters(true);
      
      if (navigator.vibrate) {
        navigator.vibrate(10);
      }
    });
    
    const savedPreference = localStorage.getItem('showAliases');
    if (savedPreference !== null) {
      showAliases = savedPreference === 'true';
      showAliasesToggle.checked = showAliases;
      applyFilters(true);
    }
  }

  categoryButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      categoryButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
      activeCategory = button.dataset.category || "all";
      applyFilters();
    });
  });
});
