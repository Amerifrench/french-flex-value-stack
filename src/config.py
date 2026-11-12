"""Hypothèses des actifs et des marchés. Tout ce qui est discutable est ici, nulle part ailleurs."""

YEAR = 2025

# Batterie résidentielle
BATTERY = {
    "energy_kwh": 10.0,       # capacité utile
    "power_kw": 5.0,          # puissance charge / décharge
    "eff_roundtrip": 0.90,    # rendement aller-retour
    "max_cycles_per_day": 1.0,
    "soc_start": 0.5,         # fraction de la capacité, imposée aussi en fin de journée
}

# Borne VE pilotée
EV = {
    "power_kw": 7.0,
    "energy_needed_kwh": 30.0,  # à livrer par session
    "plug_in_hour": 19,         # arrivée le soir
    "plug_out_hour": 7,         # départ le lendemain matin
}

# aFRR : part de la puissance batterie réservée (balayée de 0 à 1 dans run.py)
AFRR = {
    "duration_h": 1.0,  # énergie à garder en réserve par kW réservé (hypothèse simplificatrice)
}

# Mécanisme de capacité (valeurs à remplacer par le rapport RTE de l'enchère 2026-27)
CAPACITY = {
    "price_eur_per_kw_year": 0.0,  # TODO : prix de l'enchère RTE
    "derating": 0.5,               # TODO : coefficient de certification d'une batterie de 2 h
}
