"""Chargement des prix. Format commun : DataFrame indexé en heure locale (Europe/Paris), colonnes en EUR/MWh."""

import os

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_day_ahead(year: int) -> pd.Series:
    """Prix day-ahead France. Lit data/da_FR_<year>.csv s'il existe, sinon le télécharge via ENTSO-E."""
    path = os.path.join(DATA_DIR, f"da_FR_{year}.csv")
    if not os.path.exists(path):
        fetch_day_ahead_entsoe(year, path)
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    s.index = pd.to_datetime(s.index, utc=True).tz_convert("Europe/Paris")
    return s.resample("1h").mean().rename("da_eur_mwh")


def fetch_day_ahead_entsoe(year: int, path: str) -> None:
    """Télécharge les prix day-ahead France via entsoe-py. Nécessite la variable d'environnement ENTSOE_API_KEY."""
    from entsoe import EntsoePandasClient

    client = EntsoePandasClient(api_key=os.environ["ENTSOE_API_KEY"])
    start = pd.Timestamp(f"{year}-01-01", tz="Europe/Paris")
    end = pd.Timestamp(f"{year + 1}-01-01", tz="Europe/Paris")
    prices = client.query_day_ahead_prices("FR", start=start, end=end)
    os.makedirs(DATA_DIR, exist_ok=True)
    prices.to_csv(path)


def load_afrr_capacity(year: int) -> pd.Series:
    """Prix de la capacité aFRR (EUR/MW/h), heure par heure. TODO : à remplir avec les données RTE.

    Fichier attendu : data/afrr_capacity_FR_<year>.csv, colonnes [datetime, eur_mw_h].
    """
    path = os.path.join(DATA_DIR, f"afrr_capacity_FR_{year}.csv")
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    s.index = pd.to_datetime(s.index, utc=True).tz_convert("Europe/Paris")
    return s.resample("1h").mean().rename("afrr_eur_mw_h")


def synthetic_prices(year: int, seed: int = 0) -> pd.DataFrame:
    """Prix fictifs pour tester le code sans données : creux solaire à midi, pointe du soir, quelques heures négatives."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="1h", tz="Europe/Paris", inclusive="left")
    h = idx.hour.to_numpy()
    summer = np.cos(2 * np.pi * (idx.dayofyear.to_numpy() - 172) / 365)  # 1 en juin, -1 en décembre
    da = 70 - 45 * summer * np.exp(-((h - 13) ** 2) / 8) + 35 * np.exp(-((h - 19) ** 2) / 3) + rng.normal(0, 12, len(idx))
    afrr = np.clip(15 + 10 * np.exp(-((h - 19) ** 2) / 6) + rng.normal(0, 4, len(idx)), 0, None)
    return pd.DataFrame({"da_eur_mwh": da, "afrr_eur_mw_h": afrr}, index=idx)
