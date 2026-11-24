# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 4 · Résumer 14 999 lignes en quelques chiffres
# MAGIC Personne ne lit 14 999 lignes. On commence donc par une **analyse exploratoire** (en anglais *EDA*) : faire connaissance avec les données avant de conclure.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q seaborn scipy

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : préparer les outils et lire le fichier

# COMMAND ----------

# Dossier des fichiers (volume Unity Catalog)
DATA = "/Volumes/workspace/hr_demo/datasets"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis, mode

df = pd.read_csv(f"{DATA}/HR_15000 Evaluations_NumericsOnly.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : le résumé automatique
# MAGIC `describe()` donne pour chaque colonne : le nombre de valeurs (`count`), la moyenne (`mean`), la dispersion (`std`), le minimum, les quarts (25 %, 50 %, 75 %) et le maximum.

# COMMAND ----------

print(df.describe())
print(f"{len(df)} rows in the dataset")   # len compte les lignes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : les valeurs centrales
# MAGIC - **Moyenne** : le total divisé par le nombre de personnes.
# MAGIC - **Médiane** : la valeur du milieu ; la moitié des employés est en dessous.
# MAGIC - **Mode** : la valeur la plus fréquente.

# COMMAND ----------

print(f"Sum average monthly hours: {df['average_montly_hours'].sum()}")
print(f"Average time spent in company: {df['time_spend_company'].mean()}")
print(f"Median average monthly hours: {df['average_montly_hours'].median()}")

print(f"Mode number of projects: {df['number_project'].mode()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : la dispersion
# MAGIC Les employés se ressemblent-ils, ou y a-t-il de grands écarts ?
# MAGIC - **Étendue** : le maximum moins le minimum.
# MAGIC - **Écart-type** : l'écart habituel autour de la moyenne. La **variance** est son carré.

# COMMAND ----------

print(f"Min. average monthly hours: {df['average_montly_hours'].min()}")
print(f"Max. average monthly hours: {df['average_montly_hours'].max()}")

r_min, r_max = df['average_montly_hours'].min(), df['average_montly_hours'].max()
print(f"Range average monthly hours: {r_min}, {r_max} => {r_max - r_min}")

print(f"Variance average monthly hours: {df['average_montly_hours'].var()}")
print(f"Standard deviation average monthly hours: {df['average_montly_hours'].std()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 5 : la forme
# MAGIC - **Asymétrie** (*skewness*) : proche de 0, la répartition est équilibrée à gauche et à droite.
# MAGIC - **Aplatissement** (*kurtosis*) : négatif, la répartition est plus plate que la courbe en cloche classique.

# COMMAND ----------

print(f"Skewness average monthly hours: {skew(df['average_montly_hours'])}")
print(f"Kurtosis average monthly hours: {kurtosis(df['average_montly_hours'])}")

# COMMAND ----------

# MAGIC %md
# MAGIC **Ce que l'on apprend :** environ **201 heures** par mois en moyenne, de 96 à 310 heures. La moyenne et la médiane (200) se touchent presque. Mais la moyenne cache souvent une partie de l'histoire : regardons la courbe.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 6 : dessiner la répartition des heures
# MAGIC Plus la courbe est haute, plus il y a d'employés autour de cette valeur.

# COMMAND ----------

plt.figure(figsize=(5,3))
sns.kdeplot(df['average_montly_hours'], fill=True)
plt.title("Distribution of Average Monthly Hours")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **À observer :** regardez si la courbe a une ou plusieurs bosses. La moyenne seule ne le dirait jamais.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 7 : compter les projets
# MAGIC Un **histogramme** compte combien d'employés ont 2, 3, 4… projets. Le cas le plus fréquent est **4 projets**.

# COMMAND ----------

plt.figure(figsize=(6,4))
plt.hist(df['number_project'])
plt.xlabel("Number of Projects")   # titre de l'axe horizontal
plt.ylabel("Frequency")            # titre de l'axe vertical
plt.title("Frequency of Number of Projects")
plt.show()
