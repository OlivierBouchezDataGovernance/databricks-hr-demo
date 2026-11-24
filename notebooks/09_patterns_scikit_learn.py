# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 9 · Laisser la machine découvrir les profils
# MAGIC Dans le notebook 08, **nous** avons tracé à l'œil les limites de trois profils. Ici, on demande à l'ordinateur de les trouver **seul**, avec **scikit-learn**, une bibliothèque d'apprentissage automatique (*machine learning*).
# MAGIC
# MAGIC | Question | Méthode | En clair |
# MAGIC |---|---|---|
# MAGIC | Y a-t-il des groupes parmi les partis ? | **K-Means** | Ranger ensemble ceux qui se ressemblent |
# MAGIC | Quelles règles séparent partis et restés ? | **Arbre de décision** | Une suite de questions oui / non |
# MAGIC | Peut-on mieux prévoir ? | **Forêt aléatoire** | Le vote de 200 arbres |
# MAGIC | Qu'est-ce qui compte le plus ? | **Importance par permutation** | Mélanger une colonne et voir si la prévision se dégrade |
# MAGIC
# MAGIC Lancez d'abord le notebook 08 : il crée la table utilisée ici. Ce notebook **lit** la table sans la modifier.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 1 : installer et préparer les outils

# COMMAND ----------

# MAGIC %pip install -q scikit-learn plotly matplotlib mlflow-skinny

# COMMAND ----------

import matplotlib.pyplot as plt
import mlflow
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

SEED = 42   # fixe le hasard : tout le monde obtient les mêmes résultats
LAYOUT = dict(template="plotly_white", font=dict(size=13))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 2 : lire la table et traiter les copies
# MAGIC On lit la table du notebook 08, puis on garde **une seule fois** chaque ligne.
# MAGIC
# MAGIC **Pourquoi ?** On va donner une partie des données à la machine pour apprendre, et garder le reste pour l'évaluer. Si une même ligne est des deux côtés, c'est comme donner les **réponses avant l'examen**. Ce piège s'appelle une *fuite de données*. L'étape 9 le mesure.

# COMMAND ----------

all_rows = spark.table("workspace.hr_demo.hr_employee").toPandas()
all_rows = all_rows.sort_values(list(all_rows.columns)).reset_index(drop=True)   # toujours le même ordre
df = all_rows.drop_duplicates().reset_index(drop=True)
print(f"{len(all_rows):,} lignes, dont {len(df):,} différentes")
print(f"Taux de départ : {all_rows['has_left'].mean():.1%} avec les copies, {df['has_left'].mean():.1%} sans")

# COMMAND ----------

# MAGIC %md
# MAGIC # Partie A : découvrir des groupes
# MAGIC **Apprentissage non supervisé** : on ne donne aucune réponse à la machine, elle cherche seule des ressemblances.
# MAGIC
# MAGIC ## Étape 3 : préparer les partis
# MAGIC On prend les employés **partis** et cinq informations. Les heures vont jusqu'à 310, la satisfaction jusqu'à 1 : sans précaution, les heures écraseraient tout. `StandardScaler` met toutes les colonnes **à la même échelle**.

# COMMAND ----------

features = ["satisfaction_level", "last_evaluation", "number_project", "average_monthly_hours", "time_spend_company"]
leavers = df[df["has_left"] == 1].reset_index(drop=True)
X_leavers = StandardScaler().fit_transform(leavers[features])
print(f"{len(leavers):,} employés partis, {len(features)} informations chacun")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 4 : combien de groupes ?
# MAGIC On essaie de 2 à 7 groupes. Le **score de silhouette** mesure si les groupes sont bien séparés : plus il est proche de 1, mieux c'est.

# COMMAND ----------

scores = {}
for k in range(2, 8):
    labels = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(X_leavers)
    scores[k] = silhouette_score(X_leavers, labels)
best_k = max(scores, key=scores.get)
fig = px.bar(x=list(scores), y=list(scores.values()), text=[f"{v:.2f}" for v in scores.values()],
             labels={"x": "nombre de groupes", "y": "silhouette"}, title=f"Meilleur choix : {best_k} groupes")
fig.update_layout(height=380, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** La machine choisit **3 groupes**, le même nombre que nous, sans que personne ne le lui ait dit. Les scores pour 4 et 5 groupes sont proches : 3 est le meilleur choix selon cette mesure, pas une vérité absolue.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 5 : qui sont ces groupes ?
# MAGIC La machine donne des numéros, **pas un sens**. C'est à nous de lire les moyennes et de nommer les groupes.

# COMMAND ----------

km = KMeans(n_clusters=best_k, n_init=10, random_state=SEED).fit(X_leavers)
leavers["groupe"] = km.labels_

# Les numéros sont arbitraires : on range les groupes par satisfaction croissante, puis on les nomme
order = leavers.groupby("groupe")["satisfaction_level"].mean().sort_values().index
names = ["Surchargés et malheureux", "Sous-employés", "Performants et satisfaits"]
leavers["profil"] = leavers["groupe"].map(dict(zip(order, names if best_k == 3 else [f"Groupe {i + 1}" for i in range(best_k)])))
profiles = leavers.groupby("profil")[features].mean().round(2)
profiles.insert(0, "employes", leavers["profil"].value_counts())
display(profiles.reset_index())

# COMMAND ----------

fig = px.scatter(leavers, x="satisfaction_level", y="last_evaluation", color="profil", opacity=0.5,
                 color_discrete_sequence=["#eb6834", "#2a78d6", "#1baf7a"], title="Les groupes trouvés par la machine (employés partis)")
fig.update_layout(height=500, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** On retrouve les trois profils du notebook 08 :
# MAGIC > - **Surchargés et malheureux :** satisfaction 0,12 ; environ 6 projets et 273 heures.
# MAGIC > - **Sous-employés :** environ 2 projets et 148 heures.
# MAGIC > - **Performants et satisfaits :** évaluation 0,91 ; environ 244 heures, 5 ans d'ancienneté.
# MAGIC >
# MAGIC > K-Means place **chaque** parti dans un groupe, même ceux qui sont loin des autres : les moyennes diffèrent donc un peu du notebook 08.

# COMMAND ----------

# MAGIC %md
# MAGIC # Partie B : trouver des règles
# MAGIC **Apprentissage supervisé** : cette fois, on montre à la machine des exemples avec la réponse (parti ou resté).
# MAGIC
# MAGIC ## Étape 6 : séparer l'entraînement et l'examen
# MAGIC 75 % des employés servent à **apprendre**, 25 % sont **cachés** pour l'examen. `stratify` garde la même proportion de partis des deux côtés.

# COMMAND ----------

X, y = df.drop(columns="has_left"), df["has_left"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
print(f"Apprentissage : {len(X_train):,} employés   Examen : {len(X_test):,}, dont {y_test.sum()} partis")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 7 : l'arbre de décision
# MAGIC Un arbre pose une suite de questions. On le limite à **4 questions** et à au moins 50 employés par réponse, pour qu'il reste lisible et n'apprenne pas par cœur.

# COMMAND ----------

tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=50, random_state=SEED).fit(X_train, y_train)

plt.figure(figsize=(26, 11))   # orange = restés en majorité, bleu = partis en majorité
plot_tree(tree, feature_names=list(X.columns), class_names=["reste", "parti"], filled=True, rounded=True,
          impurity=False, proportion=True, fontsize=8)
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Les mêmes règles, en texte. `class: 1` veut dire « la majorité est partie ».

# COMMAND ----------

print(export_text(tree, feature_names=list(X.columns), decimals=2, show_weights=True))

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on lit.** Trois chemins mènent au départ (seuils arrondis) :
# MAGIC > 1. Satisfaction de 0,11 ou moins, **3 projets ou plus** : tous partis (361 sur 361).
# MAGIC > 2. Satisfaction de 0,47 ou moins, **2 projets**, évaluation entre 0,45 et 0,57 : 566 partis sur 596.
# MAGIC > 3. Satisfaction au-dessus de 0,47, **5 ans ou plus**, évaluation au-dessus de 0,81 et **plus de 216 heures** : 356 partis sur 427.
# MAGIC >
# MAGIC > Encore les trois profils, avec une information en plus : **l'ancienneté** joue un rôle dans le troisième.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 8 : comparer plusieurs modèles
# MAGIC | Mesure | La question à laquelle elle répond |
# MAGIC |---|---|
# MAGIC | **Exactitude** | Quelle part des réponses est juste ? |
# MAGIC | **Précision** | Quand le modèle dit « parti », a-t-il raison ? |
# MAGIC | **Rappel** | Parmi les vrais partis, combien a-t-il trouvés ? |
# MAGIC | **AUC** | Classe-t-il bien les partis devant les restés ? (0,5 = au hasard, 1 = parfait) |
# MAGIC
# MAGIC On ajoute un modèle **naïf** qui répond toujours « resté » : c'est la barre à dépasser.

# COMMAND ----------

models = {
    "Naïf (toujours resté)": DummyClassifier(),
    "Régression logistique": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    "Arbre de décision": tree,
    "Forêt aléatoire": RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
}
rows = []
for name, model in models.items():
    model.fit(X_train, y_train)            # apprendre
    p = model.predict(X_test)              # passer l'examen
    rows.append({"modele": name, "exactitude": accuracy_score(y_test, p),
                 "precision": precision_score(y_test, p, zero_division=0), "rappel": recall_score(y_test, p),
                 "auc": roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])})
results = pd.DataFrame(rows).round(3)
display(results)

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.**
# MAGIC > - Le modèle **naïf** a 84 % d'exactitude sans trouver un seul départ : l'exactitude seule est **trompeuse**.
# MAGIC > - La **régression logistique** ne trouve qu'environ 23 % des partis : elle cherche une tendance en ligne droite, or les départs sont **aux deux extrêmes**.
# MAGIC > - L'**arbre** trouve environ 92 % des partis, la **forêt** environ 95 %.
# MAGIC > - L'arbre est presque aussi bon, et on peut **l'expliquer**. En pratique, cela compte souvent plus que quelques points.

# COMMAND ----------

# Tableau de l'examen pour la forêt : lignes = la réalité, colonnes = la prévision
forest = models["Forêt aléatoire"]
cm = confusion_matrix(y_test, forest.predict(X_test))
fig = px.imshow(cm, text_auto=True, x=["prévu resté", "prévu parti"], y=["resté", "parti"], color_continuous_scale="Blues",
                title="Forêt aléatoire : réalité et prévision")
fig.update_layout(height=380, coloraxis_showscale=False, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Était-ce de la chance ?
# MAGIC On refait l'examen **5 fois**, avec 5 découpages différents (*validation croisée*). Un petit écart veut dire un résultat stable.

# COMMAND ----------

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
cv_rows = []
for name in ("Arbre de décision", "Forêt aléatoire"):
    s = cross_val_score(models[name], X, y, scoring="recall", cv=cv)
    cv_rows.append({"modele": name, "rappel_moyen": round(s.mean(), 3), "ecart": round(s.std(), 3)})
cv_table = pd.DataFrame(cv_rows)
display(cv_table)

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ En moyenne, l'arbre trouve environ **90 %** des partis et la forêt environ **91 %** : l'écart entre les deux est plus petit que sur un seul examen.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 9 : mesurer le piège des copies
# MAGIC Que se passe-t-il si on oublie d'enlever les copies ?

# COMMAND ----------

Xa, ya = all_rows.drop(columns="has_left"), all_rows["has_left"]
a_train, a_test, ya_train, ya_test = train_test_split(Xa, ya, test_size=0.25, stratify=ya, random_state=SEED)
leaky = RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1).fit(a_train, ya_train)
seen = len(a_test.merge(a_train.drop_duplicates(), how="inner")) / len(a_test)
leaky_recall = recall_score(ya_test, leaky.predict(a_test))
print(f"Lignes de l'examen déjà vues pendant l'apprentissage : {seen:.0%}")
print(f"Rappel de la forêt avec les copies : {leaky_recall:.1%}")
print(f"Rappel de la forêt sans les copies : {recall_score(y_test, forest.predict(X_test)):.1%}")

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ **Attention.** Avec les copies, environ **30 %** des lignes de l'examen avaient déjà été vues, et le modèle **paraît meilleur** qu'il ne l'est. La qualité des données décide de la confiance qu'on peut avoir dans un modèle.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 10 : qu'est-ce qui compte le plus ?
# MAGIC On **mélange** une colonne au hasard et on regarde si la prévision se dégrade. Si oui, la colonne était importante.

# COMMAND ----------

imp = permutation_importance(forest, X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=SEED, n_jobs=-1)
imp = pd.DataFrame({"variable": X.columns, "importance": imp.importances_mean}).sort_values("importance")
fig = px.bar(imp, x="importance", y="variable", orientation="h", text=imp["importance"].map("{:.3f}".format),
             color_discrete_sequence=["#2a78d6"], title="Baisse de l'AUC quand on mélange la colonne")
fig.update_layout(height=420, **LAYOUT)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > ✅ **Ce qu'on voit.** La **satisfaction** compte le plus, puis l'**ancienneté** et le **nombre de projets**. L'accident et la promotion ne comptent presque pas. Dans la matrice de corrélation, les projets semblaient sans lien avec le départ : le modèle voit ce que la corrélation ne voyait pas.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 11 : garder une trace avec MLflow
# MAGIC En entreprise, on doit pouvoir dire **quel modèle**, avec **quels réglages**, a donné **quel résultat**. **MLflow**, intégré à Databricks, garde cet historique.
# MAGIC
# MAGIC 👉 **À montrer :** l'icône **Experiments** (fiole) à droite du notebook.

# COMMAND ----------

for r in results.to_dict("records"):
    with mlflow.start_run(run_name=r["modele"]):
        mlflow.log_params({"modele": r["modele"], "table": "workspace.hr_demo.hr_employee", "copies_enlevees": True,
                           "lignes": len(df), "seed": SEED})
        mlflow.log_metrics({k: float(v) for k, v in r.items() if k != "modele"})
print(f"{len(results)} résultats enregistrés")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Étape 12 : contrôler
# MAGIC Si une conclusion écrite plus haut n'est plus vraie (nouvelles données, nouvelle version), cette cellule **s'arrête en erreur**.

# COMMAND ----------

r = results.set_index("modele")
top = imp.sort_values("importance", ascending=False)["variable"].tolist()
checks = {
    "lignes différentes = 11 920": len(df) == 11920,
    "3 groupes": best_k == 3,
    "taille des groupes : 534, 851, 538 (à 15 près)": all(abs(a - b) <= 15 for a, b in zip([profiles.loc[n, "employes"] for n in names], [534, 851, 538])),
    "rappel régression logistique < 30 %": r.loc["Régression logistique", "rappel"] < 0.30,
    "rappel arbre entre 90 et 94 %": 0.90 <= r.loc["Arbre de décision", "rappel"] <= 0.94,
    "rappel forêt entre 93 et 96 %": 0.93 <= r.loc["Forêt aléatoire", "rappel"] <= 0.96,
    "les copies font paraître le modèle meilleur": leaky_recall > r.loc["Forêt aléatoire", "rappel"],
    "satisfaction, ancienneté, projets en tête": top[:3] == ["satisfaction_level", "time_spend_company", "number_project"],
}
for name, ok in checks.items():
    print("OK  " if ok else "NON ", name)
assert all(checks.values()), [k for k, ok in checks.items() if not ok]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclure
# MAGIC 1. **Deux méthodes différentes** (groupes et arbre) retrouvent les **mêmes trois profils** que nous avions vus à l'œil.
# MAGIC 2. **La machine trouve des motifs, l'humain leur donne un sens** : c'est nous qui avons nommé les groupes.
# MAGIC 3. **Un bon score ne suffit pas** : regarder le rappel, comparer à un modèle naïf, éviter les fuites.
# MAGIC 4. **Expliquer compte** : l'arbre est presque aussi bon que la forêt, et chacun peut le lire.
# MAGIC
# MAGIC > ⚠️ **Avant de l'utiliser pour de vrai.** Le jeu de données semble simulé : ces très bons scores seraient inhabituels dans la vie réelle. Ce sont des liens, pas des causes. Et prévoir le départ d'une personne est sensible : dans l'Union européenne, l'IA utilisée pour des décisions sur les travailleurs peut être classée **à haut risque** par l'AI Act, et le RGPD s'applique. Cette démo sert à comprendre, **pas à décider sur des personnes**.
