# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Installation, à faire une seule fois
# MAGIC Cliquez sur **Run all** (en haut). Ce notebook crée un espace `workspace.hr_demo` et y copie les fichiers de la démo. Il ne touche à rien d'autre ; vous pouvez le relancer sans risque.
# MAGIC
# MAGIC À la fin, vous devez lire **Installation terminée**.

# COMMAND ----------

import os
import shutil

# Les fichiers sont dans le dossier « datasets » du projet, à côté du dossier « notebooks »
SOURCE = os.path.abspath(os.path.join(os.getcwd(), "..", "datasets"))
TARGET = "/Volumes/workspace/hr_demo/datasets"
assert os.path.isdir(SOURCE), "Dossier 'datasets' introuvable : ouvrez ce notebook depuis le clone complet du projet (Git folder)."

# Un schéma (un rayon pour ranger les tables) et un volume (un dossier pour les fichiers)
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.hr_demo COMMENT 'HR exploration demo'")
spark.sql("CREATE VOLUME IF NOT EXISTS workspace.hr_demo.datasets")

# COMMAND ----------

copied = 0
for folder, _, files in os.walk(SOURCE):
    destination = os.path.join(TARGET, os.path.relpath(folder, SOURCE)) if folder != SOURCE else TARGET
    os.makedirs(destination, exist_ok=True)
    for name in files:
        if name.endswith(".csv"):
            shutil.copyfile(os.path.join(folder, name), os.path.join(destination, name))
            print("copié :", os.path.relpath(os.path.join(folder, name), SOURCE))
            copied += 1
assert copied == 7, f"{copied} fichiers copiés au lieu de 7"
print("Installation terminée. Ouvrez maintenant 00_commencer_ici.")
