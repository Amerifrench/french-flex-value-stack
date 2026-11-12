# Context for Claude Code

Small portfolio project: value of residential flexibility (home battery, smart EV charger) in French power markets.
Goal: a credible, readable model to show in a job application (Energy Markets France role at a VPP company).

## Rules

- Keep code simple and short. Prefer small, readable changes over rewrites. Explain each change in one line.
- All assumptions go in `src/config.py`. No magic numbers elsewhere.
- Units: kW, kWh, EUR; prices arrive in EUR/MWh and are converted to EUR/kWh in `models.py`.
- Times are Europe/Paris local time.
- Never invent market data. If a dataset is missing, stop and say which file is needed and where to get it.
- Every result printed must be reproducible with `python src/run.py`.
- Comments and README in English (the audience is a London team); talk to me in French.

## Structure

- `src/config.py` — asset and market assumptions
- `src/data.py` — price loading (ENTSO-E, RTE CSV, synthetic prices for tests)
- `src/models.py` — daily LPs: battery arbitrage (+ aFRR reservation), EV smart charging, capacity value
- `src/run.py` — runs every strategy, writes `results/summary.csv`
