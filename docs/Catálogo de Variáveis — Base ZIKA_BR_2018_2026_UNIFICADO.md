

# **Catálogo de Variáveis — Base ZIKA\_BR\_2018\_2026\_UNIFICADO**

## **Sobre a base**

Esta base reúne **236.398 registros** de notificações de **Zika** no Brasil entre **2018 e 2026**, provenientes do **SINAN (Sistema de Informação de Agravos de Notificação)** do Ministério da Saúde. Cada linha representa uma **ficha de notificação individual**.

Os nomes das colunas seguem o padrão oficial do SINAN — abreviações de no máximo 10 caracteres herdadas do formato `.dbc` (DBase comprimido) usado pelo DATASUS. Por isso são pouco intuitivos: `SG_UF` significa "Sigla da Unidade Federativa", `DT_NOTIFIC` significa "Data da Notificação", e assim por diante. A maioria dos campos categóricos é **codificada numericamente** — a tabela abaixo traduz todos esses códigos.

## **Descrição das colunas**

| Coluna | Nome completo | Descrição |
| ----- | ----- | ----- |
| `arquivo_origem` | Arquivo de origem | Nome do arquivo `.dbc` de origem do registro (ex.: `ZIKABR18.dbc`). **Coluna adicionada na unificação**, não faz parte do SINAN original. Útil para rastrear de qual ano-base veio o dado. |
| `ano_arquivo` | Ano do arquivo de origem | Ano do arquivo `.dbc` (2018 a 2026). **Coluna adicionada na unificação.** Não é necessariamente o ano em que o caso ocorreu — um caso de 2019 pode aparecer no arquivo de 2020 se a notificação foi tardia. |
| `TP_NOT` | Tipo de notificação | Sempre `2` nesta base \= Notificação Individual (padrão SINAN). |
| `ID_AGRAVO` | Código do agravo (CID-10) | `A92.` ou `A928` \= Febre pelo vírus Zika. Códigos da Classificação Internacional de Doenças, 10ª revisão. |
| `CS_SUSPEIT` | Caso suspeito | Campo em geral vazio nesta base; quando preenchido, identifica suspeita inicial. |
| `DT_NOTIFIC` | Data da notificação | Data em que o caso foi notificado ao SINAN (formato AAAA-MM-DD). |
| `SEM_NOT` | Semana epidemiológica da notificação | Semana do ano (1 a 53\) em que ocorreu a notificação. Padrão epidemiológico usado mundialmente para vigilância. |
| `NU_ANO` | Ano da notificação | Ano em que a notificação foi registrada. |
| `SG_UF_NOT` | UF de notificação | Código IBGE de 2 dígitos da UF onde foi notificado (ex.: 35 \= SP, 33 \= RJ, 15 \= PA). |
| `ID_MUNICIP` | Município de notificação | Código IBGE de 6 ou 7 dígitos do município de notificação. |
| `ID_REGIONA` | Regional de saúde de notificação | Código da regional de saúde da unidade notificadora. |
| `DT_SIN_PRI` | Data dos primeiros sintomas | Quando o paciente começou a sentir sintomas. **É a data mais importante epidemiologicamente** — usada para construir curvas epidêmicas. |
| `SEM_PRI` | Semana epidemiológica dos primeiros sintomas | Semana do ano correspondente a `DT_SIN_PRI`. |
| `NU_IDADE_N` | Idade codificada | Campo composto: o primeiro dígito indica a unidade (1=hora, 2=dia, 3=mês, 4=ano) e os demais dígitos a quantidade. **Exemplo:** `4025` \= 25 anos; `3006` \= 6 meses; `2015` \= 15 dias. Exige conversão antes de usar. |
| `CS_SEXO` | Sexo | `M` \= Masculino · `F` \= Feminino · `I` \= Ignorado. |
| `CS_GESTANT` | Idade gestacional | `1` \= 1º trimestre · `2` \= 2º trimestre · `3` \= 3º trimestre · `4` \= Idade gestacional ignorada · `5` \= Não · `6` \= Não se aplica · `9` \= Ignorado. **Especialmente relevante em Zika** pelo risco de síndrome congênita. |
| `CS_RACA` | Raça/cor (autodeclarada, padrão IBGE) | `1` \= Branca · `2` \= Preta · `3` \= Amarela · `4` \= Parda · `5` \= Indígena · `9` \= Ignorado. |
| `CS_ESCOL_N` | Escolaridade | `0` \= Analfabeto · `1` \= 1ª a 4ª série incompleta do EF · `2` \= 4ª série completa do EF · `3` \= 5ª a 8ª série incompleta do EF · `4` \= Ensino Fundamental completo · `5` \= Ensino Médio incompleto · `6` \= Ensino Médio completo · `7` \= Educação superior incompleta · `8` \= Educação superior completa · `9` \= Ignorado · `10` \= Não se aplica. |
| `SG_UF` | UF de residência | Código IBGE da UF onde o paciente reside. Pode diferir de `SG_UF_NOT`. |
| `ID_MN_RESI` | Município de residência | Código IBGE do município onde o paciente reside. |
| `ID_RG_RESI` | Regional de residência | Regional de saúde do município de residência. |
| `ID_PAIS` | País de residência | Código do país de residência (1 \= Brasil; demais códigos seguem tabela SINAN). |
| `NDUPLIC_N` | Notificação duplicada | Marcador usado quando o sistema identifica notificação em duplicidade. |
| `IN_VINCULA` | Caso vinculado | Indica vinculação a outro caso/surto. |
| `DT_INVEST` | Data da investigação | Quando a investigação epidemiológica do caso foi iniciada. |
| `ID_OCUPA_N` | Ocupação | Código CBO (Classificação Brasileira de Ocupações). |
| `CLASSI_FIN` | Classificação final | `0` \= Descartado · `1` \= Confirmado · `2` \= Em investigação · `8` \= Inconclusivo. **Use sempre `CLASSI_FIN = 1` para análises de casos confirmados.** |
| `CRITERIO` | Critério de confirmação/descarte | `0` \= Em investigação · `1` \= Laboratorial · `2` \= Clínico-epidemiológico. |
| `TPAUTOCTO` | Autoctonia | Indica se a infecção foi local ou importada. `1` \= Sim (autóctone, contraído no município de residência) · `2` \= Não (importado) · `3` \= Indeterminado. |
| `COUFINF` | UF provável de infecção | Onde a pessoa provavelmente contraiu Zika (pode diferir de UF de residência e de notificação). |
| `COPAISINF` | País provável de infecção | País onde provavelmente ocorreu a infecção. |
| `COMUNINF` | Município provável de infecção | Município onde provavelmente ocorreu a infecção. |
| `DOENCA_TRA` | Doença relacionada ao trabalho | `1` \= Sim · `2` \= Não · `9` \= Ignorado. |
| `EVOLUCAO` | Evolução do caso | `0` \= Em investigação · `1` \= Cura · `2` \= Óbito pelo agravo · `3` \= Óbito por outra causa · `9` \= Ignorado. |
| `DT_OBITO` | Data do óbito | Preenchida apenas quando há óbito; vazia caso contrário. |
| `DT_ENCERRA` | Data de encerramento | Quando o caso foi encerrado no sistema (após classificação final). |
| `CS_FLXRET` | Fluxo de retorno | Controle interno de fluxo entre níveis (municipal/estadual/federal). |
| `FLXRECEBI` | Fluxo recebido | Idem, controle de fluxo de recebimento. |
| `TP_SISTEMA` | Tipo de sistema | Sistema de origem do registro. |
| `TPUNINOT` | Tipo de unidade notificadora | Tipo do estabelecimento que notificou (hospital, UBS, etc.). |
| `ID_UNIDADE` | Código da unidade notificadora | Código CNES (Cadastro Nacional de Estabelecimentos de Saúde) da unidade. |
| `ANO_NASC` | Ano de nascimento | Ano de nascimento do paciente. |
| `DT_DIGITA` | Data de digitação | Quando o registro foi digitado no SINAN. |

## **Observações metodológicas importantes**

Alguns avisos que vale a pena os alunos terem em mente antes de cruzar e analisar esses dados.

O SINAN distingue *local de notificação* (`SG_UF_NOT`, `ID_MUNICIP`), *local de residência* (`SG_UF`, `ID_MN_RESI`) e *local provável de infecção* (`COUFINF`, `COMUNINF`). São três coisas diferentes e podem divergir — escolha qual usar conforme a pergunta de pesquisa.

Os arquivos anuais do SINAN **são atualizados retrospectivamente**: a versão de 2020 pode receber correções por anos. Portanto, o número de casos para um mesmo ano pode mudar dependendo de quando o arquivo `.dbc` foi baixado. A coluna `arquivo_origem` ajuda a rastrear isso.

A diferença entre `DT_NOTIFIC` (quando a ficha entrou no sistema) e `DT_SIN_PRI` (quando os sintomas começaram) é a **latência de notificação**. Em análises de curva epidêmica, sempre prefira `DT_SIN_PRI` ou `SEM_PRI`.

Muitos campos têm taxa alta de "Ignorado" (código 9), especialmente em escolaridade, raça/cor e ocupação. Não trate ausências como zeros — filtre adequadamente.

Para casos confirmados, sempre filtre por `CLASSI_FIN = 1`. Os demais valores incluem casos descartados ou ainda em investigação, e misturá-los gera estimativas erradas.

## **Referências para os alunos**

**Documentação oficial do SINAN e dicionários de dados**

* Portal do DATASUS — onde os arquivos `.dbc` são baixados: [https://datasus.saude.gov.br/transferencia-de-arquivos/](https://datasus.saude.gov.br/transferencia-de-arquivos/)  
* SINAN — página institucional: [https://portalsinan.saude.gov.br/](https://portalsinan.saude.gov.br/)  
* Fichas de notificação e instruções (Zika): [https://portalsinan.saude.gov.br/doencas-e-agravos](https://portalsinan.saude.gov.br/doencas-e-agravos) (procurar "Zika")  
* Dicionário de dados do SINAN-NET (PDF, listagem completa de campos e códigos): buscar em [https://portalsinan.saude.gov.br/](https://portalsinan.saude.gov.br/) por "dicionário de dados"

**Guias de vigilância e protocolos clínicos**

* Ministério da Saúde — Guia de Vigilância em Saúde: [https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/guia-de-vigilancia-em-saude](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/guia-de-vigilancia-em-saude)  
* Protocolo de vigilância da síndrome congênita associada ao Zika: [https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/z/zika-virus](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/z/zika-virus)  
* Boletins epidemiológicos de arboviroses (atualização semanal): [https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/boletins/epidemiologicos](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/boletins/epidemiologicos)

**Pacotes e ferramentas para análise**

* `microdatasus` (R) — baixa e lê arquivos `.dbc` direto do DATASUS, com decodificação automática: [https://github.com/rfsaldanha/microdatasus](https://github.com/rfsaldanha/microdatasus)  
* `read.dbc` (R) — para ler o formato `.dbc` original: [https://cran.r-project.org/package=read.dbc](https://cran.r-project.org/package=read.dbc)  
* `PySUS` (Python) — equivalente em Python, criado pela Fiocruz: [https://github.com/AlertaDengue/PySUS](https://github.com/AlertaDengue/PySUS)

**Códigos auxiliares**

* Códigos de municípios IBGE: [https://www.ibge.gov.br/explica/codigos-dos-municipios.php](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)  
* CID-10 (códigos de doenças): [http://www2.datasus.gov.br/cid10/V2008/cid10.htm](http://www2.datasus.gov.br/cid10/V2008/cid10.htm)  
* CBO (códigos de ocupação): [https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/classificacao-brasileira-de-ocupacoes](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/classificacao-brasileira-de-ocupacoes)  
* CNES (códigos de estabelecimentos de saúde): [https://cnes.datasus.gov.br/](https://cnes.datasus.gov.br/)

**Para contexto epidemiológico sobre Zika**

* Página da OPAS sobre Zika: [https://www.paho.org/pt/topicos/zika](https://www.paho.org/pt/topicos/zika)  
* WHO — Zika virus fact sheet: [https://www.who.int/news-room/fact-sheets/detail/zika-virus](https://www.who.int/news-room/fact-sheets/detail/zika-virus)  
* Fiocruz — Portal Arboviroses: [https://www.arboviroses.fiocruz.br/](https://www.arboviroses.fiocruz.br/)

**Artigos didáticos sobre uso do SINAN em pesquisa**

* Laguardia J. et al. — *Sistema de Informação de Agravos de Notificação (SINAN): desafios no desenvolvimento de um sistema de informação em saúde*. Epidemiologia e Serviços de Saúde, 2004\. (Buscar no SciELO: [https://www.scielo.br/](https://www.scielo.br/))  
* Brito CAA et al. — diversos artigos sobre Zika no Brasil. Buscar no PubMed: [https://pubmed.ncbi.nlm.nih.gov/?term=zika+brazil+SINAN](https://pubmed.ncbi.nlm.nih.gov/?term=zika+brazil+SINAN)

