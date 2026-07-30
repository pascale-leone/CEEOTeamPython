# CEEO Team Python — Summer 2026

A [Tufts CEEO](https://ceeo.tufts.edu/) project that lets kids control LEGO Education **CS+AI hub** robots (Single Motor, Double Motor, Color Sensor, and Controller "cards") by writing a small number of simple, English-verb Python functions — `dm.turn_left(90)`, `sm.spin(2)`, `cs.detect_color()` — instead of dealing with LEGO's full BLE/RPC API directly. The project also includes an AI chatbot "tutor" that helps students while they code.

> This README describes `main` as it currently stands. A separate, independently-developed browser app also exists on the `web_app` → `web_app_pyodide` branch lineage (raw Pyodide + hand-rolled Web Bluetooth); see that branch's own README for details. The two efforts are not yet reconciled — see [Branches](#branches).

---

## Table of contents

- [What problem this solves](#what-problem-this-solves)
- [The simplified Python library](#the-simplified-python-library)
- [`pyscript_website/` — the in-browser PyScript app](#pyscript_website--the-in-browser-pyscript-app)
- [The legacy desktop server](#the-legacy-desktop-server)
- [Repository layout](#repository-layout)
- [Running it locally](#running-it-locally)
- [Branches](#branches)
- [Known issues / repo hygiene](#known-issues--repo-hygiene)

---

## What problem this solves

LEGO Education's official `legoeducation` Python package is a real BLE/RPC driver (`pip install legoeducation`, built on `bleak`) with the kind of API a professional developer expects: verbose method names, enums, manual connect/retry handling, raw device objects. That's too much for the elementary/middle-school students this project targets.

This repo wraps `legoeducation` in thin, kid-friendly subclasses with short verb-based method names, so a student can write:

```python
dm = doubleMotor()
dm.connect('1128')       # connection card serial number
dm.turn_left(90)
dm.run_time(2000)
dm.stop()
```

instead of the equivalent raw `legoeducation` calls.

## The simplified Python library

On `main`, the library lives directly under `letranslationlib/` (one file per device, no `python/` subfolder):

| File | Class | Purpose |
|---|---|---|
| `single_motor_functions.py` | `singleMotor` | One motor: spin, run, run to a position |
| `double_motor_functions.py` | `doubleMotor` | Two-motor drive base: steps, timed runs, per-side control, turning |
| `color_sensor_functions.py` | `colorSensor` | Reads and names the detected color |
| `controller_functions.py` | `controller` | Remote/joystick input, plus a `drive()` teleop helper |
| `user_functions_list.py` | — | Human-readable API reference (a long block of bare docstring-style strings) shown to students, not a code-execution sandbox |

`lego_block_translator.py`, at the repo root, is a separate, more elaborate design that mirrors LEGO's own drag-and-drop "Coding Canvas" blocks 1:1 (`DoubleMotorProgram`, `SingleMotorProgram`, `ColorSensorProgram`). Rather than executing immediately, it *queues* block-style commands (`start_moving`, `turn`, `move`, `set_light`, `beep`, `repeat`, `when_color_detected`, …) and replays them in one `run()` call, with its own printable block-to-Python cheat sheet (`print_reference()` / `BLOCK_REFERENCE`).

## `pyscript_website/` — the in-browser PyScript app

`main`'s active web-app effort is a genuine **[PyScript](https://pyscript.net)** app (not a hand-rolled Pyodide bootstrap):

- **`pyscript.toml`** is the real PyScript config: it micropip-installs the `legoeducation` package, stages the sibling `*_functions.py` / `plot.py` files into PyScript's virtual filesystem via `[files]`, and registers `ble.js` as a native JS module (`[js_modules.main]`) importable from Python.
- **`index.html`** loads the PyScript CDN bundle (`core.css` / `core.js`, release `2024.1.1`) and boots the app with `<script type="py" src="./main.py" config="./pyscript.toml"></script>` — PyScript's own module/config system, distinct from `web_app_pyodide`'s manual `loadPyodide()` + `from js import ...` approach.
- **`main.py`** is the entry point PyScript loads. It patches `legoeducation`'s internal worker so BLE calls dispatch through JS instead of a native thread (WASM has no threads), defines `LegoDevice` subclasses that build connect/disconnect UI per device, implements the "Run" button handler (`execute_user_code()` — an AST transform auto-`await`s student code and runs it as an `asyncio` task), `stop_user_code()`, and an AI-tutor chat bridge (`send_to_tutor()`).
- **`ble.js`** exports a `BLEDevice` class using the standard Web Bluetooth API against the same LEGO CS+AI GATT service used elsewhere in the project (`0000fd02-...`). Python reaches it via PyScript's native bridge: `from pyscript.js_modules.ble import BLEDevice`.
- **`plot.py`** is a working live-plotting implementation (Plotly-based, one chart per connected device, rolling 200-point buffers) — unlike the `web_app_pyodide` branch, where the equivalent plot feature is currently disabled in the UI as broken.
- The per-device function files here (`single_motor_functions.py`, `double_motor_functions.py`, `color_sensor_functions.py`, `controller_functions.py`) share the same class names and public API as `letranslationlib/`'s, adapted for non-blocking single-threaded WASM execution (`blocking=False` everywhere, `turn_left`/`turn_right`/`run_time`/`drive()` became `async def`), plus new getters (`get_speed`, `get_power`, `get_position`, `get_absolute_position`) and extra color-sensor reads (`detect_rgb`, `detect_hue`, `detect_saturation`, `detect_reflection`) not present in `letranslationlib/`.
- **`.gitignore`** keeps `config.js` and `.env` out of version control — `config.js` is referenced from `pyscript.toml`'s JS modules table and is presumably where a local AI-tutor API key lives (see [Known issues](#known-issues--repo-hygiene)).
- `pyscript_website/README.md` is currently just a two-line stub (`"TO DO"` / a note about a planned click-to-copy/drag-and-drop function palette) — active work in progress, not yet documented.

## The legacy desktop server

`letranslationlib/server.py` is a small Flask app (`/exec`, `/stop`-style routes) that `exec()`s student code server-side against the real `legoeducation` BLE library, intended to sit behind a native desktop shell rather than a browser. It predates the `pyscript_website/` browser app and isn't currently wired to it.

## Repository layout

```
README.md
lego_block_translator.py       # alternate block-style translator (standalone)
letranslationlib/              # simplified library (flat files) + legacy Flask desktop server
  single_motor_functions.py, double_motor_functions.py,
  color_sensor_functions.py, controller_functions.py
  user_functions_list.py       # student-facing API reference
  server.py                    # legacy local Flask exec server (desktop-app era)
  index.html, tests.py, all_functions_test.py
pyscript_website/              # active in-browser PyScript app (see above)
  index.html, main.py, ble.js, plot.py
  single_motor_functions.py, double_motor_functions.py,
  color_sensor_functions.py, controller_functions.py
  pyscript.toml
experiments/                   # ad-hoc hardware prototyping scripts (raw legoeducation calls)
```

## Running it locally

**`pyscript_website/` (in-browser PyScript app):**
1. Serve `pyscript_website/` over HTTP (Web Bluetooth needs a secure/local context, not `file://`), e.g. `python3 -m http.server` from inside that folder.
2. Provide a local `config.js` (gitignored — not included in the repo) if the AI tutor bridge needs one.
3. Open `index.html` in Chrome or Edge, connect a device over Bluetooth, then write and Run code.

**Legacy desktop server:** `python letranslationlib/server.py`, paired with a native shell that posts code to it over `localhost`.

## Branches

`main` is an active line of development in its own right — it is **not** a frozen baseline. It forked the `web_app` / `claude_app_pascale` lineage at commit `6314cb9` (2026-06-09) but has since continued forward independently with the introduction of `pyscript_website/`, so those branches no longer contain everything on current `main`.

| Branch | What it is |
|---|---|
| `main` | This branch. Original translation library plus the active `pyscript_website/` PyScript browser app. |
| `chris_claude` | An early, independent rewrite of the library by a different contributor, introducing a differently-shaped API (`Motor("3683")`, `Robot("3683")` in `lego_easy.py`). Forked before this branch's current tip existed; abandoned. |
| `web_app` | Forked from `main` at `6314cb9`. Turns the library into a native **Electron desktop app**: a rewritten `letranslationlib/index.html`, a PyInstaller-bundled Flask server, a reorganized `letranslationlib/python/` package, and a Render-hosted proxy for a chatbot's API key. |
| `web_app_windows` | A narrow follow-on to `web_app` fixing Windows-specific PyInstaller packaging and a Render proxy warm-up ping. |
| `web_app_pyodide` | Forked from `web_app`. Converts the desktop app into a browser-based app using **raw Pyodide** (manual `loadPyodide()`/`from js import`) + hand-rolled Web Bluetooth, deployed via GitHub Pages. Has its own detailed README. |
| `claude_app_pascale` | Forked from `main` at `6314cb9`. An early chatbot-tutor prototype that called the Anthropic SDK directly from a local server using a `.env`-stored API key; superseded by the proxy-based design used on `web_app` onward. |

Net effect: there are currently **two independent, unreconciled prototypes** of "run the simplified library in-browser over Web Bluetooth" — `main`'s `pyscript_website/` (real PyScript) and `web_app_pyodide`'s hand-rolled Pyodide app. Worth comparing and consolidating before choosing one to ship.

## Known issues / repo hygiene

- **Stray scratch files at the repo root**: `newfiletest` (literally just the text "hello this is a test file") and `single_motor_test.py` (a duplicate of `experiments/single_motor_test.py`) look like leftover scratch/test artifacts rather than intentional project files.
- **`pyscript_website/README.md`** is just a `"TO DO"` stub — no setup/run instructions live there yet even though the app itself is fairly built out.
- **`config.js`** (gitignored, referenced by `pyscript.toml`) presumably holds a local AI-tutor API key with no proxy in front of it in this branch — worth checking it isn't shipped to students directly, the way `web_app`/`web_app_pyodide` hide their key behind a hosted Flask proxy.
- **`letranslationlib/user_functions_list.py`** has a stale docstring claiming `controller.left_position()`/`right_position()` return `'UP'`/`'DOWN'`/`'RELEASED'` — the actual implementation returns a raw numeric percentage.
