"""Genuine local TabPFN inference and held-cycle benchmark, exported for a $0 demo."""
from pathlib import Path
import json
import time
import hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from ml.make_data import ROOT, FEATURES, make_data

def new_model():
    from tabpfn import TabPFNRegressor
    from tabpfn.constants import ModelVersion
    # V2 has publicly downloadable weights and a permissive attribution license.
    return TabPFNRegressor.create_default_for_version(ModelVersion.V2,
        device="cpu", n_estimators=2, random_state=42)

def evaluate():
    import torch
    torch.set_num_threads(4)
    df = make_data()
    train, cal, test = [df[mask] for mask in (df.cycle<28, (df.cycle>=28)&(df.cycle<35), df.cycle>=35)]
    model = new_model()
    start=time.perf_counter()
    model.fit(train[FEATURES], train.next_moisture)
    fit_seconds=time.perf_counter()-start
    start=time.perf_counter()
    pred = model.predict(test[FEATURES])
    inference_seconds=time.perf_counter()-start
    calibration = model.predict(cal[FEATURES])
    residuals=np.abs(cal.next_moisture.to_numpy()-calibration)
    q=float(np.quantile(residuals, min(1, np.ceil((len(cal)+1)*.9)/len(cal)), method="higher"))
    baselines={
        "last_reading": test.moisture.to_numpy(),
        "mean_training_drop": test.moisture.to_numpy()-float((train.moisture-train.next_moisture).mean()),
    }
    report={"status":"measured", "model":"TabPFN v2", "data_kind":"synthetic", "seed":20261002,
        "train_rows":len(train),"calibration_rows":len(cal),"test_rows":len(test),
        "split":"Whole watering cycles: train 0–27; calibration 28–34; held-out test 35–41",
        "metric":"MAE in relative moisture percentage points (lower is better)",
        "tabpfn_mae":float(mean_absolute_error(test.next_moisture,pred)),
        "baselines":{k:float(mean_absolute_error(test.next_moisture,v)) for k,v in baselines.items()},
        "interval_half_width":q,
        "test_interval_coverage":float(np.mean(np.abs(test.next_moisture.to_numpy()-pred)<=q)),
        "fit_seconds":fit_seconds,"test_inference_seconds":inference_seconds,
        "checkpoint":"Prior-Labs/TabPFN-v2-reg", "license":"Prior Labs License (Apache 2.0 + attribution)",
        "limitations":"Synthetic engineering test; not real-world plant validation. Multi-day intervals are heuristic, not calibrated guarantees.",
        "source_sha256":hashlib.sha256((ROOT/"web/public/data/synthetic_history.csv").read_bytes()).hexdigest()}
    target=ROOT/"web/public/data"
    (target/"tabpfn-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    # Precompute actual model predictions for three named demo scenarios.
    scenarios=[]
    for name,initial,temp,humidity,light,pot in (
        ("pothos",49.,24.,48.,5.,16.), ("monstera",62.,23.,57.,4.,20.), ("basil",37.,27.,40.,6.,12.)):
        value=initial
        points=[{"day":0,"mean":value,"lower":value,"upper":value}]
        for day in range(1,8):
            x=pd.DataFrame([[value,temp,humidity,light,pot,day+2]],columns=FEATURES)
            value=float(np.clip(model.predict(x)[0],0,100))
            width=q*np.sqrt(day)
            points.append({"day":day,"mean":round(value,2),"lower":round(max(0,value-width),2),"upper":round(min(100,value+width),2)})
        scenarios.append({"id":name,"source":"recorded_tabpfn","current":initial,"temperature":temp,
            "humidity":humidity,"light_hours":light,"pot_size":pot,"points":points})
    artifact={"source":"recorded_tabpfn", "model":"TabPFN v2", "data_kind":"synthetic",
        "note":"These are genuine recorded local model outputs. Scenario controls select recorded forecasts; they do not rerun TabPFN in the cloud.",
        "interval_note":"90% split-conformal one-day residual interval; sqrt(day) expansion is a multi-day heuristic.","scenarios":scenarios}
    (target/"forecasts.json").write_text(json.dumps(artifact,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__ == "__main__":
    evaluate()
