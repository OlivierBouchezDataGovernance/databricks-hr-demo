# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 8 · Pourquoi les employés partent-ils ?
# MAGIC L'analyse complète du notebook Jupyter `HR_Numerics_Analysis`, refaite **à la manière de Databricks**.
# MAGIC
# MAGIC | Étape | Dans Jupyter | Ici |
# MAGIC |---|---|---|
# MAGIC | Charger | Lire un CSV en mémoire | Créer une **table documentée** |
# MAGIC | Contrôler | Quelques `print` | Des **règles de qualité** enregistrées dans la table |
# MAGIC | Calculer | pandas | **SQL** et Spark |
# MAGIC | Réutiliser | Copier le code | Des **vues** partagées avec l'équipe |
# MAGIC | Dessiner | Images fixes | Graphiques **interactifs** |
# MAGIC | Vérifier | À l'œil | Un **contrôle automatique** à la fin |
# MAGIC
# MAGIC **Le parcours :** 1 préparer · 2 charger · 3 contrôler · 4 répartitions · 5 départs · 6 corrélations · 7 partis et restés · 8 groupes à risque · 9 profils cachés · 10 vérifier · 11 conclure

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : préparer les outils
# MAGIC `%pip install` ajoute la bibliothèque de graphiques interactifs **Plotly**. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q plotly

# COMMAND ----------

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyspark.sql import functions as F

# Les mêmes couleurs partout, lisibles aussi par les personnes daltoniennes
BLUE, ORANGE = "#2a78d6", "#eb6834"                 # bleu = resté, orange = parti
COLORS = {"resté": BLUE, "parti": ORANGE}
LAYOUT = dict(template="plotly_white", font=dict(size=13))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : charger les données dans une table
# MAGIC On ne travaille pas directement sur le fichier. On crée une **table** avec, pour chaque colonne, un nom clair, un type et une description.
# MAGIC
# MAGIC On en profite pour corriger le fichier d'origine : `average_montly_hours` (faute de frappe) devient `average_monthly_hours`, et `left` devient `has_left`. Le fichier, lui, n'est pas modifié.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- COMMENT = la description que verront les collègues dans le Catalog
# MAGIC CREATE TABLE IF NOT EXISTS workspace.hr_demo.hr_employee (
# MAGIC   satisfaction_level     DOUBLE NOT NULL COMMENT 'Satisfaction score, from 0 to 1',
# MAGIC   last_evaluation        DOUBLE NOT NULL COMMENT 'Last evaluation score, from 0 to 1',
# MAGIC   number_project         INT    NOT NULL COMMENT 'Number of projects',
# MAGIC   average_monthly_hours  INT    NOT NULL COMMENT 'Average hours worked per month',
# MAGIC   time_spend_company     INT    NOT NULL COMMENT 'Years in the company',
# MAGIC   work_accident          INT    NOT NULL COMMENT '1 = had a work accident',
# MAGIC   has_left               INT    NOT NULL COMMENT '1 = left the company',
# MAGIC   promotion_last_5years  INT    NOT NULL COMMENT '1 = promoted in the last 5 years'
# MAGIC ) COMMENT 'HR demo: one row per employee record, numeric variables only. No employee number in the source.'

# COMMAND ----------

# MAGIC %md
# MAGIC Ensuite, on remplit la table à partir du fichier, rangé dans le **volume**. `OVERWRITE` remplace le contenu d'un seul coup : relancer ne crée pas de doublons, et un collègue qui lit la table au même moment ne la voit jamais vide.

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT OVERWRITE workspace.hr_demo.hr_employee
# MAGIC SELECT CAST(satisfaction_level AS DOUBLE), CAST(last_evaluation AS DOUBLE), CAST(number_project AS INT),
# MAGIC        CAST(average_montly_hours AS INT), CAST(time_spend_company AS INT), CAST(Work_accident AS INT),
# MAGIC        CAST(`left` AS INT), CAST(promotion_last_5years AS INT)
# MAGIC FROM read_files('/Volumes/workspace/hr_demo/datasets/HR_15000 Evaluations_NumericsOnly.csv', format => 'csv', header => true)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Regarder 5 lignes de la table
# MAGIC SELECT * FROM workspace.hr_demo.hr_employee LIMIT 5

# COMMAND ----------

# MAGIC %md
# MAGIC 👉 **À montrer :** **Catalog** › `workspace` › `hr_demo` › `hr_employee`. Les descriptions sont là, et l'onglet **Lineage** montre d'où vient la table.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : contrôler la qualité
# MAGIC Avant d'analyser, on vérifie. Ici les règles sont **dans la table** : une ligne qui ne les respecte pas serait refusée.

# COMMAND ----------

# Les règles : un nom, et la condition que chaque ligne doit respecter
rules = {
    "scores_0_to_1": "satisfaction_level BETWEEN 0 AND 1 AND last_evaluation BETWEEN 0 AND 1",
    "flags_0_or_1": "has_left IN (0, 1) AND work_accident IN (0, 1) AND promotion_last_5years IN (0, 1)",
}
# On ajoute seulement les règles qui n'existent pas encore : le notebook peut être relancé
existing = {r.key for r in spark.sql("SHOW TBLPROPERTIES workspace.hr_demo.hr_employee").collect()}
for name, condition in rules.items():
    if f"delta.constraints.{name}" not in existing:
        spark.sql(f"ALTER TABLE workspace.hr_demo.hr_employee ADD CONSTRAINT {name} CHECK ({condition})")
    print(f"Règle {name} : en place")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Combien de lignes, et combien sont la copie exacte d'une autre ?
# MAGIC WITH u AS (SELECT DISTINCT * FROM workspace.hr_demo.hr_employee)
# MAGIC SELECT t.n                              AS nb_lignes,
# MAGIC        t.n - d.n                        AS nb_copies,
# MAGIC        round(100 * (t.n - d.n) / t.n, 1) AS pct_copies,
# MAGIC        round(100 * t.taux, 1)           AS pct_departs_toutes_lignes,
# MAGIC        round(100 * d.taux, 1)           AS pct_departs_sans_copies
# MAGIC FROM (SELECT count(*) AS n, avg(has_left) AS taux FROM workspace.hr_demo.hr_employee) t
# MAGIC CROSS JOIN (SELECT count(*) AS n, avg(has_left) AS taux FROM u) d

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ **Attention.** Une ligne sur cinq est une copie exacte d'une autre. Sans ces copies, le taux de départ passe de **23,8 %** à **16,1 %**. Sans numéro d'employé, impossible de savoir si ce sont des doublons ou des personnes semblables. Comme dans le notebook d'origine, on garde toutes les lignes, mais chaque pourcentage qui suit dépend de ce choix.
# MAGIC
# MAGIC C'est exactement le rôle de la **gouvernance des données** : un identifiant dans la source aurait réglé la question.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Le résumé de chaque colonne
# MAGIC `summary()` calcule le nombre, la moyenne, la dispersion, le minimum et le maximum.

# COMMAND ----------

df = spark.table("workspace.hr_demo.hr_employee")   # la table, prête pour Spark
display(df.summary())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : les répartitions
# MAGIC Spark compte les employés par valeur ou par tranche ; seul ce petit résultat est envoyé au graphique. **Passez la souris** sur une barre pour lire sa valeur.

# COMMAND ----------

# Pour les trois variables continues, on regroupe en 30 tranches
continuous = ["satisfaction_level", "last_evaluation", "average_monthly_hours"]


def bins(c, n=30):
    """Compte les employés par tranche de la colonne c, pour les restés et pour les partis."""
    lo, hi, _ = df.agg(F.min(c), F.max(c), F.count("*")).first()
    step = (hi - lo) / n
    k = F.least(F.floor((F.col(c) - lo) / step), F.lit(n - 1))      # numéro de la tranche
    out = df.groupBy(k.alias("k"), "has_left").count().toPandas()
    out["x"] = lo + (out["k"].astype(float) + 0.5) * step           # milieu de la tranche
    return out.sort_values("x")


fig = make_subplots(rows=2, cols=4, subplot_titles=df.columns)
for i, c in enumerate(df.columns):
    if c in continuous:
        d = bins(c).groupby("x", as_index=False)["count"].sum()
    else:
        d = df.groupBy(F.col(c).alias("x")).count().orderBy("x").toPandas()
    fig.add_trace(go.Bar(x=d["x"], y=d["count"], marker_color=BLUE), row=i // 4 + 1, col=i % 4 + 1)
    if c in continuous:                                             # ligne pointillée = moyenne
        fig.add_vline(x=float(df.agg(F.avg(c)).first()[0]), line_dash="dash", line_color=ORANGE, row=i // 4 + 1, col=i % 4 + 1)
fig.update_layout(height=600, showlegend=False, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** L'évaluation et les heures ont chacune **deux bosses**. La satisfaction montre un groupe à part, très insatisfait, près de 0,1.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 5 : les départs
# MAGIC 👉 **Sans code :** cliquez sur **+ › Visualization** au-dessus du résultat pour en faire un graphique.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT CASE has_left WHEN 1 THEN 'parti' ELSE 'resté' END AS statut,
# MAGIC        count(*) AS employes,
# MAGIC        round(100 * count(*) / sum(count(*)) OVER (), 1) AS pct    -- part du total
# MAGIC FROM workspace.hr_demo.hr_employee
# MAGIC GROUP BY has_left
# MAGIC ORDER BY has_left

# COMMAND ----------

# Le même résultat, dessiné en une barre
t = df.groupBy("has_left").count().orderBy("has_left").toPandas()
t["statut"] = t["has_left"].map({0: "resté", 1: "parti"})
fig = px.bar(t, x="count", y=[""] * 2, color="statut", orientation="h", color_discrete_map=COLORS,
             text=[f"{n:,} ({n / t['count'].sum():.1%})" for n in t["count"]], title="Employés restés et partis")
fig.update_layout(height=220, xaxis_title="", yaxis_title="", **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 6 : les corrélations
# MAGIC Une corrélation va de **-1** (quand l'un monte, l'autre descend) à **1** (ils montent ensemble) ; **0** = pas de lien en ligne droite. Cette cellule est technique : on peut regarder seulement l'image.

# COMMAND ----------

cols = df.columns
pairs = [(a, b) for i, a in enumerate(cols) for b in cols[:i]]      # chaque paire une seule fois
row = df.agg(*[F.corr(a, b).alias(f"{a}|{b}") for a, b in pairs]).first().asDict()
corr = pd.DataFrame(index=cols, columns=cols, dtype=float)
for a, b in pairs:
    corr.loc[a, b] = row[f"{a}|{b}"]
fig = px.imshow(corr.iloc[1:, :-1], text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale=[BLUE, "#f0efec", ORANGE],
                title="Corrélations de Pearson")
fig.update_layout(height=600, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** La satisfaction a le lien le plus fort avec le départ (**-0,39**). Évaluation, projets et heures sont liés entre eux (0,34 à 0,42) mais semblent sans lien avec le départ. La suite montre que c'est **trompeur**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 7 : comparer les partis et les restés

# COMMAND ----------

m = df.groupBy("has_left").agg(*[F.avg(c).alias(c) for c in cols if c != "has_left"]).orderBy("has_left").toPandas()
cmp = m.set_index("has_left").T.rename(columns={0: "reste", 1: "parti"})
cmp["difference_pct"] = 100 * (cmp["parti"] / cmp["reste"] - 1)     # écart en pourcentage
display(cmp.round(2).rename_axis("variable").reset_index())

# COMMAND ----------

# Forme des répartitions : part de chaque groupe par tranche, pour comparer des groupes de tailles différentes
fig = make_subplots(rows=1, cols=3, subplot_titles=continuous)
for i, c in enumerate(continuous):
    d = bins(c)
    for v, name in ((0, "resté"), (1, "parti")):
        p = d[d["has_left"] == v]
        fig.add_trace(go.Scatter(x=p["x"], y=100 * p["count"] / p["count"].sum(), name=name, line_color=COLORS[name],
                                 fill="tozeroy", opacity=0.6, showlegend=i == 0), row=1, col=i + 1)
fig.update_yaxes(title_text="% du groupe", col=1)
fig.update_layout(height=400, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** Les moyennes d'évaluation et d'heures sont presque égales, mais pas les formes : les partis se concentrent **aux deux extrêmes**, les restés au milieu. Deux groupes opposés s'annulent dans la moyenne, et dans la corrélation.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 8 : le taux de départ par groupe
# MAGIC Plutôt que de garder ce calcul pour soi, on crée une **vue** : une requête enregistrée, avec un nom. Toute l'équipe, et les tableaux de bord, l'utilisent ensuite comme une table.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW workspace.hr_demo.hr_turnover_by_group
# MAGIC COMMENT 'HR demo: turnover rate by number of projects, monthly hours, years, accident and promotion' AS
# MAGIC WITH g AS (
# MAGIC   SELECT has_left, number_project, time_spend_company, work_accident, promotion_last_5years,
# MAGIC          CASE WHEN average_monthly_hours <= 130 THEN '091-130' WHEN average_monthly_hours <= 160 THEN '131-160'
# MAGIC               WHEN average_monthly_hours <= 190 THEN '161-190' WHEN average_monthly_hours <= 220 THEN '191-220'
# MAGIC               WHEN average_monthly_hours <= 250 THEN '221-250' WHEN average_monthly_hours <= 280 THEN '251-280'
# MAGIC               ELSE '281-310' END AS hours_band
# MAGIC   FROM workspace.hr_demo.hr_employee),
# MAGIC l AS (  -- une ligne par employé et par critère
# MAGIC   SELECT has_left, 'projects' AS criterion, CAST(number_project AS STRING) AS value FROM g
# MAGIC   UNION ALL SELECT has_left, 'hours', hours_band FROM g
# MAGIC   UNION ALL SELECT has_left, 'years', lpad(CAST(time_spend_company AS STRING), 2, '0') FROM g
# MAGIC   UNION ALL SELECT has_left, 'accident', CAST(work_accident AS STRING) FROM g
# MAGIC   UNION ALL SELECT has_left, 'promotion', CAST(promotion_last_5years AS STRING) FROM g)
# MAGIC SELECT criterion, value, count(*) AS employees, sum(has_left) AS leavers, round(100 * avg(has_left), 1) AS turnover_pct
# MAGIC FROM l GROUP BY criterion, value

# COMMAND ----------

# MAGIC %sql
# MAGIC -- employees : combien de personnes derrière chaque pourcentage ?
# MAGIC SELECT * FROM workspace.hr_demo.hr_turnover_by_group ORDER BY criterion, value

# COMMAND ----------

g = spark.table("workspace.hr_demo.hr_turnover_by_group").orderBy("value").toPandas()
avg_rate = 100 * float(df.agg(F.avg("has_left")).first()[0])
titles = {"projects": "Nombre de projets", "hours": "Heures par mois", "years": "Années dans l'entreprise"}
fig = make_subplots(rows=1, cols=3, subplot_titles=list(titles.values()))
for i, k in enumerate(titles):
    p = g[g["criterion"] == k]
    fig.add_trace(go.Bar(x=p["value"].str.lstrip("0"), y=p["turnover_pct"], marker_color=BLUE, customdata=p["employees"],
                         text=[f"{float(v):.0f}%" for v in p["turnover_pct"]], textposition="outside",
                         hovertemplate="%{y} % de %{customdata} employés<extra></extra>"), row=1, col=i + 1)
    fig.add_hline(y=avg_rate, line_dash="dash", line_color=ORANGE, row=1, col=i + 1)    # moyenne générale
fig.update_xaxes(type="category")
fig.update_yaxes(range=[0, 115])
fig.update_layout(height=430, showlegend=False, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.**
# MAGIC > - **Projets :** 2 % de départs avec 3 projets, mais 66 % avec 2 et 100 % avec 7 (256 personnes).
# MAGIC > - **Heures :** le plus bas entre 161 et 220 heures (3 à 4 %) ; 81 % au-dessus de 280.
# MAGIC > - **Années :** 57 % à 5 ans ; aucun départ à partir de 7 ans.
# MAGIC > - **Promotion :** seulement 319 promus, dont 6 % sont partis.
# MAGIC >
# MAGIC > Trop peu de travail et trop de travail vont tous deux avec le départ.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 9 : les profils cachés
# MAGIC On place chaque employé selon sa satisfaction et son évaluation.

# COMMAND ----------

# Plusieurs employés ont le même point : Spark les compte, la taille du point montre combien ils sont
p = df.groupBy("satisfaction_level", "last_evaluation", "has_left").count().toPandas()
p["statut"] = p["has_left"].map({0: "resté", 1: "parti"})
fig = px.scatter(p, x="satisfaction_level", y="last_evaluation", size="count", size_max=9, opacity=0.45, color="statut",
                 facet_col="statut", color_discrete_map=COLORS, category_orders={"statut": ["resté", "parti"]},
                 title="Satisfaction et évaluation")
fig.update_layout(height=500, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC À droite, trois groupes de partis apparaissent. On enregistre leur définition dans une **vue**, pour que chacun utilise les mêmes limites.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW workspace.hr_demo.hr_profile_summary
# MAGIC COMMENT 'HR demo: the three leaver profiles; boundaries drawn by eye on the same data' AS
# MAGIC WITH c AS (
# MAGIC   SELECT *, CASE
# MAGIC     WHEN satisfaction_level <= 0.11 AND last_evaluation >= 0.77 THEN 'Overworked and unhappy'
# MAGIC     WHEN satisfaction_level BETWEEN 0.36 AND 0.46 AND last_evaluation BETWEEN 0.45 AND 0.57 THEN 'Underused'
# MAGIC     WHEN satisfaction_level BETWEEN 0.72 AND 0.92 AND last_evaluation >= 0.80 THEN 'Happy top performers'
# MAGIC     END AS profile
# MAGIC   FROM workspace.hr_demo.hr_employee)
# MAGIC SELECT profile, count(*) AS employees, sum(has_left) AS leavers,
# MAGIC        round(100 * avg(has_left), 1) AS turnover_pct,
# MAGIC        round(100 * sum(has_left) / (SELECT sum(has_left) FROM workspace.hr_demo.hr_employee), 1) AS share_of_leavers_pct,
# MAGIC        round(avg(CASE WHEN has_left = 1 THEN number_project END), 1) AS projects_of_leavers,
# MAGIC        round(avg(CASE WHEN has_left = 1 THEN average_monthly_hours END), 0) AS hours_of_leavers
# MAGIC FROM c WHERE profile IS NOT NULL GROUP BY profile

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM workspace.hr_demo.hr_profile_summary ORDER BY turnover_pct DESC

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** Trois groupes compacts réunissent environ **92 % des départs** :
# MAGIC > - **Surchargés et malheureux** (*Overworked and unhappy*, 100 % partis) : 6 projets, 277 heures.
# MAGIC > - **Sous-employés** (*Underused*, 93 % partis) : 2 projets, 144 heures.
# MAGIC > - **Performants et satisfaits** (*Happy top performers*, 38 % partis) : 245 heures.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 10 : vérifier
# MAGIC Deux outils, un même résultat ? On compare automatiquement avec les chiffres du notebook Jupyter. Si un seul diffère, la cellule **s'arrête en erreur**.

# COMMAND ----------

by = {(r.criterion, r.value): (r.employees, float(r.turnover_pct)) for r in spark.table("workspace.hr_demo.hr_turnover_by_group").collect()}
pr = {r.profile: (float(r.turnover_pct), float(r.projects_of_leavers), float(r.hours_of_leavers)) for r in spark.table("workspace.hr_demo.hr_profile_summary").collect()}
total = spark.table("workspace.hr_demo.hr_profile_summary").agg(F.sum("share_of_leavers_pct")).first()[0]
n, u = df.count(), df.distinct().count()

checks = [   # (ce que l'on vérifie, valeur ici, valeur dans Jupyter)
    ("lignes", n, 14999), ("copies", n - u, 3079),
    ("départs, toutes lignes %", round(avg_rate, 1), 23.8),
    ("départs, sans copies %", round(100 * df.distinct().agg(F.avg("has_left")).first()[0], 1), 16.1),
    ("corrélation satisfaction / départ", round(row["has_left|satisfaction_level"], 2), -0.39),
    ("corrélation projets / heures", round(row["average_monthly_hours|number_project"], 2), 0.42),
    ("employés avec 2 projets", by["projects", "2"][0], 2388), ("employés avec 7 projets", by["projects", "7"][0], 256),
    ("employés 91-130 h", by["hours", "091-130"][0], 770), ("employés 281-310 h", by["hours", "281-310"][0], 562),
    ("employés 3 ans", by["years", "03"][0], 6443), ("employés promus", by["promotion", "1"][0], 319),
    ("départs, promus %", by["promotion", "1"][1], 6.0), ("départs, accident %", by["accident", "1"][1], 7.8),
    ("départs, 2 projets %", round(by["projects", "2"][1]), 66), ("départs, 5 ans %", round(by["years", "05"][1]), 57),
    ("départs, plus de 280 h %", round(by["hours", "281-310"][1]), 81),
    ("surchargés : départs %", round(pr["Overworked and unhappy"][0]), 100),
    ("surchargés : heures", pr["Overworked and unhappy"][2], 277),
    ("sous-employés : départs %", round(pr["Underused"][0]), 93), ("sous-employés : heures", pr["Underused"][2], 144),
    ("performants : départs %", round(pr["Happy top performers"][0]), 38), ("performants : heures", pr["Happy top performers"][2], 245),
    ("part des départs dans les 3 profils %", round(float(total)), 92),
]
result = pd.DataFrame([(a, float(b), float(c), float(b) == float(c)) for a, b, c in checks], columns=["controle", "databricks", "jupyter", "identique"])
display(result)
bad = result[~result["identique"]]
assert bad.empty, f"Différences : {bad.to_dict('records')}"
print(f"{len(result)} contrôles sur {len(result)} identiques")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 11 : conclure
# MAGIC - Environ **un employé sur quatre** est parti, ou un sur six sans les copies.
# MAGIC - La **satisfaction** a le lien direct le plus fort avec le départ, mais ce lien n'est pas une ligne droite.
# MAGIC - La **charge de travail** compte aux deux extrêmes : trop peu ou trop de projets et d'heures.
# MAGIC - Les partis forment **trois profils**, invisibles dans les moyennes et dans les corrélations.
# MAGIC - Ceux qui partent le moins ont 3 à 4 projets et travaillent 161 à 220 heures.
# MAGIC
# MAGIC > ⚠️ **Attention.** Ce sont des liens, pas des causes. Les limites des profils ont été tracées à l'œil sur les mêmes données, et leurs bords très nets suggèrent que le jeu de données est **simulé**. Une ligne sur cinq est une copie exacte.
# MAGIC
# MAGIC **Ce que la plateforme a ajouté :** une table documentée, des règles de qualité, deux vues réutilisables, un lignage et un contrôle automatique.
