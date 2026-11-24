# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Commencer ici : un environnement de données professionnel
# MAGIC Cette démo montre comment une équipe analyse des données dans un outil professionnel, **Databricks**. Aucune connaissance de Python ou de Databricks n'est nécessaire : le but n'est pas d'apprendre à programmer, mais de comprendre **le chemin, de la question à la réponse**.
# MAGIC
# MAGIC ## La question de départ
# MAGIC > Dans une entreprise de 14 999 employés, **qui part, et qu'est-ce qui accompagne ces départs ?**
# MAGIC
# MAGIC Les données sont un jeu de démonstration : une ligne par employé, sans nom.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Les mots à connaître
# MAGIC | Mot | En clair |
# MAGIC |---|---|
# MAGIC | **Notebook** | Un cahier numérique qui mélange explications, code et résultats. Vous en lisez un en ce moment. |
# MAGIC | **Cellule** | Un bloc du cahier. On l'exécute avec le bouton ▶, ou Maj + Entrée. Le résultat s'affiche dessous. |
# MAGIC | **Python** | Un langage pour donner des instructions à l'ordinateur. |
# MAGIC | **SQL** | Un langage pour poser des questions à une table. |
# MAGIC | **Bibliothèque** | Des outils déjà écrits par d'autres, que l'on ajoute avec `import`. |
# MAGIC | **Serverless** | L'ordinateur dans le cloud qui fait les calculs. Databricks le démarre à la demande. |
# MAGIC | **Volume** | Un dossier de fichiers dans Databricks. |
# MAGIC | **Table** | Des données rangées en lignes et colonnes, prêtes à être interrogées. |
# MAGIC | **Unity Catalog** | L'inventaire des données : ce qui existe, qui y a accès, d'où cela vient. |
# MAGIC | **Spark** | Le moteur de calcul, capable de répartir le travail sur plusieurs machines. |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Le parcours
# MAGIC | Notebook | Ce qu'on y fait |
# MAGIC |---|---|
# MAGIC | `01_pearson_correlation` | Mesurer le lien entre deux informations, sur 10 employés |
# MAGIC | `02_correlation_plot` | Dessiner ces liens en couleurs |
# MAGIC | `03_correlation_15000_lines` | Refaire la même chose sur 14 999 employés |
# MAGIC | `04_hr_eda_statistics` | Résumer les données en quelques chiffres |
# MAGIC | `05_hr_eda_turnover` | Qui part, et de quel département ? |
# MAGIC | `06_hr_eda_distributions` | Voir comment chaque information se répartit |
# MAGIC | `07_databricks_equivalent` | La même analyse avec les outils de la plateforme |
# MAGIC | `08_hr_numerics_analysis` | L'analyse complète : pourquoi les employés partent-ils ? |
# MAGIC | `09_patterns_scikit_learn` | Laisser la machine découvrir les profils |
# MAGIC | `10_nettoyer_sans_code` | Nettoyer des données à la souris, comme dans Power Query |
# MAGIC | `11_unity_catalog` | Visiter l'inventaire des données |
# MAGIC | *HR - Pourquoi les employés partent-ils* | Le tableau de bord |
# MAGIC
# MAGIC ## Essayez : votre première cellule
# MAGIC Cliquez dans la cellule ci-dessous, puis sur ▶. Le premier lancement peut prendre un peu de temps : l'ordinateur démarre.

# COMMAND ----------

# Une ligne qui commence par # est un commentaire : l'ordinateur l'ignore, elle sert au lecteur.
# print affiche un texte ou un résultat.
print("Bonjour ! Cette cellule vient d'être calculée dans le cloud.")
print("2 + 3 =", 2 + 3)
