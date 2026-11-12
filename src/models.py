"""Les trois stratégies, chacune optimisée jour par jour (le day-ahead est connu la veille).

Unités : kW, kWh, EUR. Les prix arrivent en EUR/MWh et sont convertis en EUR/kWh.
"""

import cvxpy as cp
import numpy as np
import pandas as pd


def battery_day(prices_kwh: np.ndarray, b: dict, reserve_kw: float = 0.0,
                afrr_eur_kw_h: np.ndarray | None = None, afrr_duration_h: float = 1.0) -> dict:
    """Une journée de batterie : arbitrage day-ahead, avec en option une puissance réservée à l'aFRR.

    La réserve réduit la puissance disponible pour l'arbitrage et impose une marge d'énergie
    (reserve_kw * afrr_duration_h) en haut et en bas de l'état de charge. L'énergie activée n'est pas modélisée.
    """
    T = len(prices_kwh)
    E, P = b["energy_kwh"], b["power_kw"]
    eta = np.sqrt(b["eff_roundtrip"])  # rendement réparti entre charge et décharge
    margin = reserve_kw * afrr_duration_h

    ch = cp.Variable(T, nonneg=True)
    dis = cp.Variable(T, nonneg=True)
    soc = cp.Variable(T + 1)

    cons = [
        soc[0] == b["soc_start"] * E,
        soc[T] == b["soc_start"] * E,
        soc[1:] == soc[:-1] + eta * ch - dis / eta,
        soc >= margin,
        soc <= E - margin,
        ch + dis <= P - reserve_kw,  # avec les prix positifs, ne charge et décharge jamais en même temps
        cp.sum(dis) / eta <= b["max_cycles_per_day"] * E,
    ]
    arbitrage = prices_kwh @ (dis - ch)
    cp.Problem(cp.Maximize(arbitrage), cons).solve(solver=cp.HIGHS)

    afrr = 0.0 if afrr_eur_kw_h is None else float(reserve_kw * afrr_eur_kw_h.sum())
    return {"arbitrage_eur": float(arbitrage.value), "afrr_eur": afrr,
            "throughput_kwh": float(dis.value.sum())}


def run_battery_year(df: pd.DataFrame, b: dict, reserve_share: float = 0.0, afrr_duration_h: float = 1.0) -> dict:
    """Boucle sur les jours de l'année ; renvoie les totaux annuels."""
    reserve_kw = reserve_share * b["power_kw"]
    tot = {"arbitrage_eur": 0.0, "afrr_eur": 0.0, "throughput_kwh": 0.0}
    for _, day in df.groupby(df.index.date):
        afrr = day["afrr_eur_mw_h"].to_numpy() / 1000 if "afrr_eur_mw_h" in day else None
        r = battery_day(day["da_eur_mwh"].to_numpy() / 1000, b, reserve_kw, afrr, afrr_duration_h)
        for k in tot:
            tot[k] += r[k]
    tot["cycles"] = tot["throughput_kwh"] / b["energy_kwh"]
    tot["total_eur"] = tot["arbitrage_eur"] + tot["afrr_eur"]
    return tot


def ev_sessions(df: pd.DataFrame, ev: dict):
    """Découpe l'année en sessions de recharge : de plug_in_hour le jour J à plug_out_hour le jour J+1."""
    for d in pd.unique(df.index.date):
        start = pd.Timestamp(d, tz="Europe/Paris") + pd.Timedelta(hours=ev["plug_in_hour"])
        end = pd.Timestamp(d, tz="Europe/Paris") + pd.Timedelta(days=1, hours=ev["plug_out_hour"])
        window = df.loc[(df.index >= start) & (df.index < end), "da_eur_mwh"]
        if len(window) * ev["power_kw"] >= ev["energy_needed_kwh"]:
            yield window


def run_ev_year(df: pd.DataFrame, ev: dict) -> dict:
    """Compare la recharge naïve (dès le branchement) et la recharge optimisée sur le day-ahead."""
    naive_cost = smart_cost = 0.0
    neg_hours_naive = neg_hours_smart = 0
    for window in ev_sessions(df, ev):
        p = window.to_numpy() / 1000
        T, P, need = len(p), ev["power_kw"], ev["energy_needed_kwh"]

        # Naïf : pleine puissance jusqu'à avoir livré l'énergie
        naive = np.minimum(P, np.clip(need - P * np.arange(T), 0, None))
        naive_cost += p @ naive
        neg_hours_naive += int(((naive > 0) & (p < 0)).sum())

        # Optimisé : minimise le coût sous contrainte de livraison
        x = cp.Variable(T, nonneg=True)
        cp.Problem(cp.Minimize(p @ x), [x <= P, cp.sum(x) == need]).solve(solver=cp.HIGHS)
        smart_cost += p @ x.value
        neg_hours_smart += int(((x.value > 1e-6) & (p < 0)).sum())

    return {"naive_cost_eur": naive_cost, "smart_cost_eur": smart_cost,
            "savings_eur": naive_cost - smart_cost,
            "neg_price_hours_naive": neg_hours_naive, "neg_price_hours_smart": neg_hours_smart}


def capacity_value(b: dict, cap: dict) -> float:
    """Revenu annuel du mécanisme de capacité : puissance x coefficient de certification x prix."""
    return b["power_kw"] * cap["derating"] * cap["price_eur_per_kw_year"]
