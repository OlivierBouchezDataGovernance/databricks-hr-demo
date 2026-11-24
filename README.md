# Démo Databricks : hr-demo

**Pourquoi les employés partent-ils ?** Une démo pas à pas pour découvrir un environnement de données professionnel, sans connaître ni Python ni Databricks. Toutes les explications sont dans les notebooks, en français.

Vous allez : explorer des données, dessiner des graphiques, nettoyer des fichiers à la souris (comme dans Power Query), laisser la machine trouver des profils, ouvrir un tableau de bord et visiter le catalogue des données.

## 1. Créer un compte gratuit (Databricks Free Edition)

1. Ouvrez la [page d'inscription](https://login.databricks.com/?dbx_source=docs&intent=CE_SIGN_UP).
2. Choisissez une méthode : code reçu par e-mail, **Google** ou **Microsoft**.
3. Databricks crée votre espace de travail (*workspace*). C'est tout.

À savoir :
- La Free Edition est faite pour apprendre ; l'**usage commercial n'est pas autorisé**.
- Il y a un **quota de calcul**. S'il est dépassé, les calculs s'arrêtent jusqu'à la fin de la journée (dans des cas extrêmes, du mois) ; vos données sont conservées.
- Détails : [présentation](https://docs.databricks.com/aws/en/getting-started/free-edition) et [limites](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

N'y mettez pas de données personnelles ni de données de votre entreprise.

## 2. Copier ce projet dans Databricks (Git folder)

Un **clone** est une copie du projet, reliée à GitHub. Aucun compte GitHub n'est nécessaire si ce dépôt est public.

1. Dans la barre de gauche : **Workspace** › **Home**.
2. En haut à droite : **Create** › **Git folder**.
3. **Git repository URL** : `https://github.com/OlivierBouchezDataGovernance/databricks-hr-demo.git`
4. **Git provider** : GitHub. Le nom du dossier se remplit seul.
5. Cliquez sur **Create Git folder**.

Le dossier `databricks-hr-demo` apparaît dans votre Home.

*Pour recevoir une mise à jour plus tard :* cliquez sur **Git** à côté du nom du dossier, puis **Pull**.

## 3. Installer la démo

1. Ouvrez `databricks-hr-demo` › `notebooks` › **`00_installation`**.
2. En haut à droite, choisissez **Serverless**.
3. Cliquez sur **Run all** et attendez **Installation terminée**. Le premier démarrage peut prendre un peu de temps.

## 4. Suivre le parcours

Ouvrez chaque notebook dans l'ordre, lisez, et lancez les cellules avec ▶ (ou Maj + Entrée).

| Notebook | Ce qu'on y découvre |
|---|---|
| `00_commencer_ici` | Les mots à connaître, une première cellule |
| `01` à `03` | Mesurer et dessiner des liens, de 10 à 14 999 employés |
| `04` à `06` | Résumer, compter, voir les répartitions |
| `07_databricks_equivalent` | La même analyse avec une table, SQL et Spark |
| **`08_hr_numerics_analysis`** | **L'analyse complète. À lancer avant 09, 11 et le tableau de bord** |
| `09_patterns_scikit_learn` | Apprentissage automatique : groupes, arbre de décision |
| `10_nettoyer_sans_code` | Nettoyer à la souris avec Lakeflow Designer (ou en SQL) |
| `11_unity_catalog` | L'inventaire des données : sens, accès, historique, lignage. *À lancer après 08 et 10* |

**Tableau de bord :** après le notebook 08, ouvrez `dashboard` › `hr_departs.lvdash.json`. S'il le demande, choisissez le SQL warehouse proposé.

Peu de temps ? Faites `00_installation` → `00_commencer_ici` → `08` → tableau de bord → `10`.

## En cas de problème

| Message | Que faire |
|---|---|
| `Dossier 'datasets' introuvable` | Ouvrez le notebook depuis le Git folder, pas depuis une copie isolée |
| `No module named 'seaborn'` | Lancez la cellule **Étape 0** en haut du notebook, ou **Run all** |
| `TABLE_OR_VIEW_NOT_FOUND` | Lancez d'abord `00_installation`, puis `08` (et `10` pour le 11) |
| Schéma ou catalogue introuvable | La démo suppose un catalogue nommé `workspace` |
| Rien ne démarre | Le quota gratuit du jour est peut-être atteint : réessayez demain |
| **Visual data prep** absent du menu **+ New** | Utilisez le *plan B en SQL* du notebook 10 |

**Tout effacer**, dans le SQL Editor : `DROP SCHEMA workspace.hr_demo CASCADE` (supprime toute la démo, sans retour possible).

## Les données

Un jeu de démonstration de 14 999 lignes, sans nom ni numéro d'employé, qui semble **simulé**. Environ une ligne sur cinq est une copie exacte d'une autre. Les fichiers `datasets/dirty` contiennent des erreurs, exprès ; `ref_department_corrected.csv` a été déduit en comparant avec le fichier propre.

Cette démo sert à apprendre, **pas à décider sur des personnes**.

## Contenu du dépôt

`notebooks/` la démo · `datasets/` les fichiers CSV · `dashboard/` le tableau de bord · `docs/` le script de démonstration de 5 minutes

Réalisé par Olivier Bouchez, [olivier-bouchez.com](https://olivier-bouchez.com), 2026.
