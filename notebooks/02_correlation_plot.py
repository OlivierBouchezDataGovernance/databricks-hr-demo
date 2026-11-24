# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 2 · Dessiner les liens
# MAGIC **La question :** avec quatre informations par employé, lesquelles sont liées entre elles ?
# MAGIC
# MAGIC Comparer les paires une par une serait long. On calcule tout en une fois, puis on le **dessine en couleurs**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q seaborn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : préparer les outils

# COMMAND ----------

import pandas as pd               # pandas : des tableaux, comme une feuille Excel, pilotés par du code
import numpy as np                # calculs numériques
import seaborn as sns             # graphiques statistiques
import matplotlib.pyplot as plt   # graphiques de base

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : construire le tableau
# MAGIC Chaque ligne du code est une colonne du tableau : satisfaction, évaluation, nombre de projets, heures par mois.

# COMMAND ----------

data = {
    "satisfaction": [1, 0.99, 0.99, 0.89, 0.89, 0.81, 0.79, 0.45, 0.36, 0.24],
    "evaluation": [0.41, 0.93, 0.97, 0.65, 0.92, 0.61, 0.84, 0.55, 0.5, 0.5],
    "projects": [4, 4, 4, 7, 4, 5, 3, 7, 2, 5],
    "hours": [174, 236, 208, 195, 165, 231, 176, 148, 132, 174]
}

df = pd.DataFrame(data)   # df = "data frame", le nom habituel d'un tableau

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : calculer tous les liens
# MAGIC Une seule instruction, `corr()`, compare chaque colonne à toutes les autres.

# COMMAND ----------

correlation_matrix = df.corr()
print(correlation_matrix)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : dessiner

# COMMAND ----------

plt.figure(figsize=(5,5))   # taille du dessin
# annot : écrire les nombres ; fmt : deux décimales ; cmap : les couleurs, du bleu (négatif) au rouge (positif)
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", square=True)
plt.title("Correlation Matrix")
plt.show()                  # afficher le dessin

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comment lire le résultat
# MAGIC - La **diagonale vaut 1** : chaque information est parfaitement liée à elle-même.
# MAGIC - Le tableau est **symétrique** : il suffit d'en lire une moitié.
# MAGIC - Le lien le plus fort ici : satisfaction et heures, environ **0,62**.
