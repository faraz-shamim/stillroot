# Stillroot

A little care, less guesswork. An open AI plant-care companion built for my friend Rohan during the **Hacktoberfest Weekend Challenge: Build for a Friend**, October 2–5, 2026.

Choose a plant, explore its seven-day moisture forecast, plan time away, and save a short handoff note. A small Gemma model explains the forecast **on your device**. The project focuses on **TabPFN, Gemma, and Render**.

## The design premise

The windowsill is a creative gift scenario for Rohan, rather than a documented problem or interview. The sample plants and all history rows are simulated. No claim is made that Rohan owns these plants, supplied sensor data, or has already tested the app. Real histories can replace the demonstration CSV.

## What actually runs

| Component | Implementation | Where it runs |
|---|---|---|
| Moisture prediction | Actual TabPFN v2 regressor, two estimators | Local Python CPU; audited recorded outputs in the hosted demo |
| Forecast explanation | Gemma 3 270M instruction model, ONNX q8 | Browser Web Worker with ONNX Runtime WASM |
| Care signal | Readable deterministic policy | Browser; also exposed by the Python API |
| Website | Vite, semantic HTML, CSS, vanilla JavaScript | Render free web service |
| Custom CSV | Portable analogue baseline, or live local TabPFN | Browser by default; your explicit local runtime otherwise |

The hosted demo does **not** claim to run TabPFN afresh for every slider movement. It selects recorded real inference outputs for three simulated plants. CSV uploads stay in the browser unless the user explicitly chooses the local TabPFN button. The public Render runtime never receives an uploaded CSV in that flow.

Gemma downloads roughly 600 MB of model and runtime assets from Hugging Face on its first use; a recent desktop browser and sufficient memory are recommended. Questions and answers are computed locally and are not sent to an inference API. Model assets can be cached by the browser; offline operation is not guaranteed because cache retention is controlled by the browser. The interface labels model failures instead of substituting a pretend answer.

## Measured forecast experiment

Dataset: 294 synthetic rows, generated deterministically with seed `20261002`. Entire watering cycles are separated: 196 training rows (cycles 0–27), 49 calibration rows (28–34), and 49 held-out test rows (35–41). Adjacent days from the same cycle never appear across these partitions.

| Held-out metric | Result |
|---|---:|
| TabPFN v2 MAE | 0.4890 relative moisture percentage points |
| Mean training-drop baseline MAE | 0.9766 points |
| Last-reading baseline MAE | 6.2986 points |
| Test coverage of nominal 90% one-day residual interval | 91.84% (45/49) |

This is approximately **49.9% lower error** than the mean-drop baseline on this synthetic engineering task. It does not establish real-world horticultural performance. Longer-term predictions are recursive and compound model error. The multi-day range expands one-day residual width by `sqrt(day)` and is explicitly a heuristic. A sensor percentage is relative to that sensor's calibration, not an absolute soil property.

Reproduce:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
$env:TABPFN_MODEL_CACHE_DIR = Join-Path (Get-Location) 'models\tabpfn'
$env:HF_HOME = Join-Path (Get-Location) 'models\huggingface'
.\.venv\Scripts\python.exe -m ml.forecast
```

Reports and exact model outputs are committed under `web/public/data/`. Model weights and caches are ignored. Model inference needs internet only for the first checkpoint download. V2 weights are publicly downloadable under the Prior Labs attribution license.

## Run the app

Node.js 20.19+ or 22.12+ and Python 3.12 are supported.

```powershell
npm ci
npm run build
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. For UI development, `npm run dev` serves Vite on its reported address.

To predict from your CSV with real local TabPFN, install `requirements-ml.txt`, set `$env:TABPFN_MODE = 'local'` before starting the Python server, and choose **Run local TabPFN**. Use that feature from the local app, where browser security settings permit requests to the loopback runtime. Public HTTPS pages may block loopback requests.

CSV schema: `moisture,temperature,humidity,light_hours,pot_size,days_since_water,next_moisture`. Use 20–1,000 complete numeric rows; maximum file size 200 KB. The supplied CSV also includes `cycle` and `day` for auditing the experiment. The portable upload baseline uses nearby historical examples and is clearly labeled **not TabPFN**.

## Deploy to Render for $0

Connect the public GitHub repository on Render and create a **free** Python web service. The supplied `render.yaml` specifies:

- Build: `pip install -r requirements.txt && npm ci && npm run build`
- Start: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`
- `TABPFN_MODE=recorded`

The free runtime does not install Torch or host model weights. Gemma inference runs in the visitor's browser. Free Render services may sleep when idle and need time to wake. No paid instance, subscription, GPU, or API key is required.

## Checks

```powershell
npm test
npm run build
```

The domain checks cover stale sensor handling, wet-soil protection, malformed CSV rejection, and bounded forecasts. API validation, plant selection, trip duration, stale readings, mobile layout, and a real Gemma answer are also verified during browser QA. The browser handoff note is copied or downloaded; it is never automatically sent to another person.

## Scope and next steps

Before relying on it for real plants: collect genuinely observed watering cycles, calibrate the sensor, validate on future cycles and new plants, and replace the sample assumptions with Rohan's preferences. Handing the project to Rohan and recording his actual feedback would improve the project; no feedback is fabricated.

## Credits and licenses

- Original Stillroot application code: MIT, see `LICENSE`.
- **TabPFN, developed by Prior Labs**: [repository](https://github.com/PriorLabs/TabPFN), [Prior Labs License](https://github.com/PriorLabs/TabPFN/blob/main/LICENSE). TabPFN v2 weights and implementation retain their attribution requirements. The project's MIT license does not relicense those weights.
- **Gemma, developed by Google**: [model information](https://ai.google.dev/gemma/docs), [Gemma Terms](https://ai.google.dev/gemma/terms). Gemma is an open-weight model with its own usage terms, not an MIT model.
- [ONNX Community Gemma conversion](https://huggingface.co/onnx-community/gemma-3-270m-it-ONNX), maintained in the Hugging Face ecosystem.
- [Transformers.js](https://github.com/huggingface/transformers.js), [ONNX Runtime](https://github.com/microsoft/onnxruntime), and [Vite](https://github.com/vitejs/vite).
- [Render](https://render.com/docs) hosts the application runtime.

This new repository was started within the challenge window. AI assistance was used to implement and test the project. Any changes after the submission deadline must be noted here.
