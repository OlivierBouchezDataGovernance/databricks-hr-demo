# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 5 · Qui part ?
# MAGIC **La question :** combien d'employés sont partis, et de quels départements ?
# MAGIC
# MAGIC On utilise le fichier complet, qui contient aussi le département. Attention au nom : la colonne du département s'appelle `sales`, et l'un des départements s'appelle aussi *sales*. Des noms peu clairs comme celui-ci sont une des raisons d'être de la **gouvernance des données**.

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

file_path = f"{DATA}/HR_15000 Evaluations - CLEAN.csv"
df = pd.read_csv(file_path)

colors = ["green", "red"]        # vert = resté, rouge = parti
labels = ["stayed","left"]       # stayed = resté, left = parti

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : la vue d'ensemble

# COMMAND ----------

# Dans la colonne "left", 0 = resté et 1 = parti : on compte les deux groupes
counts = [ len(df[ df['left'] == 0 ]), df['left'].sum() ]
plt.figure(figsize=(3, 3))
plt.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
plt.title("Employee Turnover")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Résultat :** 3 571 départs sur 14 999 employés, soit **23,8 %**, près d'un sur quatre.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : compter par département
# MAGIC C'est l'équivalent d'un **tableau croisé dynamique** dans Excel : une ligne par département, une colonne pour les restés (0), une pour les partis (1).

# COMMAND ----------

grouped = df.groupby(['sales', 'left']).size().reset_index(name='count')        # compter chaque groupe
grouped = grouped.pivot(index='sales', columns='left', values='count').fillna(0) # disposer en tableau
grouped = grouped.sort_values(by=[1, 0], ascending=[False, True])                # le plus de départs en haut
print(grouped)

# Barres empilées : restés en vert, partis en rouge
fig, ax = plt.subplots(figsize=(6, 3))
grouped.plot(kind='bar', stacked=True, color=colors, ax=ax)
plt.legend(labels, title="Status")
plt.xlabel("Department")
plt.ylabel("Count")
plt.title("Leavers vs Stayers by Department")
plt.xticks(rotation=45)   # incliner les noms pour qu'ils restent lisibles
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Piège :** *sales* compte le plus de départs (1 014). Est-ce le département le plus touché ? Pas forcément : c'est aussi le plus grand.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : les mêmes chiffres côte à côte
# MAGIC Un seul réglage change : `stacked=False`.

# COMMAND ----------

fig, ax = plt.subplots(figsize=(6, 3))
grouped.plot(kind='bar', stacked=False, color=colors, ax=ax)
plt.legend(labels, title="Status")
plt.xlabel("Department")
plt.ylabel("Count")
plt.title("Leavers vs Stayers by Department (Grouped)")
plt.xticks(rotation=45)
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 5 : comparer en pourcentage
# MAGIC Pour comparer des départements de tailles différentes, on divise par le total de chacun.

# COMMAND ----------

data_percentage = grouped.div(grouped.sum(axis=1), axis=0) * 100
print(data_percentage)
fig, ax = plt.subplots(figsize=(6, 3))
data_percentage.plot(kind='bar', stacked=True, color=colors, ax=ax)
plt.legend(labels, title="Status")
plt.xlabel("Department")
plt.ylabel("Percentage")
plt.title("Leavers vs Stayers by Department (Percentage)")
plt.xticks(rotation=45)
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ce qu'on retient
# MAGIC - La plus forte proportion de départs est dans **hr** (29,1 %), la plus faible dans **management** (14,4 %).
# MAGIC - **sales**, premier en nombre, est à 24,5 %, tout près de la moyenne générale.
# MAGIC - **Le choix du graphique change l'histoire racontée.** Nombre ou pourcentage : il faut savoir ce que l'on regarde.
