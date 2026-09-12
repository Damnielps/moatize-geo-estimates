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
      **Reexecutado em 2026-09-11 (gitleaks 8.30.1), a pedido do titular, em quatro
      passadas:** (1) `gitleaks git . --log-opts=--all` — 8 commits, 530 MB, inclusive a
      branch local com o histórico anterior à reescrita: *no leaks found*; (2)
      `gitleaks dir .` sobre a árvore inteira — 905 MB: *no leaks found*; (3)
      `gitleaks dir` sobre uma cópia de `app/dist` (o build publicado) — 31 MB: *no
      leaks found*; (4) passada com **regras próprias de dado pessoal** (e-mail, caminho
      `/Users/<usuário>`, CPF, telefone), porque gitleaks procura credenciais e não PII —
      9 achados, discutidos no item abaixo.

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

- [x] **Rodapé/aviso de fonte em todas as visualizações.** Amostrar mapa, população,
      gráficos, narrativa, artigo e metodologia: todas devem trazer a atribuição às
      fontes (WSF Evolution/DLR, GHSL/JRC, HDX, classificação própria) — hoje presente
      no rodapé fixo do app (`app/src/App.jsx`, componente `Rodape`) e no rodapé
      estático de `app/index.html` (visível antes do React montar).
      **Verificado pela sessão em 2026-09-11, no site publicado:** `<Rodape />` está
      fora de `<Routes>` em `App.jsx`, portanto vale para as sete rotas (início, mancha,
      província, população, gráficos, artigo, metodologia); o texto
      (`rodape_atribuicao_sufixo`, PT e EN) nomeia classificação própria
      (Landsat/Sentinel-2), WSF Evolution (DLR), GHSL (JRC) e COD-AB/COD-PS (HDX), mais
      a ressalva "nenhuma leitura causal... sem o veredito da Fase 3".

- [x] **Licenças no lugar.** Três arquivos:
      - `LICENSE` (MIT para código; remete a `LICENSE-DADOS.md` para dados)
      - `LICENSE-DADOS.md` (novo) — CC BY 4.0 com tabela de exceções por camada
      - `CITATION.cff` (YAML, CFF 1.2.0, adicionado e validado nesta sessão)
      **Verificado pela sessão em 2026-09-11.**

- [ ] **ORCID confirmado pelo titular.** Campo `orcid` em `CITATION.cff` e `.zenodo.json`
      contém "https://orcid.org/0000-0002-6632-3991". ORCID é o mesmo registrado no
      projeto irmão `urban-canaa`. **Ação pendente:** só o titular pode confirmar que o
      ORCID é o seu; a sessão não tem como verificar isso.
      **O que a sessão verificou em 2026-09-11:** o identificador é o mesmo nos cinco
      arquivos que o declaram (`CITATION.cff`, `.zenodo.json`, `README.md`, o JSON-LD de
      `app/index.html` e `app/src/lib/publicacao.js`), passa no dígito verificador
      mod 11-2 da especificação do ORCID, e agora **aparece na tela** — o bloco "Como
      citar" do rodapé mostra "Autor: ... · ORCID ..." com link para `orcid.org`, em PT e
      em EN, conferido no app construído. Contratos em `pipeline/tests/test_publicacao.py`.

- [x] **`SITE_URL`/`BASE_PATH` corretos.** Destino decidido em 2026-09-09: repositório
      `github.com/Damnielps/moatize-geo-estimates`, página de **projeto** (não de
      usuário/organização). Variáveis em
      *Settings → Secrets and variables → Actions → Variables*:
      - `SITE_URL` = `https://Damnielps.github.io/moatize-geo-estimates`
      - `BASE_PATH` = `/moatize-geo-estimates/`
      **Resolvido e verificado pela sessão em 2026-09-11:** o repositório existe, as
      variáveis foram configuradas pelo titular e o site responde. Conferido no ar:
      `<link rel="canonical">`, `og:url` e o JSON-LD trazem
      `https://Damnielps.github.io/moatize-geo-estimates/`; os dois assets
      (`assets/index-*.js`, `assets/index-*.css`) e `sitemap.xml`, `robots.txt`,
      `favicon.svg`, `404.html` respondem 200; nenhum `__SITE_URL__` e nenhum
      `EXEMPLO.invalid` no build servido.

- [x] **`git status` mostra só o esperado.** Antes do primeiro push, conferir que os
      arquivos novos/alterados são exatamente os documentados (dados de
      `data/processed`, app, workflows, licenças, README etc.) — nada de `.env`,
      chaves ou outro segredo. **Verificado pela sessão em 2026-09-11:** arquivos
      alterados: `LICENSE`, `README.md`, `CITATION.cff`, `.zenodo.json` (atualizados);
      `LICENSE-DADOS.md` (novo); `docs/CHECKLIST_PUBLICACAO.md` (este arquivo).

- [x] **Exposição residual do e-mail pessoal nos commits antigos — aceita pelo titular.**
      **Diagnóstico (verificado em 2026-09-11).** A `main` publicada está limpa. O que
      não está: a reescrita de histórico de 4b-29 moveu `main`, mas não apagou os objetos
      do servidor. As seis `refs/pull/1..6/head` — PRs fechados do dependabot — têm
      **todas o commit `dc0673b` como pai**, e por isso seguravam o histórico antigo
      inteiro. A API do GitHub entrega esses commits a quem tenha o SHA, e um deles
      devolve `fetch_osm_reassentamentos.sh` com o e-mail pessoal em texto. `refs/pull/*`
      é do lado do servidor: **nenhum push do dono a remove.**

      **Por que apagar e recriar o repositório é a saída, e não um exagero.** As duas
      únicas opções são pedir ao suporte do GitHub que remova as refs obsoletas, ou
      apagar e recriar. O custo que normalmente torna a segunda inaceitável — perder
      estrelas, forks, issues, discussões e histórico de PRs — **aqui é zero**, medido na
      API em 2026-09-11: 0 estrelas, 0 forks, 0 watchers, 0 subscribers, 0 issues, e os
      únicos 6 PRs são bumps fechados do dependabot — isto é, exatamente aquilo que
      ancora a exposição. O repositório foi criado em 2026-09-09. A URL do Pages não
      muda (mesmo dono, mesmo nome), então nenhum link publicado quebra, e o Zenodo ainda
      não arquivou nada.

      **Decisão do titular, 2026-09-11: não eliminar.** Depois do diagnóstico e com o
      runbook pronto, o titular desistiu de apagar e recriar o repositório. A exposição
      fica, e fica **declarada aqui** em vez de esquecida: os commits antigos seguem
      recuperáveis por quem tenha o SHA, e o que eles contêm é um endereço de e-mail
      pessoal — não uma credencial, nada que se possa usar para agir em nome do titular.
      Nenhum segredo, chave ou token foi exposto em momento algum (gitleaks verde no
      histórico, na árvore e no build). Se mudar de ideia, os passos abaixo continuam
      válidos, e `scripts/verificar_exposicao.py` continua sendo a prova de que funcionou.

      **Passos, se e quando o titular quiser executá-los (exigem a conta do GitHub).**
      1. Confirmar o backup: espelho do histórico limpo em
         `~/Documents/Code/estudos-pesquisa/moatize-geo-estimates-backup-20260911.git`
         (criado nesta sessão, `git clone --mirror`, `main` em `6b8c3e7`). O clone de
         trabalho também é cópia completa.
      2. GitHub → o repositório → *Settings* → *General* → *Danger Zone* →
         **Delete this repository**.
      3. Criar de novo com o **mesmo nome**, `moatize-geo-estimates`, **público** e
         **vazio** — sem README, sem .gitignore, sem licença (qualquer arquivo inicial
         cria um commit que conflita com o push).
      4. `git push -u origin main` a partir deste clone (o remoto não muda).
      5. *Settings* → *Pages* → *Source*: **GitHub Actions**.
      6. *Settings* → *Secrets and variables* → *Actions* → *Variables*: recriar
         `SITE_URL` e `BASE_PATH` com os valores acima. Sem elas o job `construir` cai no
         placeholder e o site publica com URL errada.
      7. Verificar: `uv run python scripts/verificar_exposicao.py` — **rc=0 e "LIMPO"**.
         O script consulta o servidor (não a árvore local): nenhuma referência remota
         aponta para commit descartado, nenhum descartado resolve na API, e toda
         `refs/pull/*` que exista nasce do histórico de `main`. Um erro de rede devolve
         rc=2 (inconclusivo), nunca "limpo".
      8. Aguardar o `Publicar` e reconferir o site no ar.

      Os SHAs descartados e o mapeamento antigo→novo estão em
      `config/commits_obsoletos.yaml`, com a confiança de cada correspondência declarada.
      Dependabot voltará a abrir PRs; as refs novas nascerão do histórico limpo e são
      inofensivas — o passo 7 continua provando isso a cada execução.

- [ ] **Endereço institucional de terceiro no acervo publicado.** A passada de PII achou
      `dpa@ine.gov.mz` (contato público da Direcção de Planificação do INE de
      Moçambique) em `data/_reprovado/0p-demograficas/FASE0_DEMOGRAFICAS_SUMMARY.md`,
      commit `ad468af`, alcançável a partir de `main`. Não é dado do titular e o INE o
      publica, mas está numa nota de trabalho reprovada. Decidir se sai do acervo
      publicado.

## Depois do primeiro deploy

- [x] **GitHub Pages com HTTPS** ativo (Settings → Pages do repositório). Domínios
      `*.github.io` sem domínio próprio são servidos em HTTPS por padrão.
      **Verificado pela sessão em 2026-09-11:** o workflow `Publicar` concluiu com
      sucesso em `96225aa` e `https://Damnielps.github.io/moatize-geo-estimates/`
      responde 200 em HTTPS. Percorridas no site publicado as abas Início (mapa de
      scrollytelling desenhando), Mancha e pegadas (11 camadas, 30 requisições de dados,
      todas 200), Província e cidades e Metodologia: **zero erro de console e zero
      requisição falha**.
- [ ] **Google Search Console**: propriedade verificada; confirmar em *Sitemaps* que
      `sitemap.xml` foi enviado. Como o app é uma página única com `HashRouter`, o
      sitemap lista só a URL raiz (ver `app/public/sitemap.xml`) — não há URLs por seção
      para indexar separadamente.
- [ ] **Bing Webmaster Tools**: propriedade verificada; confirmar `sitemap.xml` listado.
- [ ] **Descrição e tópicos do repositório GitHub** preenchidos (`homepage` apontando
      para a URL do GitHub Pages, `topics` como `mozambique`, `mining`, `urbanization`,
      `remote-sensing` etc.).
      **Parcial, verificado na API em 2026-09-11:** `description` e `homepage`
      (`https://damnielps.github.io/moatize-geo-estimates/`) gravados; **`topics` continua
      vazio** — no diálogo do About cada tópico só é aceito com Enter antes de salvar.
      Sem tópicos o repositório não aparece nas buscas por tema, que é a razão do item.

## Procedimento de DOI (Zenodo) — **executado em 2026-09-11**

DOIs emitidos, conferidos na API do Zenodo (`zenodo.org/api/records/22718198`):

| | DOI |
|---|---|
| **Conceitual** — resolve sempre para a versão mais recente; é o que se cita | `10.5281/zenodo.22718197` |
| **Versão v1.0.0** — o snapshot arquivado | `10.5281/zenodo.22718198` |

O badge que a página de settings do Zenodo mostra é o **da versão**, não o conceitual;
os dois são distintos e a citação usa o conceitual. O depósito leu `.zenodo.json`
corretamente: título, autor com ORCID `0000-0002-6632-3991` e licença CC BY 4.0.

Propagação feita por `uv run python scripts/definir_doi.py 10.5281/zenodo.22718197
--doi-versao 10.5281/zenodo.22718198` + `npm --prefix app run build`; `--verificar`
devolve rc=0, e o `CITATION.cff` resultante valida no esquema CFF 1.2.0.

O passo a passo abaixo fica como registro do procedimento, para a próxima versão.

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

5. **Propagar o DOI para os quatro arquivos que o publicam — um comando, não quatro
   edições à mão** (acrescentado em 2026-09-11; a versão anterior deste checklist
   mandava editar `CITATION.cff`, `README.md`, `publicacao.js` e `index.html` um a um,
   e basta um ficar para trás para o painel citar um DOI e o `CITATION.cff` citar outro):

   ```bash
   uv run python scripts/definir_doi.py 10.5281/zenodo.XXXXXX --doi-versao 10.5281/zenodo.YYYYYY
   ```

   O script valida a forma do DOI, localiza todas as âncoras e só então grava (se
   alguma faltar, **nada** é escrito e o rc é 2); é idempotente; e reexecutar com outro
   DOI substitui o anterior em vez de acumular. `--verificar` informa o estado sem
   escrever. Os contratos estão em `pipeline/tests/test_publicacao.py`, e o
   `CITATION.cff` que ele gera foi validado contra o esquema CFF 1.2.0 (`cffconvert`).

6. **Verificar `.zenodo.json`**:
   - Arquivo já tem `"creators"`, `"license": "CC-BY-4.0"`, `"related_identifiers"`
   - Nenhuma alteração necessária após a release

7. **Reconstruir o app** para o DOI chegar ao site (o script não constrói sozinho):

   ```bash
   npm --prefix app run build
   ```

   O bloco "Como citar" passa a mostrar o DOI no lugar da URL, a nota "sem DOI ainda"
   desaparece e o rodapé ganha o link `doi.org`. Confirme com
   `uv run python scripts/definir_doi.py --verificar` (rc=0) e `uv run pytest -q`.

8. **Commit e push final**:
   ```bash
   git add CITATION.cff README.md app/src/lib/publicacao.js app/index.html
   git commit -m "Adiciona DOI do Zenodo"
   git push origin main
   ```
   - O workflow `publicar.yml` reconstrói e redeploya o app automaticamente

---

Assinatura do titular: **Daniel Pessini Sobreira** — data: ______________
