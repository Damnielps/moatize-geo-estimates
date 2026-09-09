# Checklist de publicação

Checklist para o titular do projeto (Daniel Pessini Sobreira) assinar (marcar e datar)
antes do **primeiro push** para um repositório público e a cada **atualização de
dados**. Molde adaptado de `atlas-migração/docs/CHECKLIST_PUBLICACAO.md` — mas este
projeto **não** usa microdados de acesso controlado (só fontes de nível A, CLAUDE.md
§4.0), então os itens sobre termo de uso/finalidade do IBGE daquele checklist não se
aplicam aqui e foram substituídos pelos equivalentes deste projeto.

Nenhum item aqui é verificável por uma sessão do Claude Code sozinha quando depende de
uma decisão que só o titular pode tomar (licença de código, e-mail dos commits, DOI).
Marcar um item como concluído é uma declaração do titular, não uma checagem automática —
exceto onde anotado "verificado pela sessão", que registra o que uma sessão já conferiu.

## Antes do primeiro push (repositório se torna público)

- [x] **Apenas fontes de nível A sustentam números publicados.** `data/DATA_AUDIT.md`
      emitiu o veredito de abertura da Fase 1 e documenta, fonte a fonte, o nível A/B/C.
      **Ressalva registrada no próprio `DATA_AUDIT.md` (revisão de 2026-09-08, ADR
      0012–0014):** a classificação de `cultivo_sequeiro` tem desempenho pior que
      aleatório (kappa −0,065) e H5/H6/P8 foram rebaixadas — isso é uma limitação de
      **desempenho do classificador**, não de licença/nível da fonte, e já está refletido
      no rodapé do app ("nenhuma leitura causal... sem o veredito da Fase 3").
      **Confirmar antes de publicar:** que a versão do app no momento do push mostra
      essas ressalvas de forma acessível (aba Metodologia/Artigo), não só em `DATA_AUDIT.md`.

- [x] **Nenhum dado de nível B versionado.** `git ls-files | grep -Ei
      'ipums|nicfi|dhs_microdata'` e a mesma busca em `git log --all --name-only`
      retornam vazio (job `verificar` do CI repete isso a cada push).
      **Verificado pela sessão em 2026-09-09.**

- [x] **`gitleaks` verde.** Rodado nesta sessão em duas passadas: (1)
      `gitleaks detect --source .` sobre o histórico do git (1 commit, ~11 MB) —
      "no leaks found"; (2) `gitleaks detect --no-git` sobre uma cópia exata de tudo
      que `git add -A` incluiria (rastreados + não-ignorados, 1.116 arquivos, ~345 MB,
      respeitando `.gitignore` via `git ls-files --cached --others --exclude-standard`)
      — "no leaks found". `.gitleaks.toml` só abre exceção para os sidecars
      `*.sha256`/`*.meta.json` (checksums de integridade, não segredos).
      **Verificado pela sessão em 2026-09-09.** Repetir sempre que novos arquivos forem
      adicionados antes de um push (o job `verificar` do `publicar.yml` cobre o
      histórico do git a cada push, mas não escaneia arquivos ainda não commitados).

- [x] **Varredura manual complementar de dados sensíveis** (além de segredos/chaves,
      que o gitleaks já cobre): padrões de e-mail pessoal, CPF, caminho local
      (`/Users/danielpessini`), arquivos de credencial (`.env`, `.pem`, `service_account*`)
      e nomes individualizados de domicílios reassentados — nenhum encontrado, com uma
      correção aplicada: `pipeline/00_fetch/fetch_osm_reassentamentos.sh` tinha o e-mail
      pessoal do titular hardcoded no `User-Agent` de contato exigido pela política da
      API do OSM (Nominatim/Overpass); trocado por uma URL do repositório, no mesmo
      padrão já usado em `fetch_osm_contexto.py`. **Verificado pela sessão em 2026-09-09.**

- [x] **Nenhum arquivo de `data/raw`/`data/interim` fora do padrão de sidecars no
      histórico do git.** A regex do job `verificar` (`publicar.yml`) rodada contra
      `git log --all --name-only` do histórico real: só `.sha256`, `.meta.json` e
      `.gitkeep` aparecem em `data/raw/`; nada em `data/interim/`; nenhum `.tif` em
      `data/processed/`. **Verificado pela sessão em 2026-09-09** — histórico tem só
      1 commit até agora, então esta checagem é barata; repetir a cada nova fase antes
      de commitar, porque remover num commit novo não apaga do histórico.

- [x] **E-mail dos commits.** Corrigido nesta sessão: o único commit existente até
      então usava `damniel@gmail.com` (e-mail pessoal do titular). Como não havia
      remote configurado (`git remote -v` vazio) e portanto nenhum histórico publicado
      para quebrar, a sessão fez um backup (clone espelho para fora do repositório +
      `git stash push -u` das mudanças não commitadas) e reescreveu autor/committer com
      `git filter-repo --mailmap` para `Daniel Pessini Sobreira
      <129672935+Damnielps@users.noreply.github.com>`; `user.email` local também foi
      atualizado para os próximos commits. **Verificado pela sessão em 2026-09-09:**
      `git log --all --format='%ae' | sort -u` retorna só o e-mail no-reply.

- [ ] **Rodapé/aviso de fonte em todas as visualizações.** Amostrar mapa, população,
      gráficos, narrativa, artigo e metodologia: todas devem trazer a atribuição às
      fontes (WSF Evolution/DLR, GHSL/JRC, HDX, classificação própria) — hoje presente
      no rodapé fixo do app (`app/src/App.jsx`, componente `Rodape`) e no rodapé
      estático de `app/index.html` (visível antes do React montar).

- [x] **Licenças no lugar.** `LICENSE` (MIT para código; CC-BY-4.0 para
      `data/processed/`, no mesmo arquivo — decisão já tomada em `LICENSE` e no
      `README.md`) e `CITATION.cff` (adicionado nesta sessão) existem na raiz.
      **Confirmação da licença de código pelo titular:** o `LICENSE` já define MIT;
      confirmar antes do push que essa continua sendo a escolha (ou trocar).

- [ ] **`SITE_URL`/`BASE_PATH` corretos.** Destino decidido em 2026-09-09: repositório
      `github.com/Damnielps/moatize-geo-estimates`, página de **projeto** (não de
      usuário/organização). ⚠️ **Falta apenas criar o repositório e configurar as
      variáveis** (a sessão não tem acesso à conta do GitHub do titular) — em
      *Settings → Secrets and variables → Actions → Variables*:
      - `SITE_URL` = `https://Damnielps.github.io/moatize-geo-estimates`
      - `BASE_PATH` = `/moatize-geo-estimates/`
      Até lá, `app/vite.config.js` e `.github/workflows/publicar.yml` caem no
      placeholder `https://EXEMPLO.invalid` (RFC 2606) e o job `construir` emite um
      aviso (`::warning::`). `CITATION.cff` e `.zenodo.json` já usam a URL real.

- [ ] **`git status` mostra só o esperado.** Antes do primeiro push, conferir que os
      arquivos novos/alterados são exatamente os documentados (dados de
      `data/processed`, app, workflows, licenças, README etc.) — nada de `.env`,
      chaves ou outro segredo. `git status` no início desta sessão já mostrava um
      volume grande de arquivos modificados de fases anteriores do pipeline — revisar
      esse diff linha a linha (ou por `git add -p`) antes do primeiro commit público,
      não só os arquivos desta sessão.

## Depois do primeiro deploy

- [ ] **GitHub Pages com HTTPS** ativo (Settings → Pages do repositório). Domínios
      `*.github.io` sem domínio próprio são servidos em HTTPS por padrão.
- [ ] **Google Search Console**: propriedade verificada; confirmar em *Sitemaps* que
      `sitemap.xml` foi enviado. Como o app é uma página única com `HashRouter`, o
      sitemap lista só a URL raiz (ver `app/public/sitemap.xml`) — não há URLs por seção
      para indexar separadamente.
- [ ] **Bing Webmaster Tools**: propriedade verificada; confirmar `sitemap.xml` listado.
- [ ] **Descrição e tópicos do repositório GitHub** preenchidos (`homepage` apontando
      para a URL do GitHub Pages, `topics` como `mozambique`, `mining`, `urbanization`,
      `remote-sensing` etc.).
- [ ] **DOI no Zenodo** (opcional). `.zenodo.json` já existe na raiz com os metadados
      do depósito. Procedimento: em zenodo.org → *GitHub* → ativar o repositório
      `Damnielps/moatize-geo-estimates` **antes** de criar a release (o Zenodo só arquiva
      releases publicadas depois de ativado) → no GitHub, *Releases → Draft a new
      release* (ex.: tag `v1.0.0`) → Zenodo arquiva automaticamente e gera um DOI
      conceitual (resolve sempre para a versão mais recente) e um DOI de versão.
      Depois: adicionar um bloco `identifiers` com `type: doi` em `CITATION.cff`
      (mesmo formato do `atlas-migração/CITATION.cff`) e, se o ORCID do titular for
      conhecido, incluí-lo em `authors`.

## Procedimento de atualização de dados (a cada nova fase concluída)

Repetir sempre que `data/processed/` for regenerado (nova fase do pipeline, correção
metodológica, nova classificação):

1. Rodar a fase relevante do pipeline (`make imagery`, `make metrics`, `make agri`,
   `make causal`, conforme o Makefile) e `make app` (gera `app/src/content/` via
   `pipeline/05_app/gerar_metodologia.py`/`gerar_artigo.py` e copia dados via
   `app/scripts/sync-data.mjs`).
2. `uv run pytest -q` — contratos de dados e regressão numérica (§11.2.4) precisam
   passar antes de commitar.
3. Revisar os itens do checklist acima que mudam com os dados (rodapé/aviso ainda
   corretos, `data/DATA_AUDIT.md` refletindo o veredito atual).
4. `git add data/processed app/src/content docs/ADR/<novo, se houver>` e qualquer outro
   arquivo alterado.
5. `git commit` e `git push` para `main` — o workflow `publicar.yml` reconstrói e
   publica o app automaticamente (sem rerodar o pipeline de dados).
6. Atualizar `version` em `CITATION.cff` e, se o Zenodo estiver conectado, considerar
   uma nova release/DOI.

---

Assinatura do titular: **Daniel Pessini Sobreira** — data: ______________
