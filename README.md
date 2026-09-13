# Observatório da Aprendizagem Industrial — SENAI RS

Dashboard independente por data de leitura. Não altera nem referencia o código do dashboard anterior.

## Uso

Abra `dist/index.html` ou publique a pasta `dist` no GitHub Pages. O site não depende de serviços externos, rastreadores ou bibliotecas carregadas de terceiros.

- Data da base: cada fotografia é preservada no seletor e no Histórico.
- Modalidade: todas, aprendizagem básica ou técnica.
- Clique em uma região para abrir suas unidades e em uma unidade para abrir os cursos. O caminho no topo e “Voltar um nível” retornam à análise anterior. Atalho: Alt + seta para cima.
- Clique em um curso para abrir métricas e participação das maiores empresas, sem identificá-las.
- Vencimentos: selecione um mês e aprofunde nos territórios.
- Ordene a tabela, busque regiões/unidades/cursos e exporte o recorte em CSV.
- Os botões de informação explicam as métricas e funcionam com foco de teclado.
- O endereço mantém a data, modalidade, visão e caminho da análise.

## Fotografia inicial: 08/09/2026

Fonte: `matriculao.08.09.26.XLSX`, aba `Sheet`.

| Medida | Valor |
|---|---:|
| Registros na origem | 356.914 |
| Registros de Aprendizagem Industrial | 47.662 |
| Registros com status Matriculado | 16.289 |
| Pessoas distintas | 16.239 |
| Vínculos vigentes | 15.106 |
| Pessoas com vínculo vigente | 15.069 |
| Empresas distintas com vínculo vigente | 2.384 |
| Pessoas com matrícula sem CNPJ e sem vínculo vigente no recorte | 770 |
| Vínculos futuros | 108 |
| Vínculos encerrados | 294 |
| Registros sem região mapeada | 4 |

O estoque CAGED e o potencial MTE de setembro ainda não foram fornecidos. Market share permanece indisponível; nenhum denominador de junho é aplicado à nova base.

## Regras

Pessoa: CPF distinto; RA como alternativa quando não há CPF utilizável. Vínculo: pessoa + CNPJ normalizado + início + término. Vigência: início ≤ data-base ≤ término, com CNPJ de 14 dígitos e dígitos verificadores válidos. Inícios futuros, encerramentos e registros inválidos ficam separados. Matrícula: registro da origem com status Matriculado; não equivale necessariamente a pessoa distinta.

Empresas: CNPJs distintos de vínculos vigentes, sem código zero. Pessoas, empresas e vínculos podem aparecer em mais de um recorte; totais são calculados diretamente, não pela soma dos filhos. Na ausência de identificador contratual uniforme, a chave operacional adotada não substitui conferência documental.

Regiões: mapeamento por CODFILIAL extraído da base regional de julho de 2026. Novos códigos ficam em “Sem mapeamento regional”. Revisar reorganizações antes de comparar territórios. Não se deduz região pelo nome da unidade.

Cobertura contratual: pessoas com ao menos um vínculo vigente / pessoas matriculadas. Não confundir com market share.

Market share: vínculos vigentes / estoque CAGED da mesma competência e território. Não é mostrado em recortes sem denominador correspondente. O potencial MTE é independente; não presumir a relação TAM ≥ SAM em toda região. A simulação assume denominador fixo e informa vínculos adicionais líquidos.

## Acrescentar uma nova base

Requisitos de processamento local: Python 3 e `lxml` (ver `requirements.txt`). A planilha é lida em fluxo para limitar uso de memória. Não coloque as planilhas brutas dentro do repositório.

```text
python scripts/build_snapshot.py "CAMINHO/novabase.xlsx" --date 2026-10-08
```

O processador localiza colunas pelos nomes e interrompe caso alguma obrigatória esteja ausente. A data é obrigatória. Cada execução cria `data/snapshots/AAAA-MM-DD.json` e recompõe `dist/data.js` com todas as fotografias. Não sobrescreve uma data existente sem `--replace` explícito. Novas colunas ou mudanças nas regras exigem revisão e incremento da versão das regras.

Para acrescentar mercado compatível:

```text
python scripts/build_snapshot.py "CAMINHO/novabase.xlsx" --date 2026-10-08 --market "CAMINHO/mercado.json"
```

O arquivo de mercado deve ter `competence` (AAAA-MM), `source` (descrição da fonte), `state` (objeto com `caged` e, opcionalmente, `mte`) e `regions` (mapa de nome regional para denominadores). Valores devem ser numéricos não negativos. Não inventar valores para preencher campos. A competência diferente é rejeitada, e regiões desconhecidas interrompem o processamento. Para corrigir uma fotografia existente após receber CAGED, use a mesma data e `--replace` deliberadamente. O denominador pode ser atualizado separadamente com `scripts/update_market.py`.

## Validação e publicação

```text
python scripts/test_snapshot.py
node --check dist/app.js
```

O fluxo GitHub Actions publica apenas `dist`. Em Settings → Pages, configure a origem como GitHub Actions. Nenhuma planilha, CPF, RA, contato ou CNPJ individual integra a publicação. Os arquivos agregados são públicos: não constituem controle de acesso à informação publicada.

Os testes cobrem pessoas/contratos distintos, CNPJ zero, vigência nas datas-limite, datas inválidas, competência de mercado e reconciliação dos vencimentos.
