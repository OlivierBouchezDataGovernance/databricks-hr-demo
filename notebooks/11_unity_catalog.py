# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 11 · Unity Catalog, l'inventaire des données
# MAGIC Dans une entreprise, les questions sont toujours les mêmes : **quelles données avons-nous ? que veulent-elles dire ? qui peut les voir ? d'où viennent-elles ? qu'est-ce qui a changé ?** Unity Catalog y répond, au même endroit.
# MAGIC
# MAGIC Pensez à une **bibliothèque** :
# MAGIC
# MAGIC | Bibliothèque | Unity Catalog | Dans notre démo |
# MAGIC |---|---|---|
# MAGIC | Le bâtiment | **Catalogue** | `workspace` |
# MAGIC | Un rayon | **Schéma** | `hr_demo` (HR), `statbel` (statistiques belges) |
# MAGIC | Un livre | **Table** ou **vue** | `hr_employee` |
# MAGIC | Une boîte de documents | **Volume** | `datasets` (les fichiers) |
# MAGIC | La fiche du livre | **Description, tags** | le sens de chaque colonne |
# MAGIC | La carte de lecteur | **Permissions** | qui peut lire |
# MAGIC
# MAGIC Une table a donc une adresse en trois parties : `workspace.hr_demo.hr_employee`.
# MAGIC
# MAGIC Lancez les notebooks **08** et **10** avant celui-ci.

# COMMAND ----------

# MAGIC %md
# MAGIC # La visite, à la souris
# MAGIC 1. Barre de gauche : **Catalog** › `workspace` › `hr_demo` › `hr_employee`.
# MAGIC 2. **Overview** : les colonnes et leurs descriptions. Le bouton **AI generate**, s'il est présent, propose des descriptions à relire.
# MAGIC 3. **Sample data** : un aperçu des lignes.
# MAGIC 4. **Details** : propriétaire, date de création, format.
# MAGIC 5. **Permissions** : qui a accès. **Grant** donne un droit, **Revoke** le retire.
# MAGIC 6. **History** : chaque modification, avec son auteur.
# MAGIC 7. **Lineage** › **See lineage graph** : le **graphique** qui relie fichier, table, vues et tableau de bord.
# MAGIC 8. En haut de la page, la **recherche** : tapez `turnover`, la vue apparaît avec sa description.
# MAGIC 9. Même visite sur `statbel` › `silver_ref_municipality` : un vrai jeu de données public.
# MAGIC
# MAGIC Les cellules suivantes montrent les mêmes informations en SQL.

# COMMAND ----------

# MAGIC %md ## 1. Quelles données avons-nous ?

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT table_schema AS schema, table_name AS nom, table_type AS type, comment AS description
# MAGIC FROM workspace.information_schema.tables
# MAGIC WHERE table_schema IN ('hr_demo', 'statbel') AND table_name NOT LIKE 'bronze%'
# MAGIC ORDER BY schema, nom

# COMMAND ----------

# MAGIC %md ## 2. Que veulent-elles dire ?
# MAGIC Chaque colonne a un type et une description, écrits une fois pour tous.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT column_name AS colonne, data_type AS type, comment AS description
# MAGIC FROM workspace.information_schema.columns
# MAGIC WHERE table_schema = 'hr_demo' AND table_name = 'hr_employee'
# MAGIC ORDER BY ordinal_position

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Classer avec des étiquettes
# MAGIC Un **tag** sert à retrouver et à classer : domaine, niveau de confidentialité… On en pose deux, puis on les relit.

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE workspace.hr_demo.hr_employee SET TAGS ('domain' = 'HR', 'demo' = 'yes');
# MAGIC SELECT schema_name AS schema, table_name AS nom, tag_name AS tag, tag_value AS valeur
# MAGIC FROM workspace.information_schema.table_tags
# MAGIC WHERE schema_name IN ('hr_demo', 'statbel') ORDER BY schema, nom, tag

# COMMAND ----------

# MAGIC %md ## 4. Qui peut y accéder ?
# MAGIC Les droits se donnent à un niveau et descendent : un droit sur le schéma vaut pour toutes ses tables.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW GRANTS ON SCHEMA workspace.hr_demo

# COMMAND ----------

# MAGIC %md
# MAGIC Exemple de droit de lecture (non exécuté ici) :
# MAGIC ```sql
# MAGIC GRANT USE SCHEMA, SELECT ON SCHEMA workspace.hr_demo TO `equipe_hr`;
# MAGIC ```

# COMMAND ----------

# MAGIC %md ## 5. Qu'est-ce qui a changé ?

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY workspace.hr_demo.hr_employee LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ### Revenir en arrière dans le temps
# MAGIC On peut relire une **version précédente** de la table, par exemple après une erreur.

# COMMAND ----------

history = spark.sql("DESCRIBE HISTORY workspace.hr_demo.hr_employee LIMIT 3").select("version", "operation").collect()
for h in history:
    n = spark.sql(f"SELECT count(*) FROM workspace.hr_demo.hr_employee VERSION AS OF {h.version}").first()[0]
    print(f"version {h.version} ({h.operation}) : {n:,} lignes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. D'où viennent-elles, où vont-elles ?
# MAGIC Le **lignage** est enregistré tout seul quand on travaille. Il peut mettre un peu de temps à apparaître. Le plus parlant reste le graphique : **Catalog** › `hr_employee` › **Lineage**.

# COMMAND ----------

try:
    display(spark.sql("""
        SELECT DISTINCT source_table_full_name AS depuis, target_table_full_name AS vers, entity_type AS par
        FROM system.access.table_lineage
        WHERE (source_table_full_name LIKE 'workspace.hr_demo.%' OR target_table_full_name LIKE 'workspace.hr_demo.%')
          AND source_table_full_name IS NOT NULL AND target_table_full_name IS NOT NULL
          AND event_date >= current_date() - 7
        ORDER BY depuis, vers"""))
except Exception as e:   # pas le droit de lire les tables système : le graphique suffit
    print("Lignage en SQL non disponible pour ce compte :", type(e).__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ce qu'on retient
# MAGIC | Question | Réponse |
# MAGIC |---|---|
# MAGIC | Quelles données ? | Le catalogue et la recherche |
# MAGIC | Que veulent-elles dire ? | Descriptions et tags |
# MAGIC | Qui y accède ? | Permissions |
# MAGIC | Qu'est-ce qui a changé ? | History |
# MAGIC | D'où viennent-elles ? | Lineage |
# MAGIC
# MAGIC **Un outil facile sans gouvernance produit vite des chiffres faux** (souvenez-vous des départements du notebook 10). Le catalogue est ce qui permet à toute une équipe de faire confiance aux données.
