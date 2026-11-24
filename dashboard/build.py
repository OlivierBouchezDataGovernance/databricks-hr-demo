"""Builds dashboard/hr_departs.lvdash.json (Databricks AI/BI dashboard on workspace.hr_demo.hr_employee)."""
import json
from pathlib import Path

SQL = """SELECT has_left, CASE has_left WHEN 1 THEN 'Parti' ELSE 'Resté' END AS statut,
  satisfaction_level, last_evaluation, average_monthly_hours,
  CAST(number_project AS STRING) AS projets,
  lpad(CAST(time_spend_company AS STRING), 2, '0') AS annees,
  CASE WHEN average_monthly_hours <= 130 THEN '091-130' WHEN average_monthly_hours <= 160 THEN '131-160'
       WHEN average_monthly_hours <= 190 THEN '161-190' WHEN average_monthly_hours <= 220 THEN '191-220'
       WHEN average_monthly_hours <= 250 THEN '221-250' WHEN average_monthly_hours <= 280 THEN '251-280'
       ELSE '281-310' END AS heures,
  CASE promotion_last_5years WHEN 1 THEN 'Promu' ELSE 'Non promu' END AS promotion,
  CASE WHEN satisfaction_level <= 0.11 AND last_evaluation >= 0.77 THEN 'Surchargés et malheureux'
       WHEN satisfaction_level BETWEEN 0.36 AND 0.46 AND last_evaluation BETWEEN 0.45 AND 0.57 THEN 'Sous-employés'
       WHEN satisfaction_level BETWEEN 0.72 AND 0.92 AND last_evaluation >= 0.80 THEN 'Performants et satisfaits'
       ELSE 'Autres' END AS profil
FROM workspace.hr_demo.hr_employee"""
PCT = {"type": "number-percent", "decimalPlaces": {"type": "max", "places": 1}}
INT = {"type": "number", "abbreviation": "none", "decimalPlaces": {"type": "max", "places": 0}}
layout = []


def put(name, x, y, w, h, body):
    layout.append({"widget": {"name": name, **body}, "position": {"x": x, "y": y, "width": w, "height": h}})


def q(fields, name="main_query"):
    return [{"name": name, "query": {"datasetName": "emp", "disaggregated": False,
             "fields": [{"name": n, "expression": e} for n, e in fields]}}]


def text(name, x, y, w, h, lines):
    put(name, x, y, w, h, {"multilineTextboxSpec": {"lines": lines}})


def counter(name, x, title, expr, fmt):
    put(name, x, 4, 2 if x < 4 else 2, 3, {"queries": q([("v", expr)]), "spec": {"version": 2, "widgetType": "counter",
        "encodings": {"value": {"fieldName": "v", "format": fmt, "displayName": title}}, "frame": {"showTitle": True, "title": title}}})


def flt(name, x, field, title):
    qn = f"f_{field}"
    put(name, x, 2, 2, 2, {"queries": q([(field, f"`{field}`"), (f"{field}_associativity", "COUNT_IF(`associative_filter_predicate_group`)")], qn),
        "spec": {"version": 2, "widgetType": "filter-multi-select", "encodings": {"fields": [{"fieldName": field, "displayName": title, "queryName": qn}]},
                 "frame": {"showTitle": True, "title": title}}})


def bar(name, x, y, w, field, title):
    put(name, x, y, w, 6, {"queries": q([(field, f"`{field}`"), ("taux", "AVG(`has_left`)"), ("n", "COUNT(`*`)")]),
        "spec": {"version": 3, "widgetType": "bar", "encodings": {
            "x": {"fieldName": field, "scale": {"type": "categorical", "sort": {"by": "natural-order"}}, "displayName": title},
            "y": {"fieldName": "taux", "scale": {"type": "quantitative"}, "format": PCT, "displayName": "Taux de départ"},
            "extra": [{"fieldName": "n", "displayName": "Employés"}], "label": {"show": True}},
            "frame": {"showTitle": True, "title": title}, "mark": {"colors": ["#2a78d6"]}}})


text("titre", 0, 0, 6, 2, ["# Pourquoi les employés partent-ils ?\n", "Jeu de démonstration, 14 999 lignes. Choisissez un filtre : tous les graphiques suivent."])
flt("f1", 0, "projets", "Nombre de projets")
flt("f2", 2, "annees", "Années dans l'entreprise")
flt("f3", 4, "promotion", "Promotion")
counter("k1", 0, "Employés", "COUNT(`*`)", INT)
counter("k2", 2, "Partis", "SUM(`has_left`)", INT)
counter("k3", 4, "Taux de départ", "AVG(`has_left`)", PCT)
bar("b1", 0, 7, 2, "projets", "Par nombre de projets")
bar("b2", 2, 7, 2, "heures", "Par heures par mois")
bar("b3", 4, 7, 2, "annees", "Par années dans l'entreprise")
put("nuage", 0, 13, 3, 8, {"queries": q([("satisfaction_level", "`satisfaction_level`"), ("last_evaluation", "`last_evaluation`"), ("statut", "`statut`"), ("n", "COUNT(`*`)")]),
    "spec": {"version": 3, "widgetType": "scatter", "encodings": {
        "x": {"fieldName": "satisfaction_level", "scale": {"type": "quantitative"}, "displayName": "Satisfaction"},
        "y": {"fieldName": "last_evaluation", "scale": {"type": "quantitative"}, "displayName": "Évaluation"},
        "color": {"fieldName": "statut", "displayName": "Statut", "scale": {"type": "categorical", "mappings": [
            {"value": "Resté", "color": "#2a78d6"}, {"value": "Parti", "color": "#eb6834"}]}},
        "size": {"fieldName": "n", "scale": {"type": "quantitative"}, "displayName": "Employés"}},
        "frame": {"showTitle": True, "title": "Satisfaction et évaluation : les profils cachés"}}})
put("profils", 3, 13, 3, 8, {"queries": q([("profil", "`profil`"), ("partis", "SUM(`has_left`)"), ("taux", "AVG(`has_left`)")]),
    "spec": {"version": 3, "widgetType": "bar", "encodings": {
        "x": {"fieldName": "taux", "scale": {"type": "quantitative"}, "format": PCT, "displayName": "Taux de départ"},
        "y": {"fieldName": "profil", "scale": {"type": "categorical", "sort": {"by": "x-reversed"}}, "displayName": "Profil"},
        "extra": [{"fieldName": "partis", "displayName": "Partis"}], "label": {"show": True}},
        "frame": {"showTitle": True, "title": "Taux de départ par profil"}, "mark": {"colors": ["#eb6834"]}}})
text("note", 0, 21, 6, 2, ["**Attention :** ce sont des liens, pas des causes. Une ligne sur cinq est une copie exacte d'une autre : sans les copies, le taux de départ est de 16,1 % au lieu de 23,8 %. Les limites des profils ont été tracées à l'œil."])
dash = {"datasets": [{"name": "emp", "displayName": "Employés", "queryLines": [l + "\n" for l in SQL.split("\n")]}],
        "pages": [{"name": "departs", "displayName": "Départs", "pageType": "PAGE_TYPE_CANVAS", "layout": layout}]}
Path(__file__).with_name("hr_departs.lvdash.json").write_text(json.dumps(dash, ensure_ascii=False, indent=1), encoding="utf-8")
