# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 3 · Passer à l'échelle
# MAGIC **La question :** que devient la même analyse avec **14 999 employés** ?
# MAGIC
# MAGIC Le code est presque le même que pour 10 personnes. Seule la source change : on lit un **fichier**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q seaborn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : indiquer où sont les données
# MAGIC Les fichiers sont dans un **volume**, un dossier géré par Databricks. Toute l'équipe autorisée lit la même copie, au lieu de s'envoyer des fichiers par e-mail.
# MAGIC
# MAGIC Pour le voir : menu **Catalog** › `workspace` › `hr_demo` › Volumes › `datasets`.

# COMMAND ----------

# L'adresse du dossier, gardée dans une variable pour ne l'écrire qu'une fois
DATA = "/Volumes/workspace/hr_demo/datasets"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : lire le fichier
# MAGIC Un fichier **CSV** est un simple fichier texte, avec une ligne par employé et des virgules entre les valeurs.

# COMMAND ----------

import pandas as pd
import numpy as np

# Lire le fichier et le ranger dans un tableau
df = pd.read_csv(f"{DATA}/HR_15000 Evaluations_NumericsOnly.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : calculer les liens
# MAGIC Si l'affichage est coupé par `...`, c'est seulement faute de place : le dessin de l'étape 4 montre tout.

# COMMAND ----------

correlation_matrix = df.corr()
print(correlation_matrix)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : dessiner

# COMMAND ----------

import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", square=True)
plt.title("Correlation Matrix")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comment lire le résultat
# MAGIC Les colonnes : `satisfaction_level` (satisfaction), `last_evaluation` (évaluation), `number_project` (projets), `average_montly_hours` (heures par mois ; la faute de frappe vient du fichier), `time_spend_company` (années dans l'entreprise), `Work_accident` (accident), `left` (1 = parti), `promotion_last_5years` (promotion).
# MAGIC
# MAGIC - **`left` et `satisfaction_level` : -0,39.** C'est le lien le plus marqué avec les départs : les employés partis étaient en général moins satisfaits.
# MAGIC - **Projets et heures : 0,42.** Plus de projets va avec plus d'heures.
# MAGIC - **Satisfaction et évaluation : 0,11.** Sur 10 employés, on trouvait 0,56 : un petit échantillon peut tromper.
# MAGIC
# MAGIC ⚠ Un lien n'est toujours pas une cause.
