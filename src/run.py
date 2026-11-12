"""Point d'entrée : python src/run.py [--synthetic]

Affiche le tableau EUR/an par stratégie et écrit results/summary.csv.
"""

import argparse
import os

import pandas as pd

import config
import data
import models


def main(synthetic: bool) -> None:
    if synthetic:
        df = data.synthetic_prices(config.YEAR)
    else:
        df = data.load_day_ahead(config.YEAR).to_frame()
        try:
            df = df.join(data.load_afrr_capacity(config.YEAR), how="left")
        except FileNotFoundError:
            print("Pas de fichier aFRR : la stratégie 3 est sautée.")

    rows = []

    # Stratégie 1 : arbitrage day-ahead seul
    r = models.run_battery_year(df.drop(columns="afrr_eur_mw_h", errors="ignore"), config.BATTERY)
    rows.append({"strategy": "1. Batterie, arbitrage DA", "eur_per_year": r["total_eur"], "cycles": r["cycles"]})

    # Stratégie 2 : VE piloté contre VE naïf
    ev = models.run_ev_year(df, config.EV)
    rows.append({"strategy": "2. VE piloté (économie vs naïf)", "eur_per_year": ev["savings_eur"],
                 "neg_price_hours": ev["neg_price_hours_smart"]})

    # Stratégie 3 : batterie, part réservée à l'aFRR balayée de 0 à 100 %
    if "afrr_eur_mw_h" in df:
        for share in [0.0, 0.25, 0.5, 0.75, 1.0]:
            r = models.run_battery_year(df, config.BATTERY, share, config.AFRR["duration_h"])
            rows.append({"strategy": f"3. Batterie, {int(share * 100)} % aFRR",
                         "eur_per_year": r["total_eur"], "arbitrage_eur": r["arbitrage_eur"],
                         "afrr_eur": r["afrr_eur"], "cycles": r["cycles"]})

    # Capacité : s'ajoute aux autres revenus de la batterie
    rows.append({"strategy": "Capacité (batterie)", "eur_per_year": models.capacity_value(config.BATTERY, config.CAPACITY)})

    out = pd.DataFrame(rows).round(1)
    os.makedirs("results", exist_ok=True)
    out.to_csv("results/summary.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="prix fictifs, pour tester sans données")
    main(parser.parse_args().synthetic)
