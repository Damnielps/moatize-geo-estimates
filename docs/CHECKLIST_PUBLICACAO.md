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
      (`/Users/<usuário>`), arquivos de credencial (`.env`, `.pem`, `service_account*`)
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
      então usava o e-mail pessoal do titular. Como não havia
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

- [x] **Licenças no lugar.** Três arquivos:
      - `LICENSE` (MIT para código; remete a `LICENSE-DADOS.md` para dados)
      - `LICENSE-DADOS.md` (novo) — CC BY 4.0 com tabela de exceções por camada
      - `CITATION.cff` (YAML, CFF 1.2.0, adicionado e validado nesta sessão)
      **Verificado pela sessão em 2026-09-11.**

- [ ] **ORCID confirmado pelo titular.** Campo `orcid` em `CITATION.cff` e `.zenodo.json`
      contém "https://orcid.org/0000-0002-6632-3991". ORCID é o mesmo registrado no
      projeto irmão `urban-canaa`. **Ação pendente:** titular confirma por e-mail
      o e-mail pessoal, que é o identificador pessoal vigente antes do push.

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
      chaves ou outro segredo. **Verificado pela sessão em 2026-09-11:** arquivos
      alterados: `LICENSE`, `README.md`, `CITATION.cff`, `.zenodo.json` (atualizados);
      `LICENSE-DADOS.md` (novo); `docs/CHECKLIST_PUBLICACAO.md` (este arquivo).

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

## Procedimento de DOI (Zenodo)

1. **Pré-requisito:** repositório público em `github.com/Damnielps/moatize-geo-estimates`.

2. **Ativar no Zenodo** (faça uma única vez):
   - Acesse [zenodo.org/account/settings/github/](https://zenodo.org/account/settings/github/)
   - Localize `Damnielps/moatize-geo-estimates`
   - Mude o toggle para **ON**
   - Zenodo começará a monitorar releases neste repositório (para releases futuras)

3. **Criar release no GitHub** (para gerar DOI):
   - Em `github.com/Damnielps/moatize-geo-estimates`, vá a *Releases* → *Draft a new release*
   - Tag: `v1.0.0` (semver, começa em 1.0.0 para primeiro release)
   - Title: `Release v1.0.0 — Primeira publicação`
   - Body: listar as fases fechadas, datasets inclusos, limitações conhecidas (copiar de
     `ORCHESTRATION_LOG.md`)
   - Clique em *Publish release*
   - GitHub criará uma tag e acionará o webhook para o Zenodo

4. **Zenodo arquiva automaticamente**:
   - Após ~5 min, acesse [zenodo.org/account/settings/github/](https://zenodo.org/account/settings/github/)
   - Você verá um novo depósito sob "Upload" com título automático
   - O depósito terá dois DOIs:
     - **DOI conceitual** (sempre resolve para versão mais recente): `10.5281/zenodo/XXXXXX`
     - **DOI de versão** (específico de v1.0.0): `10.5281/zenodo/YYYYYY`

5. **Propagador o DOI nos metadados** (editar **antes** de arquivar do Zenodo):
   - No Zenodo, no depósito editável (antes de publicar), atualize metadados se necessário
   - Depois de arquivar, os DOIs são fixos; volte ao repositório GitHub e faça um novo commit:

   ```bash
   # Editar CITATION.cff
   # - Adicionar campo identifiers (se não houver)
   # - Adicionar seção preferred-citation.doi com o DOI conceitual
   ```

   Exemplo `CITATION.cff` após a release:
   ```yaml
   doi: "10.5281/zenodo.XXXXXX"  # DOI conceitual
   identifiers:
     - type: doi
       value: "10.5281/zenodo.XXXXXX"
       description: "DOI conceitual no Zenodo (todas as versões)"
     - type: doi
       value: "10.5281/zenodo.YYYYYY"
       description: "DOI da versão v1.0.0 no Zenodo"
   preferred-citation:
     type: dataset
     doi: "10.5281/zenodo.XXXXXX"
   ```

6. **Verificar `.zenodo.json`**:
   - Arquivo já tem `"creators"`, `"license": "CC-BY-4.0"`, `"related_identifiers"`
   - Nenhuma alteração necessária após a release

7. **Atualizar `README.md` e `app/`**:
   - Remova o comentário `<!-- selo DOI: inserir após a release no Zenodo -->`
   - Adicione logo acima: `[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXX)`
   - Em `app/src/lib/publicacao.js` (se houver), atualize a constante `DATASET_DOI = "10.5281/zenodo.XXXXXX"`
   - Em `app/index.html`, seção JSON-LD, atualize `"url": "https://doi.org/10.5281/zenodo.XXXXXX"`

8. **Commit e push final**:
   ```bash
   git add CITATION.cff README.md app/src/lib/publicacao.js app/index.html
   git commit -m "Adiciona DOI do Zenodo (10.5281/zenodo.XXXXXX)"
   git push origin main
   ```
   - O workflow `publicar.yml` reconstrói e redeploya o app automaticamente

---

Assinatura do titular: **Daniel Pessini Sobreira** — data: ______________
