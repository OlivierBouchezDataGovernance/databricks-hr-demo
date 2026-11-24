# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 7 · La même analyse, à la manière de Databricks
# MAGIC Les notebooks 01 à 06 sont nés dans **Jupyter**, un outil souvent utilisé seul, sur son ordinateur. Ici, on refait l'analyse avec ce qu'une **plateforme d'équipe** apporte en plus.
# MAGIC
# MAGIC | Seul, dans Jupyter | En équipe, dans Databricks | Pourquoi |
# MAGIC |---|---|---|
# MAGIC | Un fichier CSV dans un dossier | Une **table** dans Unity Catalog | Une seule version pour tous, avec des droits d'accès |
# MAGIC | Lire le fichier avec pandas | Interroger la table en **SQL** ou avec **Spark** | Fonctionne aussi sur de très gros volumes |
# MAGIC | `describe()`, `groupby` | Fonctions et `GROUP BY` en SQL | Un langage partagé par beaucoup de métiers |
# MAGIC | Graphiques par code | Les mêmes, ou **+ › Visualization** sans code | Accessible aux non-programmeurs |
# MAGIC | Pas d'historique des données | **Historique** et **lignage** | Savoir qui a changé quoi, et d'où vient un chiffre |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q seaborn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : transformer le fichier en table
# MAGIC On lit le CSV, on l'enregistre comme **table**, puis on lui ajoute une description pour que les collègues sachent ce qu'elle contient.
# MAGIC
# MAGIC `spark` est déjà prêt dans Databricks : rien à installer.

# COMMAND ----------

TABLE = "workspace.hr_demo.hr_evaluations"   # adresse de la table : catalogue.schéma.table

# header : la première ligne contient les titres ; inferSchema : deviner nombre ou texte
# overwrite : relancer ce notebook remplace la table, sans créer de doublons
(spark.read.csv("/Volumes/workspace/hr_demo/datasets/HR_15000 Evaluations - CLEAN.csv", header=True, inferSchema=True)
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(TABLE))

# Décrire la table pour les collègues
spark.sql(f"COMMENT ON TABLE {TABLE} IS 'HR evaluations demo: 14,999 employees; left = 1 when the employee has left; sales = department'")

df = spark.table(TABLE)
display(df.limit(10))    # display : un tableau interactif (trier, filtrer, graphique)

# COMMAND ----------

# MAGIC %md
# MAGIC ### À montrer en direct
# MAGIC Menu **Catalog** › `workspace` › `hr_demo` › `hr_evaluations` :
# MAGIC - **Overview** : colonnes et description
# MAGIC - **Sample data** : un aperçu
# MAGIC - **Permissions** : qui a accès
# MAGIC - **History** : les versions successives
# MAGIC - **Lineage** : d'où vient la table
# MAGIC
# MAGIC ## Étape 2 : l'historique
# MAGIC Le premier mot, `%sql`, indique que la cellule est écrite en **SQL**. Un même notebook mélange les langages.
# MAGIC
# MAGIC Chaque modification de la table est enregistrée : quand, par qui, quelle opération.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY workspace.hr_demo.hr_evaluations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : les statistiques (notebook 04)
# MAGIC D'abord le résumé automatique, l'équivalent de `describe()`.

# COMMAND ----------

display(df.summary())

# COMMAND ----------

# MAGIC %md
# MAGIC Puis les mêmes indicateurs en SQL. La phrase se lit presque comme du texte : **SELECT** (je veux) … **FROM** (dans cette table). **AS** donne un nom au résultat, et `--` introduit un commentaire.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) AS n_rows,                                  -- nombre de lignes
# MAGIC        sum(average_montly_hours)        AS sum_hours,       -- total
# MAGIC        avg(time_spend_company)          AS avg_years,       -- moyenne
# MAGIC        median(average_montly_hours)     AS median_hours,    -- valeur du milieu
# MAGIC        mode(number_project)             AS mode_projects,   -- valeur la plus fréquente
# MAGIC        max(average_montly_hours) - min(average_montly_hours) AS range_hours,  -- étendue
# MAGIC        var_samp(average_montly_hours)   AS variance_hours,
# MAGIC        stddev_samp(average_montly_hours) AS stddev_hours,   -- écart-type
# MAGIC        skewness(average_montly_hours)   AS skewness_hours,  -- asymétrie
# MAGIC        kurtosis(average_montly_hours)   AS kurtosis_hours   -- aplatissement
# MAGIC FROM workspace.hr_demo.hr_evaluations

# COMMAND ----------

# MAGIC %md
# MAGIC **Vérifiez :** on retrouve les chiffres du notebook 04. Deux méthodes, un même résultat : c'est un bon contrôle.
# MAGIC
# MAGIC ## Étape 4 : les liens entre colonnes (notebook 03)
# MAGIC Spark calcule les corrélations, puis seaborn les dessine. Cette cellule est la plus technique : on peut la passer et regarder seulement l'image.

# COMMAND ----------

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyspark.sql import functions as F

cols = [c for c, t in df.dtypes if t != "string"]   # garder les colonnes de nombres
# Spark calcule la corrélation de chaque paire de colonnes, en une seule lecture
row = df.agg(*[F.corr(a, b).alias(f"{a}|{b}") for a in cols for b in cols]).first().asDict()
# Ranger les résultats en tableau
corr = pd.DataFrame([[row[f"{a}|{b}"] for b in cols] for a in cols], index=cols, columns=cols)

plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True)
plt.title("Correlation Matrix (computed by Spark)")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 5 : les départs par département (notebook 05)
# MAGIC **GROUP BY** : faire un paquet par département. **ORDER BY … DESC** : trier du plus grand au plus petit.
# MAGIC
# MAGIC 👉 **À essayer sans code :** au-dessus du résultat, cliquez sur **+ › Visualization**, choisissez un diagramme en barres, puis ajoutez-le à un tableau de bord.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT sales AS department,                       -- renommer : "sales" est le département
# MAGIC        count_if(`left` = 0) AS stayed,            -- restés
# MAGIC        count_if(`left` = 1) AS left_company,      -- partis
# MAGIC        round(100 * avg(`left`), 1) AS pct_left    -- pourcentage de départs
# MAGIC FROM workspace.hr_demo.hr_evaluations
# MAGIC GROUP BY sales
# MAGIC ORDER BY left_company DESC

# COMMAND ----------

# MAGIC %md
# MAGIC Les graphiques du notebook 05, dessinés à partir de la table :

# COMMAND ----------

# Spark compte, puis toPandas() ramène le petit résultat pour le dessiner
g = (df.groupBy("sales").agg(F.count_if(F.col("left") == 0).alias("stayed"), F.count_if(F.col("left") == 1).alias("left"))
       .orderBy(F.desc("left")).toPandas().set_index("sales"))
colors = ["green", "red"]                          # vert = resté, rouge = parti
fig, ax = plt.subplots(1, 3, figsize=(18, 4))      # trois graphiques côte à côte
ax[0].pie(g.sum(), labels=g.columns, colors=colors, autopct="%1.1f%%", startangle=90)
ax[0].set_title("Employee Turnover")
g.plot(kind="bar", stacked=True, color=colors, ax=ax[1], title="Leavers vs Stayers by Department")
g.div(g.sum(axis=1), axis=0).mul(100).plot(kind="bar", stacked=True, color=colors, ax=ax[2], title="Percentage")
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 6 : les répartitions (notebook 06)

# COMMAND ----------

pdf = df.select(cols).toPandas()   # ramener les colonnes de nombres pour les dessiner
fig, axes = plt.subplots((len(cols) + 1) // 2, 2, figsize=(12, 3 * ((len(cols) + 1) // 2)))
for ax, c in zip(axes.flatten(), cols):            # pour chaque colonne
    sns.kdeplot(pdf[c], ax=ax, fill=True)          # la courbe
    ax.axvline(pdf[c].mean(), linestyle="dashed", color="red")   # la moyenne
    ax.set_title(c)
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ce qu'on retient
# MAGIC 1. **Le même travail** se fait dans Jupyter et dans Databricks ; le code Python se reprend presque tel quel.
# MAGIC 2. **La plateforme ajoute** un endroit unique pour les données, des droits d'accès, un historique, un lignage et de la puissance de calcul à la demande.
# MAGIC 3. **Plusieurs métiers travaillent au même endroit** : Python, SQL ou graphiques sans code.
# MAGIC 4. **L'outil ne remplace pas le jugement** : lire un pourcentage, se méfier des petits échantillons, ne pas confondre lien et cause.
