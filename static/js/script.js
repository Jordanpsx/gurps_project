// Aguarda o carregamento completo do DOM antes de executar o script
document.addEventListener('DOMContentLoaded', () => {
    
    // Objeto para armazenar o estado atual da aplicação (a nossa "fonte da verdade")
    const state = {
        lang: 'pt',
        currentPage: 1,
        sortBy: 'id', // O padrão é "Ordem do Livro"
        spells: [],
        selectedSpell: null,
        filters: {
            school: '',
            type: '',
            search: '' // Preparado para a futura funcionalidade de busca
        }
    };

    // Mapeamento de elementos do DOM para evitar repetição de 'getElementById'
    const dom = {
        loadingIndicator: document.getElementById('loading-indicator'),
        spellList: document.getElementById('spell-list'),
        statBlock: document.getElementById('stat-block'),
        pagination: document.getElementById('pagination'),
        langToggle: document.getElementById('lang-toggle'),
        sortSelect: document.getElementById('sort-select'),
        schoolFilter: document.getElementById('school-filter'),
        typeFilter: document.getElementById('type-filter'),
        searchInput: document.getElementById('search-input'),
        resetFiltersBtn: document.getElementById('reset-filters-btn')
    };

    // --- FUNÇÕES DE API ---

    /**
     * Busca a lista de magias na API com base no estado atual da aplicação.
     */
    const fetchSpells = async () => {
        showLoading(true);
        try {
            // Constrói os parâmetros da URL a partir do objeto de estado
            const params = new URLSearchParams({
                page: state.currentPage,
                sort: state.sortBy
            });

            // Adiciona os filtros apenas se tiverem um valor selecionado
            if (state.filters.school) params.append('school', state.filters.school);
            if (state.filters.type) params.append('type', state.filters.type);
            
            const response = await fetch(`/api/magias/${state.lang}?${params.toString()}`);
            if (!response.ok) throw new Error('Falha na rede ou erro na API');
            
            const data = await response.json();
            state.spells = data.spells;
            
            // Atualiza a interface com os novos dados
            renderSpellList();
            renderPagination(data.pagination);
            renderPlaceholder(); // Limpa o painel de detalhes

        } catch (error) {
            console.error("Erro ao buscar magias:", error);
            dom.spellList.innerHTML = `<p class="error" style="padding: 1rem;">Não foi possível carregar as magias.</p>`;
        } finally {
            showLoading(false);
        }
    };
    
    /**
     * Busca as listas de escolas e tipos para preencher os menus de filtro.
     */
    const populateFilters = async () => {
        try {
            const response = await fetch('/api/filtros');
            if (!response.ok) throw new Error('Falha ao buscar filtros');
            const data = await response.json();

            // Limpa opções antigas, mantendo a primeira ("Todas")
            dom.schoolFilter.length = 1; 
            data.escolas.forEach(school => {
                const option = new Option(school, school);
                dom.schoolFilter.add(option);
            });

            dom.typeFilter.length = 1;
            data.tipos.forEach(type => {
                const option = new Option(type, type);
                dom.typeFilter.add(option);
            });
        } catch (error) {
            console.error("Erro ao popular filtros:", error);
        }
    };

    // --- FUNÇÕES DE RENDERIZAÇÃO (Atualização da Interface) ---

    /**
     * Renderiza a lista de magias no painel central.
     */
    const renderSpellList = () => {
        dom.spellList.innerHTML = '';
        if (state.spells.length === 0) {
            dom.spellList.innerHTML = '<p style="padding: 1rem;">Nenhuma magia encontrada com os filtros selecionados.</p>';
            return;
        }
        const list = document.createElement('ul');
        state.spells.forEach(spell => {
            const button = document.createElement('button');
            button.textContent = spell.name;
            button.dataset.spellUniqueName = spell.name_unique;
            // Adiciona a classe 'active' se a magia estiver selecionada
            if (state.selectedSpell && state.selectedSpell.name_unique === spell.name_unique) {
                button.classList.add('active');
            }
            const item = document.createElement('li');
            item.appendChild(button);
            list.appendChild(item);
        });
        dom.spellList.appendChild(list);
    };

    /**
     * Renderiza o bloco de estatísticas da magia selecionada no painel direito.
     */
    const renderStatBlock = (spell) => {
        state.selectedSpell = spell;
        const schoolsText = spell.schools.join(', ') || 'Nenhuma';
        const prereqsHtml = spell.prerequisites_obj.map(p => 
            `<a href="#" class="prereq-link" data-spell-unique-name="${p.name_unique}">${p.name}</a>`
        ).join(', ');
        
        dom.statBlock.innerHTML = `
            <article>
                <header>
                    <h2>${spell.name}</h2>
                    <p><em>${schoolsText} (${spell.type})</em></p>
                </header>
                <p>${spell.description || ''}</p>
                <h4>Detalhes</h4>
                <div class="grid">
                    <div><strong>Custo:</strong> ${spell.cost_text || 'N/A'}</div>
                    <div><strong>Manutenção:</strong> ${spell.maintenance_cost_text || 'N/A'}</div>
                    <div><strong>Tempo de Execução:</strong> ${spell.casting_time || 'N/A'}</div>
                    <div><strong>Duração:</strong> ${spell.duration || 'N/A'}</div>
                </div>
                <h4>Pré-requisitos</h4>
                <p>${prereqsHtml || spell.prerequisites_text || 'Nenhum'}</p>
                <h4>Item</h4>
                <p>${spell.item_description || 'Informação não disponível.'}</p>
                <footer><small>Referência: ${spell.reference || 'N/A'}</small></footer>
            </article>`;
        renderSpellList(); // Re-renderiza a lista para destacar o item ativo
    };
    
    /**
     * Renderiza os controlos de paginação.
     */
    const renderPagination = (pagination) => {
        dom.pagination.innerHTML = '';
        if (pagination.total_pages <= 1) return;
        
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Anterior';
        prevButton.disabled = !pagination.has_prev;
        prevButton.addEventListener('click', () => handlePageChange(pagination.page - 1));
        
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Próxima';
        nextButton.disabled = !pagination.has_next;
        nextButton.addEventListener('click', () => handlePageChange(pagination.page + 1));
        
        const pageInfo = document.createElement('span');
        pageInfo.textContent = `Pág. ${pagination.page} de ${pagination.total_pages}`;
        
        dom.pagination.appendChild(prevButton);
        dom.pagination.appendChild(pageInfo);
        dom.pagination.appendChild(nextButton);
    };
    
    /**
     * Mostra a mensagem inicial no painel de detalhes.
     */
    const renderPlaceholder = () => {
        state.selectedSpell = null;
        dom.statBlock.innerHTML = `
            <div class="placeholder">
                <h2>Selecione uma magia</h2>
                <p>Use os filtros à esquerda para refinar a sua busca.</p>
            </div>`;
        if (state.spells.length > 0) renderSpellList();
    };

    /**
     * Mostra ou esconde o indicador de carregamento.
     */
    const showLoading = (isLoading) => {
        dom.loadingIndicator.classList.toggle('hidden', !isLoading);
    };

    // --- MANIPULADORES DE EVENTOS ---
    
    const handleFilterChange = () => {
        state.filters.school = dom.schoolFilter.value;
        state.filters.type = dom.typeFilter.value;
        state.currentPage = 1; // Sempre volta para a primeira página ao aplicar um filtro
        fetchSpells();
    };

    const handleFilterReset = () => {
        dom.schoolFilter.value = '';
        dom.typeFilter.value = '';
        dom.searchInput.value = '';
        handleFilterChange(); // Reutiliza a lógica para atualizar o estado e recarregar
    };

    const handleSearchInput = (event) => {
        console.log(`Busca futura por: ${event.target.value}`);
    };
    
    const handleSpellClick = (event) => {
        const button = event.target.closest('button[data-spell-unique-name]');
        if (button) {
            const uniqueName = button.dataset.spellUniqueName;
            const spell = state.spells.find(s => s.name_unique === uniqueName);
            if (spell) renderStatBlock(spell);
        }
    };
    
    const handlePrereqClick = (event) => {
        if (event.target.classList.contains('prereq-link')) {
            event.preventDefault();
            console.log(`Clicou no pré-requisito: ${event.target.dataset.spellUniqueName}. Funcionalidade a ser implementada.`);
        }
    };

    const handleLangChange = (event) => { state.lang = event.target.checked ? 'en' : 'pt'; fetchSpells(); };
    const handleSortChange = (event) => { state.sortBy = event.target.value; state.currentPage = 1; fetchSpells(); };
    const handlePageChange = (newPage) => { state.currentPage = newPage; fetchSpells(); };

    // --- INICIALIZAÇÃO DA APLICAÇÃO ---
    const init = () => {
        // Configura todos os listeners de eventos
        dom.langToggle.addEventListener('change', handleLangChange);
        dom.sortSelect.addEventListener('change', handleSortChange);
        dom.schoolFilter.addEventListener('change', handleFilterChange);
        dom.typeFilter.addEventListener('change', handleFilterChange);
        dom.resetFiltersBtn.addEventListener('click', handleFilterReset);
        dom.searchInput.addEventListener('input', handleSearchInput);
        dom.spellList.addEventListener('click', handleSpellClick);
        dom.statBlock.addEventListener('click', handlePrereqClick);
        
        // Busca os dados iniciais para popular a página
        populateFilters();
        fetchSpells();
    };

    init(); // Inicia a aplicação
});

