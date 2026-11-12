# French flex value stack

What can a home battery and a smart EV charger earn in France, and on which market?

> Status: work in progress. Numbers below are placeholders until the 2025 data is in.

## Question

For 2025, what is the annual value of:

- a 10 kWh / 5 kW home battery (day-ahead arbitrage, aFRR capacity, capacity mechanism);
- a 7 kW smart EV charger (30 kWh per night, plugged 19:00–07:00) versus naive charging.

## Results (to fill)

| Strategy | EUR/year | Notes |
| --- | --- | --- |
| 1. Battery, day-ahead arbitrage only | | cycles/year |
| 2. Smart EV vs naive | | negative-price hours captured |
| 3. Battery, best aFRR / arbitrage split | | optimal share reserved |
| Capacity mechanism | | derating assumption |

## Method

- Daily LP (cvxpy + HiGHS), day-ahead prices known the day before, state of charge back to 50 % each midnight.
- aFRR: a share of battery power is reserved every hour, paid at the capacity price; that power and an energy margin (1 h) are taken away from arbitrage. Activated energy is not modelled.
- Capacity: power x derating x auction price.

## What the model ignores (read before quoting a number)

- Aggregator fees and value sharing with the customer.
- aFRR activation energy, availability penalties, qualification and telemetry costs.
- Intraday and imbalance markets; NEBCO settlement details (payment to the supplier).
- Battery degradation cost per cycle.
- Perfect day-ahead foresight: an upper bound on arbitrage.

## Run it

```bash
pip install -r requirements.txt
python src/run.py --synthetic        # fake prices, checks the code runs
export ENTSOE_API_KEY=...            # free token from transparency.entsoe.eu
python src/run.py                    # real 2025 day-ahead prices
```

aFRR capacity prices go in `data/afrr_capacity_FR_2025.csv` (columns: datetime, eur_mw_h).
All assumptions live in `src/config.py`.

## Data sources

- Day-ahead prices: ENTSO-E Transparency Platform (via `entsoe-py`).
- aFRR capacity prices: RTE (services-rte.com / data portal).
- Capacity auction: RTE report on the 2026-27 delivery-year auction.
