# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 10 · Nettoyer des données à la souris, comme dans Power Query
# MAGIC Trois fichiers HR arrivent **sales** : colonnes à corriger, totaux mélangés aux données, noms écrits de plusieurs façons. On les nettoie avec **Lakeflow Designer**, l'outil graphique de Databricks : on glisse des tables, on relie des boîtes, on choisit dans des menus.
# MAGIC
# MAGIC Ce notebook est le **guide**. On travaille dans Designer, puis on revient ici à la fin pour **vérifier** le résultat.
# MAGIC
# MAGIC | Dans Power Query | Dans Lakeflow Designer |
# MAGIC |---|---|
# MAGIC | Obtenir les données | **Source** |
# MAGIC | Étapes appliquées | Les boîtes reliées sur le **canevas** |
# MAGIC | Filtrer les lignes | **Filter** |
# MAGIC | Choisir, renommer les colonnes | **Select** |
# MAGIC | Changer le type, remplacer, supprimer les espaces, colonne personnalisée | **Prepare** |
# MAGIC | Fusionner des requêtes | **Join** |
# MAGIC | Ajouter des requêtes | **Combine** › Union |
# MAGIC | Regrouper par | **Aggregate** |
# MAGIC | Fermer et charger | **Output** › Run |
# MAGIC | Actualisation planifiée | **Schedule** |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Avant la démo : charger les fichiers bruts
# MAGIC Cette cellule crée les tables de départ, **sans rien corriger** (tout est en texte). À exécuter une fois.

# COMMAND ----------

from pyspark.sql import functions as F

DIRTY = "/Volumes/workspace/hr_demo/datasets/dirty"
for n in (1, 2, 3):
    (spark.read.csv(f"{DIRTY}/hr_dirty_{n}.csv", header=True, sep=";")      # sans inferSchema : tout reste en texte
        .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"workspace.hr_demo.hr_raw_{n}"))
    spark.sql(f"COMMENT ON TABLE workspace.hr_demo.hr_raw_{n} IS 'HR demo: dirty file {n}, loaded as text, nothing corrected'")
for name, note in (("ref_department_source", "as delivered with file 2; its ids do NOT match file 2 (see ref_department_corrected)"),
                   ("ref_department_corrected", "ids deduced by comparing file 2 with the clean reference, row by row")):
    (spark.read.csv(f"{DIRTY}/{name}.csv", header=True, sep=";")
        .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"workspace.hr_demo.{name}"))
    spark.sql(f"COMMENT ON TABLE workspace.hr_demo.{name} IS 'HR demo: departments, {note}'")
print("Tables prêtes : hr_raw_1, hr_raw_2, hr_raw_3, ref_department_source, ref_department_corrected")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Voir les problèmes
# MAGIC Combien de façons d'écrire un département dans le fichier 1 ? Les crochets rendent les espaces visibles.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT concat('[', sales, ']') AS departement, count(*) AS lignes
# MAGIC FROM workspace.hr_demo.hr_raw_1 GROUP BY sales ORDER BY lignes DESC

# COMMAND ----------

# MAGIC %md
# MAGIC | Problème | Exemple | Ce qu'on fait |
# MAGIC |---|---|---|
# MAGIC | Lignes qui ne sont pas des employés | une ligne vide, `AVERAGES`, une ligne de moyennes | Filtrer |
# MAGIC | Département écrit de plusieurs façons | `HR`, `Human Resources`, `mgmt`, `sales` suivi d'espaces | Nettoyer, remplacer |
# MAGIC | Fichier 2 : un numéro au lieu du nom | `8` | Joindre avec une table |
# MAGIC | Scores sans virgule | `38` au lieu de 0,38 | Formule |
# MAGIC | Score ambigu | `1` peut venir de 0,1 ou de 1 ; `9` de 0,09 ou de 0,9 | Laisser vide plutôt que deviner |
# MAGIC | Heures multipliées par 10 | `1600` | Formule |
# MAGIC | Ancienneté impossible | `33` ans | Remplacer par 3 |
# MAGIC | Salaire en montant | `460` | Classer : low, medium, high |

# COMMAND ----------

# MAGIC %md
# MAGIC # La démo, clic par clic
# MAGIC ## 1. Créer la préparation
# MAGIC 1. Dans la barre de gauche : **+ New** › **Visual data prep**.
# MAGIC 2. Cliquez sur le nom en haut et tapez `HR nettoyage`.
# MAGIC 3. À côté de **Schedule**, choisissez le calcul **Serverless**.
# MAGIC 4. Pour tout garder au même endroit, déplacez le fichier dans le dossier **`hr-demo`** (menu du fichier › **Move**).
# MAGIC
# MAGIC Si **Visual data prep** n'apparaît pas, l'outil n'est pas activé dans ce workspace : passez au *plan B* en bas.
# MAGIC
# MAGIC ## 2. Apporter les données
# MAGIC Depuis le panneau **Catalog**, dépliez `workspace` › `hr_demo` et **glissez** sur le canevas : `hr_raw_1`, `hr_raw_2`, `hr_raw_3`, `ref_department_corrected`.
# MAGIC
# MAGIC ## 3. Remplacer le numéro de département par son nom
# MAGIC 1. Ajoutez une boîte **Join** et reliez-y `hr_raw_2` et `ref_department_corrected`.
# MAGIC 2. Condition : `sales` = `department_id`. Utilisez la sortie **Matched**.
# MAGIC 3. Ajoutez **Select** après : retirez `sales` et `department_id`, renommez `dept_name` en `sales`, et placez `sales` juste avant `salary`.
# MAGIC
# MAGIC ## 4. Empiler les trois fichiers
# MAGIC Boîte **Combine** › **Union** › **All** : reliez `hr_raw_1`, la sortie du **Select**, et `hr_raw_3`. Les colonnes doivent être dans le même ordre.
# MAGIC
# MAGIC ## 5. Enlever ce qui n'est pas un employé
# MAGIC Boîte **Filter** : `number_project` **is not null**. Suivez la sortie **Included** ; regardez **Excluded** : ce sont les lignes de totaux.
# MAGIC
# MAGIC ## 6. Nettoyer les départements
# MAGIC Boîte **Prepare**, colonne `sales`, une action à la fois :
# MAGIC 1. **Trim** : enlever les espaces
# MAGIC 2. **Text case** : minuscules
# MAGIC 3. **Replace value** : `human resources` → `hr`
# MAGIC 4. **Replace value** : `managment` → `management`
# MAGIC 5. **Replace value** : `mgmt` → `management`
# MAGIC
# MAGIC ## 7. Corriger les nombres
# MAGIC Même boîte **Prepare** (ou une seconde). D'abord **Change type** en *integer* pour les colonnes de nombres et `salary`, puis **Formula** pour chaque ligne :
# MAGIC
# MAGIC | Nouvelle colonne | Formule à coller |
# MAGIC |---|---|
# MAGIC | `satisfaction` | `CASE WHEN satisfaction_level IN (1, 9) THEN NULL WHEN satisfaction_level >= 10 THEN satisfaction_level / 100 ELSE satisfaction_level / 10 END` |
# MAGIC | `evaluation` | `CASE WHEN last_evaluation = 1 THEN 1 WHEN last_evaluation >= 10 THEN last_evaluation / 100 ELSE last_evaluation / 10 END` |
# MAGIC | `average_monthly_hours` | `CASE WHEN average_montly_hours > 400 THEN average_montly_hours / 10 ELSE average_montly_hours END` |
# MAGIC | `years` | `CASE WHEN time_spend_company = 33 THEN 3 ELSE time_spend_company END` |
# MAGIC | `salary_class` | `CASE WHEN salary < 1000 THEN 'low' WHEN salary < 5000 THEN 'medium' ELSE 'high' END` |
# MAGIC
# MAGIC ## 8. Garder les bonnes colonnes
# MAGIC Boîte **Select** : gardez `satisfaction`, `evaluation`, `number_project`, `average_monthly_hours`, `years`, `Work_accident`, `left`, `promotion_last_5years`, `sales`, `salary_class`. Renommez `left` en `has_left` et `sales` en `department`.
# MAGIC
# MAGIC ## 9. Enregistrer
# MAGIC Boîte **Output** : **Table**, nom `hr_clean_designer`, emplacement `workspace` › `hr_demo`, mode **Overwrite**, puis **Run**.
# MAGIC
# MAGIC 👉 **À dire :** pendant la construction, on voit un **aperçu** des 1 000 premières lignes. **Run** traite toutes les lignes. **Schedule** relance tout automatiquement, comme une actualisation planifiée.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Le piège à montrer : une jointure qui marche, mais qui ment
# MAGIC La table de départements **livrée avec le fichier 2** (`ref_department_source`) se joint sans erreur. Pourtant, ses numéros ne sont pas ceux du fichier : elle appelle *support* le numéro 8, alors que c'est *sales*. Comparez :

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT r.sales AS numero, count(*) AS lignes, s.dept_name AS nom_livre, c.dept_name AS nom_reel
# MAGIC FROM workspace.hr_demo.hr_raw_2 r
# MAGIC JOIN workspace.hr_demo.ref_department_source s ON r.sales = s.department_id
# MAGIC JOIN workspace.hr_demo.ref_department_corrected c ON r.sales = c.department_id
# MAGIC GROUP BY ALL ORDER BY lignes DESC

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ Aucun message d'erreur, des chiffres plausibles, et **tous les départements faux**. On ne l'a vu qu'en comparant, ligne par ligne, avec le fichier propre de référence. Un outil facile ne remplace pas une **table de référence** tenue par un responsable : c'est la gouvernance des données.

# COMMAND ----------

# MAGIC %md
# MAGIC # Plan B : les mêmes étapes, en SQL
# MAGIC Si Designer n'est pas disponible, ou pour montrer ce qui se passe sous le capot. Chaque `|>` est une **étape appliquée**, dans l'ordre, comme dans Power Query.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.hr_demo.hr_clean_sql
# MAGIC COMMENT 'HR demo: the three dirty files, cleaned in SQL; ambiguous satisfaction scores (1, 9) left empty' AS
# MAGIC WITH file2 AS (   -- étape 3 : le nom du département au lieu du numéro
# MAGIC   SELECT r.* EXCEPT (sales, salary), d.dept_name AS sales, r.salary
# MAGIC   FROM workspace.hr_demo.hr_raw_2 r JOIN workspace.hr_demo.ref_department_corrected d ON r.sales = d.department_id),
# MAGIC stacked AS (      -- étape 4 : empiler
# MAGIC   SELECT * FROM workspace.hr_demo.hr_raw_1 UNION ALL SELECT * FROM file2 UNION ALL SELECT * FROM workspace.hr_demo.hr_raw_3)
# MAGIC FROM stacked
# MAGIC |> WHERE number_project IS NOT NULL                                                     -- étape 5 : filtrer
# MAGIC |> EXTEND lower(trim(sales)) AS d                                                       -- étape 6 : espaces, minuscules
# MAGIC |> EXTEND CASE d WHEN 'human resources' THEN 'hr' WHEN 'managment' THEN 'management'
# MAGIC                  WHEN 'mgmt' THEN 'management' ELSE d END AS department                 --           remplacer
# MAGIC |> EXTEND CAST(satisfaction_level AS INT) AS s, CAST(last_evaluation AS INT) AS e,      -- étape 7 : types
# MAGIC           CAST(average_montly_hours AS INT) AS h, CAST(time_spend_company AS INT) AS t, CAST(salary AS INT) AS m
# MAGIC |> SELECT CASE WHEN s IN (1, 9) THEN NULL WHEN s >= 10 THEN s / 100 ELSE s / 10 END AS satisfaction,
# MAGIC           CASE WHEN e = 1 THEN 1 WHEN e >= 10 THEN e / 100 ELSE e / 10 END AS evaluation,
# MAGIC           CAST(number_project AS INT) AS number_project,
# MAGIC           CASE WHEN h > 400 THEN h / 10 ELSE h END AS average_monthly_hours,
# MAGIC           CASE WHEN t = 33 THEN 3 ELSE t END AS years,
# MAGIC           CAST(Work_accident AS INT) AS Work_accident, CAST(`left` AS INT) AS has_left,
# MAGIC           CAST(promotion_last_5years AS INT) AS promotion_last_5years, department,
# MAGIC           CASE WHEN m < 1000 THEN 'low' WHEN m < 5000 THEN 'medium' ELSE 'high' END AS salary_class

# COMMAND ----------

# MAGIC %md
# MAGIC # Vérifier
# MAGIC On contrôle le résultat de Designer s'il existe, et celui du plan B. Si un contrôle échoue, la ligne affiche **NON**.

# COMMAND ----------

def check(table):
    """Compare une table nettoyée avec les valeurs attendues."""
    df = spark.table(table)
    r = df.agg(F.count("*").alias("lignes"), F.sum("has_left").alias("partis"), F.countDistinct("department").alias("departements"),
               F.max("average_monthly_hours").alias("heures_max"), F.max("years").alias("annees_max"),
               F.sum(F.col("satisfaction").isNull().cast("int")).alias("satisfaction_vide"),
               F.max("satisfaction").alias("satisfaction_max"),
               F.sum((F.col("department") == "sales").cast("int")).alias("employes_sales")).first().asDict()
    expected = {"lignes": 15001, "partis": 3571, "departements": 10, "heures_max": 310, "annees_max": ANNEES_MAX,
                "satisfaction_vide": 884, "satisfaction_max": 0.99, "employes_sales": SALES}
    rows = [(k, float(r[k] or 0), float(v), "OK" if abs(float(r[k] or 0) - v) < 1e-9 else "NON") for k, v in expected.items()]
    print(table)
    display(spark.createDataFrame(rows, "controle string, obtenu double, attendu double, resultat string"))
    return all(x[3] == "OK" for x in rows)


ANNEES_MAX, SALES = 10, 4140

assert check("workspace.hr_demo.hr_clean_sql"), "Le plan B ne donne pas les valeurs attendues"
if spark.catalog.tableExists("workspace.hr_demo.hr_clean_designer"):
    check("workspace.hr_demo.hr_clean_designer")
else:
    print("hr_clean_designer n'existe pas encore : faites la démo dans Designer, puis relancez cette cellule.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ce qu'on retient
# MAGIC 1. On nettoie **à la souris**, comme dans Power Query, et chaque étape reste visible.
# MAGIC 2. Le résultat est une **table partagée**, pas un fichier sur un ordinateur : les notebooks et les tableaux de bord peuvent l'utiliser.
# MAGIC 3. Il reste **15 001** lignes, contre 14 999 dans le fichier propre : une ligne est répétée à chaque raccord entre deux fichiers. Sans numéro d'employé, on ne peut pas l'enlever sans risquer d'effacer de vraies personnes.
# MAGIC 4. **Ne pas deviner** : 884 satisfactions ambiguës restent vides.
