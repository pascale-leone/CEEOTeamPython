# CEEO Team Python — Summer 2026

A [Tufts CEEO](https://ceeo.tufts.edu/) project that lets kids control LEGO Education **CS+AI hub** robots (Single Motor, Double Motor, Color Sensor, and Controller "cards") by writing a small number of simple, English-verb Python functions — `dm.turn_left(90)`, `sm.spin(2)`, `cs.detect_color()` — instead of dealing with LEGO's full BLE/RPC API directly. The project also includes an AI chatbot "tutor" that helps students while they code.

This branch (`web_app`) packages that library as a **native desktop app**: an Electron shell around a code editor, backed by a bundled Python/Flask server that does the actual Bluetooth communication with the robot over the real `legoeducation` library.

> This README describes `web_app` as it stands. Two later branches fork from here: `web_app_windows` (Windows packaging fixes) and `web_app_pyodide` (converts this same app to run fully in-browser via Pyodide + Web Bluetooth instead of a native shell — see that branch's own README). `main` is a separate, independent line that has since gained its own browser app, `pyscript_website/` (built on the real PyScript framework). See [Branches](#branches).

---

## Table of contents

- [What problem this solves](#what-problem-this-solves)
- [The simplified Python library](#the-simplified-python-library)
- [How the desktop app works](#how-the-desktop-app-works)
- [The AI tutor chatbot](#the-ai-tutor-chatbot)
- [Repository layout](#repository-layout)
- [Running it locally](#running-it-locally)
- [Branches](#branches)
- [Known issues / repo hygiene](#known-issues--repo-hygiene)

---

## What problem this solves

LEGO Education's official `legoeducation` Python package is a real BLE/RPC driver (`pip install legoeducation`, built on `bleak`) with the kind of API a professional developer expects: verbose method names, enums, manual connect/retry handling, raw device objects. That's too much for the elementary/middle-school students this project targets.

This repo wraps `legoeducation` in thin, kid-friendly subclasses with short verb-based method names and built-in connection retry logic, so a student can write:

```python
dm = doubleMotor()
dm.connect('1128')       # connection card serial number
dm.turn_left(90)
dm.run_time(2000)
dm.stop()
```

instead of the equivalent raw `legoeducation` calls with degree/direction/enum plumbing.

## The simplified Python library

The library lives in `letranslationlib/python/`, one file per LEGO device, each a subclass of the matching `legoeducation` class:

| File | Class | Purpose |
|---|---|---|
| `single_motor_functions.py` | `singleMotor(le.SingleMotor)` | One motor: spin, run, run to a position |
| `double_motor_functions.py` | `doubleMotor(le.DoubleMotor)` | Two-motor drive base: steps, timed runs, per-side control, turning |
| `color_sensor_functions.py` | `colorSensor(le.ColorSensor)` | Reads and names the detected color |
| `controller_functions.py` | `controller(le.Controller)` | Remote/joystick input, plus a `drive()` teleop helper |
| `lelib.py` | — | Convenience module that re-exports all four classes plus `wait()` and color-name constants |
| `user_functions_list.py` | — | Human-readable API reference shown to students, not a code-execution sandbox |

Student-facing API: `connect(card_serial, card_color=None)`, `spin()`/`run()`/`run_to()`/`position()`/`plot()` (single motor); `move_steps()`, `run()`, `run_time()`, `run_left()`/`run_right()`, `turn_left()`/`turn_right()`, `set_speed*()`, `left_position()`/`right_position()`, `plot_left()`/`plot_right()` (double motor); `detect_color()` (color sensor); `left_up()`/`left_down()`/`left_released()`, the right-side equivalents, `left_position()`/`right_position()`, `drive(dm, t=100)` (controller); plus module-level `wait(seconds)` and color-name constants.

At the repo root, `lego_block_translator.py` is a separate, more elaborate design that mirrors LEGO's own drag-and-drop "Coding Canvas" blocks 1:1, queuing block-style commands and replaying them in one `run()` call. It's an exploratory alternative that this app doesn't depend on.

## How the desktop app works

Unlike the later `web_app_pyodide` branch, this app does **not** run Python in the browser or use Web Bluetooth — all Bluetooth communication happens natively via `legoeducation`/`bleak` inside a bundled Python process:

1. **`letranslationlib/main.js`** is the Electron main process. On launch it spawns a packaged Python/Flask executable (`dist/server`, built via PyInstaller from `server.py`/`server.spec`), polls `http://localhost:5001/` until it responds, then opens a `BrowserWindow` loading `letranslationlib/index.html`.
2. **`letranslationlib/index.html`** is a CodeMirror-based code editor (with autocomplete, a Chart.js live-plotting panel, and an "Ask the Tutor" chat side panel) that talks to the local Flask server over HTTP, not to the robot directly.
3. **`letranslationlib/server.py`** is the real backend: `POST /exec` runs student code in a separate `multiprocessing.Process` (importing the simplified library and calling straight into `legoeducation`), streaming stdout back to the browser as Server-Sent Events (including a special marker for live-plot data points); `POST /stop` signals the running process to stop; `POST /chat` forwards tutor questions to the hosted proxy (see below).
4. **`letranslationlib/server.spec`** is the PyInstaller build spec that bundles `server.py` and its dependencies into the standalone `dist/server` executable Electron spawns; **`letranslationlib/package.json`** configures `electron-builder` to package `main.js` + `index.html` + `dist/server` into a signed `.dmg` for macOS.

Because BLE happens in the native Python process rather than in the browser, there's no Web Bluetooth requirement here — but it does mean each target OS needs its own PyInstaller build (this branch is macOS-focused; see `web_app_windows` for the Windows packaging work).

## The AI tutor chatbot

The "Ask the Tutor" panel's system prompt bakes in a "documentation-first" teaching style (point students at the docs before handing them code) and the full simplified API reference.

To keep the Anthropic API key off student machines, the chain of calls is:

```
browser (index.html tutor panel) → local Flask server (server.py /chat) → proxy/proxy_server.py (Render.com) → Anthropic API (claude-haiku-4-5)
```

- `letranslationlib/server.py`'s `/chat` route is the first hop — it holds the big tutor system prompt and forwards to `proxy/proxy_server.py`.
- `proxy/proxy_server.py` — a minimal Flask app deployed to **Render.com** (`ceeoteampython.onrender.com`) that holds the real `ANTHROPIC_API_KEY`, optionally checks a shared secret header, and is the only place that actually calls Anthropic.
- `chatbot/` — a standalone chat demo (`chat.html` + `chat_server.py`) with its own near-duplicate system prompt and Flask relay to the same proxy, used for testing the chatbot UI independent of the main app.

## Repository layout

```
lego_block_translator.py     # alternate block-style translator (root-level, standalone)
letranslationlib/
  main.js, package.json      # Electron shell + electron-builder packaging config
  index.html                 # code editor UI, plotting, tutor panel — talks to localhost:5001
  server.py, server.spec     # Flask backend (real legoeducation/bleak BLE) + PyInstaller build spec
  build/                     # PyInstaller build output (see Known issues)
  python/                    # the simplified library described above
  tests/                     # manual hardware smoke tests
  images/                    # connection-card / per-device reference images
chatbot/                     # standalone chatbot demo (chat.html + Flask relay)
proxy/                       # Render-hosted Flask proxy that holds the Anthropic API key
experiments/                 # ad-hoc hardware prototyping scripts (raw legoeducation calls, matplotlib plot prototype)
```

## Running it locally

1. Build the bundled server once: `cd letranslationlib && pyinstaller server.spec` (produces `dist/server`, gitignored and not checked in).
2. `npm install` in `letranslationlib/`, then `npm start` to launch the Electron app — it spawns `dist/server`, waits for it to come up on port 5001, and opens the editor window.
3. Connect the physical LEGO cards (native BLE via `bleak`, no browser Bluetooth permissions needed), then write and run code.
4. To package a distributable app: `npm run build` (macOS `.dmg` via `electron-builder`, per `package.json`).

For quick iteration without Electron, you can also run `python letranslationlib/server.py` directly and open `letranslationlib/index.html` in a browser — the editor only needs the Flask server reachable at `localhost:5001`.

**Standalone chatbot demo:** `pip install -r chatbot/requirements.txt && python chatbot/chat_server.py`, then open the URL it prints.

## Branches

`web_app` forks from `main` at `6314cb9` (2026-06-09). `main` itself is not frozen — it has since gained its own independent browser app, `pyscript_website/` (real PyScript), so `main` and `web_app` have diverged rather than one containing the other.

```
                             ┌── web_app (this branch, 2026-06-26) ──┬── web_app_windows (2026-06-26)
main (6314cb9, 2026-06-09) ──┤                                       └── web_app_pyodide (2026-07-08+)
                             └── claude_app_pascale (2026-06-16)

main itself kept moving after that fork point, adding pyscript_website/
— a second, independent in-browser app (see main's own README).

chris_claude (independent, 2026-06-05 – 06-08, abandoned)
```

| Branch | Status | What it is |
|---|---|---|
| `main` | Active, independent line | The original translation library plus `pyscript_website/`, a separate PyScript-based browser app built independently of this branch. |
| `chris_claude` | Abandoned | An early, independent rewrite of the library by a different contributor (`Motor("3683")`/`Robot("3683")` API in `lego_easy.py`). Never merged. |
| `web_app` | **This branch.** Superseded by its own children below (last commit 2026-06-26) | The native Electron desktop app described in this README: bundled PyInstaller Flask backend, real `legoeducation`/`bleak` BLE, chatbot + Render proxy. |
| `web_app_windows` | Dormant side-branch of `web_app` (last commit 2026-06-26, same day as its fork) | Windows-specific PyInstaller packaging fixes (`hiddenimports` for `requests`/`certifi`/etc.), installer config, and a Render proxy warm-up ping. |
| `web_app_pyodide` | Active — forked from `web_app` | Converts this same app to run fully in-browser via Pyodide (Python-in-WASM) + Web Bluetooth, dropping Electron/PyInstaller entirely. Has its own detailed README. |
| `claude_app_pascale` | Superseded | An early chatbot-tutor prototype that called the Anthropic SDK directly from a local server using a `.env`-stored API key (no proxy) — replaced by the Render-proxy design used here. |

## Known issues / repo hygiene

- **`letranslationlib/build/`** (PyInstaller intermediate build output) is listed in `.gitignore` but is nonetheless tracked in git — likely added before the ignore rule existed. `dist/` (the actual executable) is correctly left untracked.
- **`chatbot/chat_server.py` and `letranslationlib/server.py`** carry two independently-maintained copies of the same large tutor system prompt — worth consolidating into one shared source so they don't drift.
- This branch targets **macOS only** (`electron-builder` config builds a `.dmg`); Windows packaging is handled entirely on the separate `web_app_windows` branch rather than being conditional here.
