document.addEventListener('DOMContentLoaded', () => {
    // Adiciona o novo seletor
    const seletorOrdenacao = document.getElementById('ordenacao');
    // ... (resto dos seus seletores: inputBusca, filtroEscola, etc.)
    const inputBusca = document.getElementById('busca'); const filtroEscola = document.getElementById('filtro-escola'); const filtroTipo = document.getElementById('filtro-tipo'); const containerNomes = document.getElementById('lista-nomes-magias'); const containerDetalhes = document.getElementById('detalhes-magia'); const botoesIdioma = document.querySelectorAll('#seletor-idioma button'); const themeSwitcher = document.querySelectorAll('input[name="theme"]'); const htmlElement = document.documentElement;

    let todasAsMagias = [];
    let itemAtivo = null;

    // ... (cole aqui suas funções popularFiltros, aplicarFiltros, renderizarLista, renderizarDetalhes)
    function popularFiltros() { filtroEscola.innerHTML = '<option value="">Todas as Escolas</option>'; filtroTipo.innerHTML = '<option value="">Todos os Tipos</option>'; const escolas = [...new Set(todasAsMagias.flatMap(m => m.escola))].filter(Boolean).sort(); const tipos = [...new Set(todasAsMagias.map(m => m.tipo))].filter(Boolean).sort(); escolas.forEach(escola => { const option = document.createElement('option'); option.value = escola; option.textContent = escola; filtroEscola.appendChild(option); }); tipos.forEach(tipo => { const option = document.createElement('option'); option.value = tipo; option.textContent = tipo; filtroTipo.appendChild(option); }); }
    function aplicarFiltros() { const termoBusca = inputBusca.value.toLowerCase(); const escolaSelecionada = filtroEscola.value; const tipoSelecionado = filtroTipo.value; const magiasFiltradas = todasAsMagias.filter(magia => { const correspondeBusca = magia.nome.toLowerCase().includes(termoBusca); const correspondeEscola = !escolaSelecionada || (magia.escola && magia.escola.includes(escolaSelecionada)); const correspondeTipo = !tipoSelecionado || magia.tipo === tipoSelecionado; return correspondeBusca && correspondeEscola && correspondeTipo; }); renderizarLista(magiasFiltradas); renderizarDetalhes(null); }
    function renderizarLista(magias) { containerNomes.innerHTML = ''; magias.forEach(magia => { const link = document.createElement('a'); link.href = '#'; link.className = 'item-lista'; link.textContent = magia.nome; link.dataset.id = magia.id; containerNomes.appendChild(link); }); }
    function renderizarDetalhes(magia) { if (itemAtivo) { itemAtivo.classList.remove('active'); itemAtivo = null; } if (!magia) { containerDetalhes.innerHTML = `<article><h3>Bem-vindo!</h3><p>Use os filtros ou selecione uma magia na lista para ver seus detalhes.</p></article>`; return; } containerDetalhes.innerHTML = `<article><header><h2>${magia.nome}</h2><p><strong>${magia.escola_display} / ${magia.tipo}</strong></p></header><p>${magia.descricao || 'Sem descrição.'}</p><hr class="stat-block-hr"><div class="stat-block-propriedade"><strong>Tempo de Conjuração:</strong> ${magia.tempo_conjuracao || 'N/A'}</div><div class="stat-block-propriedade"><strong>Custo:</strong> ${magia.custo}</div><div class="stat-block-propriedade"><strong>Duração:</strong> ${magia.duracao}</div><hr class="stat-block-hr"><div class="stat-block-propriedade"><strong>Pré-requisitos:</strong> ${magia.pre_requisitos}</div><footer><cite>- ${magia.referencia}</cite></footer></article>`; }

    // Função principal de busca de dados, agora modificada
    function fetchAndRender(lang) {
        containerNomes.innerHTML = `<p><progress></progress></p>`;
        renderizarDetalhes(null);
        inputBusca.value = '';
        
        // Pega o valor ATUAL do seletor de ordenação
        const sortBy = seletorOrdenacao.value;
        
        // Adiciona o critério de ordenação como um parâmetro na URL
        fetch(`/api/magias/${lang}?sort=${sortBy}`)
            .then(response => response.json())
            .then(data => {
                todasAsMagias = data;
                // Apenas popula os filtros se eles estiverem vazios
                if (filtroEscola.options.length <= 1) {
                    popularFiltros();
                }
                aplicarFiltros();
            });
    }
    
    // ... (cole aqui a parte do containerNomes.addEventListener)
    containerNomes.addEventListener('click', (e) => { if (e.target.classList.contains('item-lista')) { e.preventDefault(); const idMagia = parseInt(e.target.dataset.id, 10); const magiaSelecionada = todasAsMagias.find(m => m.id === idMagia); if (itemAtivo) itemAtivo.classList.remove('active'); itemAtivo = e.target; itemAtivo.classList.add('active'); renderizarDetalhes(magiaSelecionada); } });

    // Adiciona os eventos para os filtros e para o NOVO seletor de ordenação
    inputBusca.addEventListener('input', aplicarFiltros);
    filtroEscola.addEventListener('change', aplicarFiltros);
    filtroTipo.addEventListener('change', aplicarFiltros);
    seletorOrdenacao.addEventListener('change', () => {
        const langAtivo = document.querySelector('#seletor-idioma button.active').dataset.lang;
        fetchAndRender(langAtivo); // Refaz a busca com a nova ordenação
    });
    
    // ... (cole aqui a parte do botoesIdioma.forEach e themeSwitcher.forEach)
    botoesIdioma.forEach(botao => { botao.addEventListener('click', () => { const lang = botao.dataset.lang; botoesIdioma.forEach(b => b.classList.remove('active')); botao.classList.add('active'); fetchAndRender(lang); }); });
    themeSwitcher.forEach(switcher => switcher.addEventListener('change', () => { htmlElement.setAttribute('data-theme', switcher.value); }));

    // --- CARGA INICIAL ---
    document.querySelector('button[data-lang="pt"]').classList.add('active');
    fetchAndRender('pt');
});