*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).*

## What I Built

I built **Stillroot**, a quiet plant-care companion for my friend **Rohan**.

I picked a small, everyday scenario for his gift: a few plants on a windowsill, a weekend away, and the question, “Will someone need to check the soil while I'm gone?”

The pothos, monstera, and basil in the demo are imagined plants. The readings are synthetic, and the windowsill is a creative design premise. This is a working gift prototype; the next step is to put it in Rohan's hands and replace the sample assumptions with his actual routine. I wanted that distinction to be visible throughout the project.

Stillroot gives him three useful things:

- A seven-day moisture forecast with an estimated range.
- A care plan that changes with his time away, plus a note he can copy or save for a friend.
- A compact Gemma companion that explains the current situation on his device.

The interface is deliberately calm: one plant, one forecast, and one next check. A stale reading takes priority over the forecast. A dry travel forecast suggests asking a friend to **check the soil**, without automatically sending a message or deciding a watering amount.

## Demo

**[Open Stillroot on Render](https://stillroot.onrender.com)**

![Stillroot showing a recorded TabPFN forecast, a six-day trip plan, local Gemma companion, and measured results](https://raw.githubusercontent.com/faraz-shamim/stillroot/main/docs/stillroot-desktop.jpg)

Try this short journey:

1. Choose **Basil** and move **Days away** to seven. The care signal becomes **ASK FRIEND**.
2. Enable **Simulate a stale sensor reading**. The plan changes to **VERIFY SENSOR**.
3. Turn that off, then choose **Before I water**. Gemma downloads once and answers locally.
4. Open **Try your own CSV history** and use the supplied sample file. The browser labels its portable baseline; the README explains how to run actual TabPFN on a local Python runtime.

The core demo opens without an API key. Render's free service may need roughly a minute to wake after inactivity. Gemma's first download needs about 350 MB with WebGPU, or 850 MB for the CPU fallback. Browser caching can reduce later downloads, although offline availability depends on cache retention.

## Code

**[GitHub: faraz-shamim/stillroot](https://github.com/faraz-shamim/stillroot)**

The repository includes the app, local prediction runtime, deterministic dataset generator, forecast experiment, raw result files, model attribution, and deployment configuration. Original application code is MIT licensed; TabPFN and Gemma retain their own licenses and terms.

To open the app locally:

```bash
npm ci
npm run build
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`. The README includes the separate command to reproduce the TabPFN experiment and enable prediction for a custom CSV.

## How I Built It

### TabPFN provides the forecast

I ran **Prior Labs' TabPFN v2** on a CPU, using historical moisture, temperature, humidity, light hours, pot size, and days since watering to predict the next moisture reading.

The reproducible experiment contains 294 synthetic rows from 42 watering cycles. I split by entire cycle: 196 training rows, 49 calibration rows, and 49 test rows. This keeps adjacent readings from one watering cycle together in a single partition.

| Held-out test result | Error in relative moisture points |
| --- | ---: |
| TabPFN v2 | **0.4890 MAE** |
| Mean training-drop baseline | 0.9766 MAE |
| Last-reading baseline | 6.2986 MAE |

TabPFN reduced error by approximately **49.9%** against the mean-drop baseline in this experiment. The nominal 90% one-day residual interval covered 45 of 49 test readings, or 91.84%.

These are **synthetic engineering results**. They establish that the prediction pipeline runs and can be audited; field performance still needs real observations. The seven-day forecast recursively predicts future readings, and the expanding multi-day range is a disclosed heuristic. The 22% check threshold is a demo assumption that needs sensor and plant calibration.

You can inspect the [measurement report](https://github.com/faraz-shamim/stillroot/blob/main/web/public/data/tabpfn-report.json), [dataset card](https://github.com/faraz-shamim/stillroot/blob/main/web/public/data/data-card.json), and [experiment code](https://github.com/faraz-shamim/stillroot/blob/main/ml/forecast.py).

The hosted demo serves recorded outputs from **actual TabPFN inference**. That makes the first interaction quick and keeps the Render runtime small. Custom CSV uploads use a clearly labeled browser baseline by default; the explicit local-runtime option runs TabPFN on that CSV.

### Gemma makes the numbers understandable

**Google's Gemma 3 270M instruction model** runs inside a Web Worker through Transformers.js and ONNX Runtime. The question, current plant facts, and care signal are assembled into a short prompt. Model inference happens in the visitor's browser, so those questions are not sent to an inference service.

I verified a real browser answer to “What should I check before I water?” in **7.9 seconds** on the tested WebGPU runtime. That measurement is saved in the repository and represents one run, rather than a general latency claim.

A useful implementation lesson was to pin the model conversion: the newer optimized embedding operator worked with WebGPU but failed in WASM. The CPU fallback selects an earlier compatible conversion. Model failures remain visible; the app does not replace a failed inference with a scripted answer.

Gemma explains the plan. The readable care policy controls the signal, so a generated answer cannot override the stale-reading safeguard or trigger watering.

### Render makes it easy to give away

A lightweight FastAPI service on **Render's free plan** serves the built interface, forecast artifacts, health endpoint, and validated care-policy API. It installs no Torch runtime or model weights. Gemma runs on the visitor's device, while the larger TabPFN experiment runs locally.

The build, domain checks, API validation, CSV flow, responsive layout, and browser inference were tested. Optional WebMCP tools let a supporting browser read or configure the same visible care plan; invalid trip lengths fail without corrupting the plan.

This version uses **$0 in paid infrastructure and API calls**.

## Why Does Open Innovation Matter?

For this gift, openness means Rohan can understand what the app is asking him to do.

The forecast has a CSV, a split strategy, baselines, and inspectable results. The care policy is a short function he can change. Gemma's weights can run on his device, and the public conversion history let me solve a concrete runtime compatibility problem. The interface and local runtime can be copied, repaired, or adapted to another friend's plants.

A hosted language API could explain a graph, but it would introduce a service dependency, inference costs, and a different privacy boundary. Open weights gave this small project a practical way to keep its conversation local and its ongoing operating cost at zero.

The remaining work is equally concrete: collect observed watering cycles, calibrate the sensor and threshold, test on future cycles and new plants, and listen to Rohan after a real handoff. Those next steps remain visible alongside the working demo.

## Prize Categories

- **Best Use of TabPFN** — actual inference, a reproducible experiment, held-out cycles, baselines, and auditable outputs.
- **Best Use of Gemma** — an open-weight companion that answers locally in the browser.
- **Best Use of Render** — the deployed application runtime on a free web service.

Each component earns its place in the gift: TabPFN looks ahead, Gemma explains, and Render makes the project easy to open and share.

*AI assistance was used to implement, test, and write about this project. All reported measurements come from executed runs; the friend scenario and dataset are explicitly labeled synthetic.*
