# Anonimização Sintática por Generalização

Trabalho 1 da disciplina **Privacidade de Dados** (2026.2) — implementação de um
algoritmo de anonimização por **generalização**, aplicado ao dataset `covid.csv`.

**Autores:** Monique Damasceno e Diego Lopes

## Objetivo

Reduzir o risco de reidentificação de indivíduos no dataset generalizando dois
atributos quase-identificadores — `municipioCaso` e `dataNascimento` — em
diferentes níveis de detalhe, e gerar datasets de publicação (`DT_nm_nd.csv`)
junto com histogramas que mostram o efeito da generalização em cada nível.

## Estrutura do projeto

```
Anonimização Sintatica/
├── dataset/
│   ├── covid.csv                  # dataset original
│   └── map_municipio_regiao.csv   # mapeamento município → região (CE)
├── hierarquia.py                  # construção das hierarquias de generalização
├── anonimizacao.py                # laço principal: gera DT_nm_nd.csv e histogramas
└── README.md
```

## Requisitos

- Python 3
- Bibliotecas: `pandas`, `matplotlib`

Instalação das dependências:

```
pip install pandas matplotlib
```

## Como executar

Basta rodar o módulo principal — ele já importa e constrói as hierarquias
internamente, não é necessário rodar `hierarquia.py` separadamente:

```
python anonimizacao.py
```

O programa primeiro gera os histogramas do dataset original (nível 0) e depois
entra em um laço, pedindo dois níveis de generalização:

```
Nível de generalização para municipioCaso (0-2, -1 para sair): 1
Nível de generalização para dataNascimento (0-3, -1 para sair): 2
```

Para cada par `(nm, nd)` informado, o programa gera:

- `DT_<nm>_<nd>.csv` — dataset publicado, com os dois atributos generalizados
  para os níveis escolhidos
- `HIST_municipioCaso_<nm>.png` e `HIST_dataNascimento_<nd>.png` — histogramas
  dos valores generalizados

Para encerrar o laço, digite `-1` para os dois níveis.

O arquivo `hierarquia.py` também pode ser executado sozinho
(`python hierarquia.py`), útil apenas para conferir manualmente o conteúdo das
hierarquias sem rodar o pipeline completo.

## Hierarquias de generalização

### `municipioCaso` (3 níveis)

| Nível | Conteúdo                              | Exemplo            |
|-------|----------------------------------------|---------------------|
| 0     | Município original                     | Fortaleza           |
| 1     | Região do município                    | Grande Fortaleza    |
| 2     | Estado (fixo — todo o dataset é do CE) | Ceará               |

O mapeamento de município para região vem de `map_municipio_regiao.csv`. Nomes
de município são comparados sem acento (ex.: "Baturité" e "Baturite" são
tratados como o mesmo município) para evitar divergências de grafia entre os
dois arquivos.

### `dataNascimento` (4 níveis)

| Nível | Conteúdo               | Exemplo       |
|-------|-------------------------|---------------|
| 0     | Data completa            | 1991-11-13    |
| 1     | Mês/ano                  | 11/1991       |
| 2     | Ano                       | 1991          |
| 3     | Faixa de 5 anos           | 1991-1995     |

Registros com `municipioCaso` ou `dataNascimento` vazios, ou sem
correspondência na hierarquia de município, são excluídos do dataset final,
conforme pedido no enunciado.

## Observações

- O dataset original tem 128.370 registros e 184 municípios distintos; todos
  os municípios possuem correspondência válida no arquivo de mapeamento.
- No histograma de `municipioCaso` nível 0, os rótulos do eixo X são ocultados
  por haver muitos municípios distintos, dificultando a leitura.