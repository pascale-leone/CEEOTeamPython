# CEEO Team Python — Summer 2026

A [Tufts CEEO](https://ceeo.tufts.edu/) project that lets kids control LEGO Education **CS+AI hub** robots (Single Motor, Double Motor, Color Sensor, and Controller "cards") by writing a small number of simple, English-verb Python functions — `dm.turn_left(90)`, `sm.spin(2)`, `cs.detect_color()` — instead of dealing with LEGO's full BLE/RPC API directly. The project also includes an AI chatbot "tutor" that helps students while they code.

The repository has evolved through several branches, from an early proof-of-concept translation library, to a native desktop app, to its current form: **a fully browser-based app that runs Python in-browser via Pyodide (WASM) and talks to the robot directly over Web Bluetooth.**

> This README describes both the simplified library shared across the project and what each branch in the repo contributes. It reflects `web_app_pyodide` (the current, most actively developed branch) unless a section says otherwise.

---

## Table of contents

- [What problem this solves](#what-problem-this-solves)
- [The simplified Python library](#the-simplified-python-library)
- [How code actually reaches the robot](#how-code-actually-reaches-the-robot)
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

The canonical version of the library lives in `letranslationlib/python/`. It's split one file per LEGO device, each a subclass of the matching `legoeducation` class:

| File | Class | Purpose |
|---|---|---|
| `single_motor_functions.py` | `singleMotor(le.SingleMotor)` | One motor: spin, run, run to a position |
| `double_motor_functions.py` | `doubleMotor(le.DoubleMotor)` | Two-motor drive base: steps, timed runs, per-side control, turning |
| `color_sensor_functions.py` | `colorSensor(le.ColorSensor)` | Reads and names the detected color |
| `controller_functions.py` | `controller(le.Controller)` | Remote/joystick input, plus a `drive()` teleop helper |
| `lelib.py` | — | Convenience module that re-exports all four classes plus `wait()` and color-name constants |
| `user_functions_list.py` | — | Human-readable API reference / scaffold template shown to students (has a `"MY CODE GOES HERE!"` placeholder), not a code-execution sandbox |

### Student-facing API

**Single Motor**
- `connect(card_serial, card_color=None)` — connect, with automatic retry on transient BLE errors
- `spin(rotations=1)` / `stop()` / `set_speed(speed)` / `run()` / `run_to(degrees=90)`
- `position()` — current absolute position
- `plot()` — live-streams motor position to the UI for graphing

**Double Motor**
- `connect(card_serial, card_color=None)`
- `move_steps(step=1)` (1 step = 180°), `run()`, `run_time(time=2000)`
- `run_left_to(degrees)` / `run_right_to(degrees)`, `run_left(degrees=None)` / `run_right(degrees=None)`
- `turn_left(degrees=90)` / `turn_right(degrees=90)`
- `set_speed(speed)` / `set_speed_left(speed)` / `set_speed_right(speed)` / `stop()`
- `left_position()` / `right_position()`, `plot_left()` / `plot_right()`

**Color Sensor**
- `connect(card_serial, card_color=None)`
- `detect_color()` — returns a human-readable name (`'Red'`, `'Azure'`, …) mapped from the raw sensor value

**Controller**
- `connect(card_serial, card_color=None)`
- `left_up()` / `left_down()` / `left_released()`, `right_up()` / `right_down()` / `right_released()`
- `left_position()` / `right_position()` — raw joystick percentages
- `drive(dm, t=100)` — reads both sticks and drives a `doubleMotor` tank-style for `t` iterations

**Module-level:** `wait(seconds)`, plus color-name constants (`azure`, `blue`, `red`, `yellow`, …).

### An alternate translator: `lego_block_translator.py`

At the repo root, `lego_block_translator.py` is a separate, more elaborate design that mirrors LEGO's own drag-and-drop "Coding Canvas" blocks 1:1 (`DoubleMotorProgram`, `SingleMotorProgram`, `ColorSensorProgram`). Rather than executing immediately, it *queues* block-style commands (`start_moving`, `turn`, `move`, `set_light`, `beep`, `repeat`, `when_color_detected`, …) and replays them in one `run()` call. It ships its own printable block-to-Python cheat sheet (`print_reference()` / `BLOCK_REFERENCE`) and demo programs. This looks like an exploratory alternative to the `letranslationlib` design rather than something the current app depends on.

## How code actually reaches the robot

Neither this repo's wrapper classes nor `legoeducation` are reimplemented from scratch here — `legoeducation` (BLE RPC over `bleak`) does the real Bluetooth work in the desktop-app branches. The **current browser-based app takes a different path entirely**:

1. **Pyodide** (Python compiled to WebAssembly) runs directly in the browser tab, loaded from CDN in `letranslationlib/index.html` / `docs/index.html`.
2. A large embedded Python string (`SHIMS`) defines browser-native `singleMotor` / `doubleMotor` / `colorSensor` / `controller` classes whose methods are `async` wrappers that call straight out to JavaScript via Pyodide's `from js import ...`.
3. `letranslationlib/lego_ble.js` (and its byte-identical copy in `docs/`) implements the actual **Web Bluetooth** connection: it talks to the LEGO CS+AI hub's GATT service (`0000fd02-...`) directly from the browser tab — no native app, no local server, no `bleak` — parsing the same RPC message framing `legoeducation` uses (`MOTOR_RUN_COMMAND`, `MOTOR_RUN_TO_ABSOLUTE_POSITION_COMMAND`, `DEVICE_NOTIFICATION`, etc.), and exposes plain functions (`motorRunToAbsolutePosition`, `getLeftPosition`, `legoConnect`, `legoStopAll`, …) on `window` for Python to call.
4. Before running, student code is passed through a Python AST transform (`_auto_await`) that inserts the `await`s a student never has to type, and — importantly — injects a yield/stop-check into every loop body so a runaway `while True:` can't freeze the single-threaded WASM runtime or crash the tab (this was the subject of several recent bug-fix commits).

Because this all runs client-side, **the app must be served over HTTP(S) and opened in a browser that supports Web Bluetooth (e.g. Chrome/Edge on desktop)** — there is no backend needed to run student code or talk to the robot in this branch.

Earlier in the project's history (see [Branches](#branches)), the same simplified library was instead hosted by a local Flask server (`letranslationlib/server.py`, bundled into a standalone executable via PyInstaller/`server.spec`) that a native Electron desktop app talked to over HTTP — this is still how the `web_app` and `web_app_windows` branches work.

## The AI tutor chatbot

Students can ask an "Ask the Tutor" panel for help. The system prompt bakes in a "documentation-first" teaching style (point students at the docs before handing them code) and the full simplified API reference.

To keep the Anthropic API key off student machines, the tutor never calls Anthropic directly:

```
browser (index.html tutor panel)  →  proxy/proxy_server.py  →  Anthropic API (claude-haiku-4-5)
```

- `proxy/proxy_server.py` — a minimal Flask app deployed to **Render.com** (`ceeoteampython.onrender.com`) that holds the real `ANTHROPIC_API_KEY`, optionally checks a shared secret header, and forwards chat requests to Anthropic.
- `chatbot/` — a standalone chat demo (`chat.html` + `chat_server.py`) that adds its own local Flask hop in front of the same proxy; used for local testing of the chatbot UI independent of the main app.
- An earlier design (see the `claude_app_pascale` branch) called the Anthropic SDK directly from a local server using a `.env`-stored API key — this was replaced by the Render proxy approach to avoid distributing API keys with the desktop app.

## Repository layout

```
lego_block_translator.py     # alternate block-style translator (root-level, standalone)
docs/                        # GitHub Pages deployment mirror of the browser app (what students actually open)
  index.html                 # code editor UI, Pyodide bootstrap, tutor panel
  lego_ble.js                # Web Bluetooth layer
  images/                    # docs images (connection cards, per-device diagrams)
letranslationlib/            # primary working source tree
  index.html, lego_ble.js    # source of truth for the browser app (synced into docs/)
  python/                    # the simplified library described above
  server.py, server.spec     # legacy local Flask server + PyInstaller build spec (desktop-app branches)
  tests/, build/, dist/      # manual hardware smoke tests; PyInstaller build output (see Known issues)
chatbot/                     # standalone chatbot demo (chat.html + Flask relay)
proxy/                       # Render-hosted Flask proxy that holds the Anthropic API key
experiments/                 # ad-hoc hardware prototyping scripts (raw legoeducation calls, matplotlib plot prototype)
```

## Running it locally

**Browser app (current branch):**
1. Serve the repo over HTTP (Web Bluetooth requires a secure/local context, not `file://`), e.g. `python3 -m http.server` from the repo root.
2. Open `letranslationlib/index.html` (or `docs/index.html`, the deployed GitHub Pages version) in Chrome or Edge.
3. Click a device's Connect button, pick the matching physical LEGO card over Bluetooth, then write and Run code.
4. The tutor panel talks to the hosted Render proxy directly — no local chatbot server is required unless you want to test `chatbot/` in isolation.

**Standalone chatbot demo:** `pip install -r chatbot/requirements.txt && python chatbot/chat_server.py`, then open the URL it prints.

**Desktop app (older branches, `web_app` / `web_app_windows`):** run `letranslationlib/server.py` (or the prebuilt `letranslationlib/dist/server.exe` on Windows) and the Electron shell (`main.js`) talks to it over `localhost:5001`.

## Branches

```
main (frozen, 2026-06-09) ──┬── web_app (2026-06-26) ──┬── web_app_windows (2026-06-26)
                             │                           └── web_app_pyodide (2026-07-08+) ← current
                             └── claude_app_pascale (2026-06-16)

chris_claude (independent, 2026-06-05 – 06-08, abandoned)
```

| Branch | Status | What it is |
|---|---|---|
| `main` | Frozen since 2026-06-09 | The original translation library: single/double motor + sensor functions, a basic desktop server, and the very first stub of "web app" work. Every other branch is a strict descendant — nothing has been merged back. |
| `chris_claude` | Abandoned (last commit 2026-06-08) | An early, independent rewrite of the library by a different contributor, introducing a differently-shaped API (`Motor("3683")`, `Robot("3683")` in `lego_easy.py`). Forked before `main`'s current tip existed; never merged. |
| `web_app` | Superseded (last commit 2026-06-26) | Turns the library into a native **Electron desktop app**: adds a rewritten `index.html`, a PyInstaller-bundled Flask server (`server.py`/`server.spec`), a reorganized `letranslationlib/python/` package, and the Render-hosted `proxy/` for the chatbot's API key. Fully contains `main`. |
| `web_app_windows` | Dormant side-branch (last commit 2026-06-26, same day as its fork) | A narrow follow-on to `web_app` fixing **Windows-specific PyInstaller packaging** (`hiddenimports` for `requests`/`certifi`/etc.), installer config, and a Render proxy "warm-up" ping to hide cold-start latency. Nothing builds on top of it. |
| `web_app_pyodide` | **Active — current branch** (through 2026-07-08 plus local work) | Converts the desktop app into a **fully browser-based app**: drops Electron/PyInstaller in favor of Pyodide (Python-in-WASM) + Web Bluetooth (`lego_ble.js`), adds the `docs/` GitHub Pages mirror, and removes the native shell. Most of its history since is bug-fixing/polish on the in-browser runtime (runaway-loop crashes, Stop button state, motor position readbacks, multi-device BLE, hiding the broken plot UI). |
| `claude_app_pascale` | Superseded (last commit 2026-06-16) | An early chatbot-tutor prototype for the desktop app that called the Anthropic SDK **directly** from a local server using a `.env`-stored API key (no proxy). Replaced by the Render-proxy design that shipped in `web_app` onward. Fully contains `main`. |

## Known issues / repo hygiene

- **`letranslationlib/build/` and `letranslationlib/dist/`** (PyInstaller output, including the ~14.6MB `server.exe`) are listed in `.gitignore` but are nonetheless tracked in git — leftover from the pre-Pyodide desktop-app era and no longer needed on this branch. Worth removing from version control.
- **`letranslationlib/SimpleLE/`** is an empty directory — likely a placeholder from an earlier/renamed component.
- **`docs/` and `letranslationlib/` have drifted slightly**: `docs/index.html` currently has a multi-line comment toggle and copy-to-clipboard buttons (commit `3d13946`) that haven't been ported back to `letranslationlib/index.html`, the nominal source of truth. Keep these in sync when editing the editor UI.
- **The live-plotting feature is currently disabled in the UI** (commit `b781488`, "Hide broken plot feature from UI for stakeholder demo") — the underlying Python/JS plotting code (`plot()`, `plot_left()`, `plot_right()`, Chart.js panels) still works if called directly, but its buttons, docs, and autocomplete entries are commented out pending a fix.
