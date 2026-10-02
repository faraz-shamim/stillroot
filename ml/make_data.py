"""Reproducible SYNTHETIC soil histories, not measurements from Rohan's plants."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["moisture", "temperature", "humidity", "light_hours", "pot_size", "days_since_water"]

def make_data():
    rng = np.random.default_rng(20261002)
    rows = []
    # Simulated watering cycles. Entire cycles, rather than adjacent rows, are held out.
    for cycle in range(42):
        moisture = rng.uniform(58, 74)
        pot = float(rng.choice([12, 16, 20]))
        for day in range(7):
            temp = rng.uniform(19, 30)
            humidity = rng.uniform(30, 73)
            light = rng.uniform(2, 8)
            loss = (2.4 + 0.26*(temp-19) + 0.028*(70-humidity) + 0.35*light) * (16/pot)**0.5
            next_moisture = max(5, moisture-loss+rng.normal(0, 0.65))
            rows.append(dict(cycle=cycle, day=day, moisture=round(moisture, 2), temperature=round(temp,2),
                humidity=round(humidity,2), light_hours=round(light,2), pot_size=pot,
                days_since_water=day, next_moisture=round(next_moisture,2)))
            moisture = next_moisture
    df = pd.DataFrame(rows)
    target = ROOT / "web" / "public" / "data"
    target.mkdir(parents=True, exist_ok=True)
    df.to_csv(target / "synthetic_history.csv", index=False)
    (target / "data-card.json").write_text(json.dumps({
        "kind":"synthetic", "seed":20261002, "rows":len(df), "cycles":42,
        "purpose":"Engineering demonstration. Not validated horticultural guidance.",
        "split":"Cycles 0–27 train, 28–34 calibrate, 35–41 test. No shuffled adjacent-day leakage.",
        "features":FEATURES, "target":"next_moisture", "units":"relative sensor percentage",
        "generator":"ml/make_data.py", "observations_from_rohan":False
    },indent=2),encoding="utf-8")
    print(f"Wrote {len(df)} synthetic records")
    return df

if __name__ == "__main__":
    make_data()
