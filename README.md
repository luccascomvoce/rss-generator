# 📡 rss-generator

Gerador automático de feeds RSS para sites que não possuem feed oficial.  
Roda via **GitHub Actions** a cada hora e publica os feeds como arquivos estáticos via **GitHub Pages**.

## Como funciona

```
GitHub Actions (cron: 1h)
  └── engine/run.py
        ├── lê sources/*.yml
        ├── scrapa páginas ou busca RSS existentes
        ├── deduplica por URL
        ├── gera docs/*.xml
        └── commita e publica via GitHub Pages
```

## Como usar (fork)

1. Faça **fork** deste repositório
2. Ative o **GitHub Pages** nas configurações do repo (branch `main`, pasta `/docs`)
3. Adicione um arquivo `.yml` em `sources/` descrevendo sua fonte (veja exemplos)
4. O workflow roda automaticamente a cada hora

Seus feeds estarão disponíveis em:
```
https://<seu-usuario>.github.io/<nome-do-repo>/<id-da-fonte>.xml
```

## Estrutura do repositório

```
rss-generator/
├── .github/workflows/generate-feeds.yml   ← workflow agendado
├── sources/                               ← configs das fontes (adicione as suas aqui)
│   ├── prefeitura-blumenau.yml            ← exemplo: scraping HTML
│   ├── camara-blumenau.yml                ← exemplo: scraping HTML
│   └── defesa-civil-sc.yml               ← exemplo: passthrough de RSS existente
├── engine/
│   ├── run.py                             ← ponto de entrada
│   ├── scraper.py                         ← baixa e extrai itens da página
│   ├── feed_builder.py                    ← gera o XML RSS
│   └── deduplicator.py                    ← evita itens repetidos
├── state/seen/                            ← histórico por fonte (versionado)
├── docs/                                  ← feeds gerados (servidos via GitHub Pages)
└── requirements.txt
```

## Configurando uma fonte (sources/*.yml)

### Fonte por scraping HTML

```yaml
id: minha-fonte
title: "Nome do Feed"
description: "Descrição do feed"
url: https://exemplo.com/noticias
feed_output: minha-fonte.xml
type: scrape

selectors:
  items: "article, li.news-item"    # seletor CSS dos itens
  title: "h2, h3, .titulo"          # seletor do título dentro de cada item
  link: "a"                         # seletor do link dentro de cada item
  date: "time, .data"               # seletor da data (opcional)
  summary: "p, .resumo"             # seletor do resumo (opcional)

link_prefix: "https://exemplo.com"  # prefixo para links relativos (opcional)
max_items: 30                       # máximo de itens por execução
```

### Fonte por passthrough de RSS existente (com filtro opcional)

```yaml
id: minha-fonte-rss
title: "Nome do Feed Filtrado"
description: "Apenas itens relacionados ao meu tema"
rss_url: https://exemplo.com/feed.rss
feed_output: minha-fonte-rss.xml
type: rss

filter_keywords:              # itens sem nenhuma dessas palavras são descartados
  - "Palavra Chave 1"
  - "Palavra Chave 2"

max_items: 30
```

## Variáveis de ambiente (opcionais)

Nenhuma variável obrigatória. O projeto funciona sem secrets.  
Para fontes que exigem User-Agent customizado, edite `engine/scraper.py`.

## Dependências

- Python 3.12+
- `requests`, `beautifulsoup4`, `feedgen`, `PyYAML`, `python-dateutil`

## Licença

MIT
