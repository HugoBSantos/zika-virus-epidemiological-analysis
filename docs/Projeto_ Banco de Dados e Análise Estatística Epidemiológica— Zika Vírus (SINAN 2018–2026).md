## **Projeto: Banco de Dados e Análise Estatística Epidemiológica— Zika Vírus (SINAN 2018–2026)**

**Disciplina:** Banco de Dados / Modelagem Estatística  

**Tecnologia:** PostgreSQL 15+, Pyhon

**Dataset:** `ZIKA_BR_2018_2026_UNIFICADO.csv` — 236.398 notificações · 43 colunas · 27 UFs 

**Fonte:** SINAN — Sistema de Informação de Agravos de Notificação (DataSUS/MS)

### **Contexto**

O Zika vírus emergiu como emergência de saúde pública no Brasil em 2015–2016, associado a casos de microcefalia e síndrome de Guillain-Barré. O SINAN registra todas as notificações compulsórias de doenças no país. A base disponibilizada cobre 2018 a 2026 e será transformada em um banco de dados relacional auditado, capaz de responder perguntas epidemiológicas reais.

### **Objetivo**

Transformar o CSV bruto do SINAN em um banco de dados relacional normalizado no PostgreSQL, aplicando boas práticas de modelagem, automação e análise de dados em saúde pública.

### **Entregas**

**1\. Modelagem e carga (ETL)** Projetar o esquema relacional (ERD), criar as tabelas no PostgreSQL e carregar os dados via script Python.

**2\. Funções** Implementar funções para operações recorrentes: decodificação de idade, resumo epidemiológico por UF/ano, inserção validada e detecção de duplicatas.

**3\. Triggers** Criar triggers de auditoria (INSERT/UPDATE/DELETE com snapshot antes/depois em JSONB) e de validação clínica (consistência entre campos antes de persistir).

**4\. Views para dashboard** Construir views prontas para visualização: série temporal semanal, casos por UF e ano, pirâmide etária, vigilância de gestantes e cards de KPI.

**5\. Análise estatística** Explorar sazonalidade, tendência por UF, previsão de casos (Prophet) e agrupamento de municípios por perfil epidemiológico (K-Means)