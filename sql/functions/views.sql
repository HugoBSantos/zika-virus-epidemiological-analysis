--VIEW 1: Serie Temporal Semanal
CREATE VIEW silver.vw_serie_temporal_semanal AS
SELECT
	semana_primeiros_sintomas,
	COUNT(*) AS total_casos
FROM silver.notificacoes_casos
WHERE classificacao_final = 'Confirmado'
GROUP BY semana_primeiros_sintomas;

--VIEW 2: Casos por UF e Ano
CREATE VIEW silver.vw_casos_uf_ano AS
SELECT
	u.sigla AS uf,
	EXTRACT(YEAR FROM nc.data_notificacao) AS ano,
	COUNT(*) AS total_casos
FROM silver.notificacoes_casos AS nc
JOIN silver.ufs AS u ON nc.uf_provavel_infeccao = u.uf_id
WHERE nc.classificacao_final = 'Confirmado'
	AND nc.uf_provavel_infeccao IS NOT NULL
GROUP BY u.sigla, ano
ORDER BY ano;

--VIEW 3: Piramide Etaria
CREATE VIEW silver.vw_piramide_etaria AS
WITH base AS(
	SELECT
		p.sexo,
		idade_anos(p.idade_codificada) AS idade
	FROM silver.pacientes AS p
	JOIN silver.notificacoes_casos AS nc ON p.paciente_id = nc.paciente_id
	WHERE nc.classificacao_final = 'Confirmado'
		AND p.sexo IN ('Masculino','Feminino')
)
SELECT
	CASE
		WHEN idade < 5 THEN '0-4'
		WHEN idade < 10 THEN '5-9'
		WHEN idade < 15 THEN '10-14'
		WHEN idade < 20 THEN '15-19'
		WHEN idade < 30 THEN '20-29'
		WHEN idade < 40 THEN '30-39'
		WHEN idade < 50 THEN '40-49'
		WHEN idade < 60 THEN '50-59'
		WHEN idade < 70 THEN '60-69'
		WHEN idade < 80 THEN '70-79'
		ELSE '80+'
	END AS faixa_etaria,
	sexo,
	COUNT(*) AS total_casos
FROM base
GROUP BY faixa_etaria, sexo
ORDER BY faixa_etaria, sexo;

--VIEW 4: Vigilancia de Gestantes
CREATE VIEW silver.vw_vigilancia_gestantes AS
SELECT
	idade_gestacional,
	COUNT(*) AS total_casos
FROM silver.pacientes
WHERE idade_gestacional IN ('1º trimestre', '2º trimestre', '3º trimestre')
GROUP BY idade_gestacional;

--VIEW 5: Cards de KPIs
CREATE VIEW silver.vw_kpis AS
SELECT
	COUNT(*) AS total_casos,
	SUM(
		CASE
			WHEN nc.evolucao_caso = 'Óbito pelo agravo' THEN 1
			ELSE 0
		END
	) AS total_obitos,
	SUM(
		CASE
			WHEN p.idade_gestacional IN ('1º trimestre', '2º trimestre', '3º trimestre') THEN 1
			ELSE 0
		END
	) AS total_gestantes,
	SUM(
		CASE
			WHEN nc.classificacao_final = 'Em investigação' THEN 1
			ELSE 0
		END
	) AS aguardando_investigacao
FROM silver.notificacoes_casos AS nc
JOIN silver.pacientes AS p ON nc.paciente_id = p.paciente_id;