# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 1 · Mesurer le lien entre deux informations
# MAGIC **La question :** les employés les plus satisfaits sont-ils aussi les mieux évalués ?
# MAGIC
# MAGIC On commence petit, avec **10 employés**, pour comprendre la méthode.
# MAGIC
# MAGIC **La mesure :** le *coefficient de corrélation de Pearson*, un nombre entre -1 et 1.
# MAGIC
# MAGIC | Valeur | Ce que cela veut dire |
# MAGIC |---|---|
# MAGIC | proche de **1** | les deux montent ensemble |
# MAGIC | proche de **0** | pas de lien en ligne droite |
# MAGIC | proche de **-1** | quand l'un monte, l'autre descend |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 0 : installer les outils
# MAGIC Une **bibliothèque** est un outil écrit par d'autres. `%pip install` la télécharge et l'installe pour ce notebook : c'est l'équivalent d'installer une application. Le texte technique affiché dessous est normal.

# COMMAND ----------

# MAGIC %pip install -q scipy

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : préparer les outils
# MAGIC On ajoute deux boîtes à outils : `numpy` pour les nombres, `scipy` pour les statistiques. Cette cellule n'affiche rien, c'est normal.

# COMMAND ----------

import numpy as np                    # calculs sur des listes de nombres ; "np" est un surnom
from scipy.stats import pearsonr      # l'outil qui calcule la corrélation

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : saisir les données
# MAGIC Deux listes de 10 nombres. Le premier nombre de chaque liste concerne le même employé, le deuxième aussi, etc.

# COMMAND ----------

# Satisfaction des 10 employés (0 = pas du tout satisfait, 1 = très satisfait)
satisfaction = np.array([1, 0.99, 0.99, 0.89, 0.89, 0.81, 0.79, 0.45, 0.36, 0.24])
# Dernière évaluation des mêmes employés (0 = faible, 1 = excellente)
evaluation = np.array([0.41, 0.93, 0.97, 0.65, 0.92, 0.61, 0.84, 0.55, 0.5, 0.5])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 3 : calculer et afficher

# COMMAND ----------

# pearsonr donne deux résultats : on garde le premier, et "_" veut dire "je n'utilise pas le second"
correlation, _ = pearsonr(satisfaction, evaluation)
print("Pearson correlation:", correlation)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comment lire le résultat
# MAGIC Environ **0,56** : un lien positif, moyen. Dans ce petit groupe, satisfaction et évaluation montent plutôt ensemble.
# MAGIC
# MAGIC ⚠ **Deux pièges**
# MAGIC - 10 personnes, c'est très peu. Le notebook 03 refait le calcul sur 14 999 employés : le résultat change beaucoup.
# MAGIC - **Un lien n'est pas une cause.** On ne sait pas si l'un provoque l'autre.
