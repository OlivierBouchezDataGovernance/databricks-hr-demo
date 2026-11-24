# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 6 · Voir toutes les répartitions d'un coup
# MAGIC **L'idée :** dessiner la courbe de chaque colonne sans écrire huit fois le même code. L'ordinateur **répète** l'opération à notre place.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q seaborn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : préparer et lire

# COMMAND ----------

# Dossier des fichiers (volume Unity Catalog)
DATA = "/Volumes/workspace/hr_demo/datasets"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

file_path = f"{DATA}/HR_15000 Evaluations_NumericsOnly.csv"
df = pd.read_csv(file_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : préparer une page de graphiques, puis répéter
# MAGIC Deux graphiques par ligne ; le nombre de lignes est calculé à partir du nombre de colonnes.
# MAGIC
# MAGIC Le mot `for` veut dire « pour chaque ». La ligne rouge pointillée indique la moyenne.

# COMMAND ----------

num_vars = len(df.columns)                          # nombre de colonnes
num_rows = (num_vars // 2) + (num_vars % 2)         # nombre de lignes de graphiques
fig, axes = plt.subplots(num_rows, 2, figsize=(12, 3 * num_rows))
axes = axes.flatten()                               # mettre les cases à la suite

# Pour chaque colonne : dessiner la courbe, la moyenne et le titre
for i, var in enumerate(df.columns):
    sns.kdeplot(df[var], ax=axes[i], fill=True)
    axes[i].axvline(df[var].mean(), linestyle='dashed', color='red')
    axes[i].set_title(var)

plt.tight_layout()   # éviter que les graphiques se chevauchent
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comment lire le résultat
# MAGIC - Une **grande bosse** : beaucoup d'employés ont une valeur proche.
# MAGIC - **Deux bosses** : peut-être deux groupes différents, à étudier.
# MAGIC - Pour `Work_accident`, `left` et `promotion_last_5years`, seules les valeurs 0 et 1 existent. La courbe entre les deux est un effet du dessin : un diagramme en barres conviendrait mieux.
