import multiprocessing
import os
import threading
import json
import sys
from io import StringIO
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS


def _find_env():
    if hasattr(sys, '_MEIPASS'):
        exe_dir = Path(sys.executable).parent
        # Packaged .app: binary at Contents/Resources/server, .env is in same dir
        if (exe_dir / ".env").exists():
            return exe_dir / ".env"
        # Unpackaged dev: binary at letranslationlib/dist/server, .env is two levels up
        return exe_dir.parent.parent / ".env"
    # Running as script: server.py is in letranslationlib/, .env is one level up
    return Path(__file__).parent.parent / ".env"

load_dotenv(_find_env(), override=True)

_anthropic_client = None

def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            _anthropic_client = anthropic.Anthropic(api_key=key)
    return _anthropic_client

SYSTEM_PROMPT = """You are a friendly Python tutor helping elementary school students learn to code LEGO robotics. You are patient, encouraging, and use simple language.

## DOCUMENTATION-FIRST RULE — FOLLOW THIS BEFORE EVERY ANSWER ##
The student's app has five built-in documentation sections visible on their screen:
  - "Double Motor Functions"
  - "Single Motor Functions"
  - "Controller Functions"
  - "Color Sensor Functions"
  - "General Python tips!"

BEFORE giving any code or direct answer about how to use a device, you MUST:
1. Tell the student which section to look at first.
2. Ask them to read it and come back with what they found.
3. Only give direct code or a detailed answer AFTER the student says they already checked the docs or asks a follow-up.

Example of a correct first response to "How do I make my car move forward?":
  "Great question! First, check out the Double Motor Functions section in your app — it has all the commands for making your car move. Read through it and let me know what you find, or if you have questions about something specific!"

NEVER give code or a step-by-step answer on the first message about a new topic. Always point to the docs first.

---

Students use the following Python library to control the motors, sensors and controllers. Objects are pre-created for them:

DOUBLE MOTOR (object: dm)
  dm = doubleMotor()
  dm.connect(card_serial, card_color=None)     — connect to the double motor
  dm.move_steps(step=1)                   — move forward N steps (1 step = 180 degrees of rotation)
  dm.run()                                — run both motors continuously (if wait(seconds) used after, otherwise will only move a small amount) (both motors must run at same speed)
  dm.run_time(time=2000)                  — run both motors for N milliseconds
  dm.run_left()                           — run left motor continuously
  dm.run_right()                          — run right motor continuously
  dm.turn_left(degrees=90)               — use when car is built --> turn the car left by N degrees
  dm.turn_right(degrees=90)              — use when car is built --> turn the car right by N degrees
  dm.set_speed(speed)                     — set speed for both motors
  dm.set_speed_left(speed)               — set speed for left motor only (will only run at this speed if left motor is run on its own)
  dm.set_speed_right(speed)              — set speed for right motor only (will only run at this speed if right motor is run on its own)
  dm.stop()                               — stop both motors

SINGLE MOTOR (object: sm)
  sm = singleMotor()
  sm.connect(card_serial, card_color=None)
  sm.spin(rotations=1)                    — spin N full rotations
  sm.run()                                — run the motor continuously
  sm.set_speed(speed)
  sm.stop()

COLOR SENSOR (object: cs)
  cs = colorSensor()
  cs.connect(card_serial, card_color=None)
  cs.detect_color()                       — returns a color string: 'Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'White', 'Teal', 'Magenta', 'Azure', or 'No color'

CONTROLLER (object: c)
  c = controller()
  c.connect(card_serial, card_color=None)
  c.drive(dm, t=100)                      — drive the car with joysticks for t iterations (0.1s each), default t=100, does not necessarily need time
  c.left_up()                             — True if left joystick pushed up
  c.left_down()                           — True if left joystick pushed down
  c.left_released()                       — True if left joystick released
  c.right_up()                            — True if right joystick pushed up
  c.right_down()                          — True if right joystick pushed down
  c.right_released()                      — True if right joystick released
  c.left_position()                       — left joystick position (-100 to 100)
  c.right_position()                      — right joystick position (-100 to 100)

Color constants for connect(): red, blue, green, yellow, orange, purple, white, black, teal, magenta, azure

Example connection:
  dm.connect("3212")
  cs.connect(card_serial="9015", card_color=blue)

Teaching guidelines:
- Always be encouraging. Learning to code is hard and students should feel proud of their effort.
- Explain the "why" behind things, not just what to type.
- CRITICAL RULE — ALWAYS follow this before giving any code or answer: The student's app has four built-in documentation sections they can read right now: "Double Motor Functions", "Single Motor Functions", "Controller Functions", and "Color Sensor Functions". For EVERY question about how to use a device, your FIRST response must point them to the relevant section. Say something like: "Great question! First, check out the Double Motor Functions section in your app — it lists all the commands you can use. Then come back and tell me what you found or if you have more questions!" Only give direct code or a full answer after the student has had a chance to look at the docs, or if they say they already checked. Never say you don't know which section applies — you always do based on the device they mention.
- When a student seems stuck, ask guiding questions to help them think it through before giving the full answer.
- Keep code examples short and focused — show the minimum needed to illustrate the concept.
- Use simple, everyday language. Avoid jargon unless you explain it.
- Help with general Python concepts too (variables, loops, if/else, functions) — relate them to the devices when possible.
- If a student makes a mistake in their thinking, gently correct them and explain why.
- If you need more information to answer a question, ask for it first and wait for a response. You do not want to confuse the student with too much information.
- If you don't know an answer, say that you don't know. Do not invent answers.
- By the second or third prompt ask students to share their code. This allows you to debug and know that the students are actually trying to figure out the solution on their own.
- Whether the question is simple or complex, always point to the relevant app section first. Only share code after the student has looked at the docs or explicitly says they already did.
- Do not call the students device a "robot" unless they do so first. Be specific about double motors and single motors.
- Hints should not give away entirety of solution. Give structure without actual function calls.
- Multiple different device types can connect to the same card (ie. dm and sm), but two double motors should be connected to different cards. They connect via bluetooth, no physical connection. Connection card looks like a playing card.
- Always say LEGO (all capitalized) not lego or Lego.  
"""

app = Flask(__name__)
CORS(app)

current_process = None
_process_lock = threading.Lock()


class _QueueStdout:
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        if not text:
            return
        if text.startswith("\x00PLOT\x00"):
            data = json.loads(text[6:])
            self.queue.put({"type": "plot_data", **data})
        else:
            self.queue.put({"type": "output", "line": text})

    def flush(self):
        pass


def _run_code_worker(code, queue):
    import sys, time
    from pathlib import Path
    _lib_dir = str(Path(__file__).parent / "python")
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    import single_motor_functions, double_motor_functions
    import color_sensor_functions, controller_functions
    import legoeducation as le

    def wait(seconds):
        time.sleep(seconds)

    sys.stdout = _QueueStdout(queue)

    fresh_namespace = {
        "colorSensor": color_sensor_functions.colorSensor,
        "doubleMotor": double_motor_functions.doubleMotor,
        "singleMotor": single_motor_functions.singleMotor,
        "controller": controller_functions.controller,
        "wait": wait,
        "le": le,
        "orange": le.LEGO_COLOR_ORANGE,
        "purple": le.LEGO_COLOR_PURPLE,
        "blue": le.LEGO_COLOR_BLUE,
        "magenta": le.LEGO_COLOR_MAGENTA,
        "pink": le.LEGO_COLOR_MAGENTA,
        "green": le.LEGO_COLOR_GREEN,
        "azure": le.LEGO_COLOR_AZURE,
        "teal": le.LEGO_COLOR_TEAL,
        "red": le.LEGO_COLOR_RED,
        "yellow": le.LEGO_COLOR_YELLOW,
        "white": le.LEGO_COLOR_WHITE,
        "time": time,
    }

    try:
        exec(code, fresh_namespace)
        queue.put({"type": "done", "status": "ok"})
    except KeyboardInterrupt:
        queue.put({"type": "done", "status": "stopped"})
    except SystemExit:
        queue.put({"type": "done", "status": "error"})
    except Exception as e:
        while not queue.empty():
            try:
                queue.get_nowait()
            except Exception:
                break
        queue.put({"type": "output", "line": str(e) + "\n"})
        if type(e) is TypeError:
            queue.put({"type": "output", "line":  str(e) + "\n\nMake sure your code matches the documentation exactly!\n"})
        queue.put({"type": "done", "status": "error"})
    finally:
        sys.stdout = sys.__stdout__
        for val in fresh_namespace.values():
            if hasattr(val, 'disconnect'):
                try:
                    val.disconnect()
                except:
                    pass


@app.route("/exec", methods=["POST"])
def run_code():
    code = request.json["code"]
    queue = multiprocessing.Queue()

    def generate():
        global current_process
        proc = multiprocessing.Process(target=_run_code_worker, args=(code, queue))
        with _process_lock:
            current_process = proc
        proc.start()

        has_output = False
        while True:
            try:
                msg = queue.get(timeout=0.1)
            except Exception:
                if not proc.is_alive():
                    if not has_output:
                        yield f"data: {json.dumps({'type': 'output', 'line': 'Stopped.'})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'status': 'stopped'})}\n\n"
                    break
                continue

            if msg.get("type") == "output":
                has_output = True
                yield f"data: {json.dumps(msg)}\n\n"
            elif msg.get("type") == "plot_data":
                yield f"data: {json.dumps(msg)}\n\n"
            elif msg.get("type") == "done":
                if not has_output and msg.get("status") == "ok":
                    yield f"data: {json.dumps({'type': 'output', 'line': 'Done.'})}\n\n"
                yield f"data: {json.dumps(msg)}\n\n"
                break

        proc.join(timeout=1)
        with _process_lock:
            current_process = None

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/stop", methods=["POST"])
def stop_code():
    with _process_lock:
        proc = current_process
    if proc and proc.is_alive():
        proc.terminate()
        proc.join(timeout=3)
        if proc.is_alive():
            proc.kill()
            proc.join()
    return jsonify({"status": "stopped", "output": "Stopped."})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    code = data.get("code", "").strip()
    error = data.get("error", "").strip()
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    client = _get_anthropic_client()
    if client is None:
        return jsonify({"error": "ANTHROPIC_API_KEY not configured"}), 500

    system = SYSTEM_PROMPT
    if code:
        system += (
            "\n\n## Student's Current Code\n"
            "The student currently has this code in their editor:\n"
            f"```python\n{code}\n```\n"
            "Refer to it when giving feedback or debugging. If they haven't written anything relevant yet, ignore this section."
        )
    if error:
        system += (
            "\n\n## Error from Last Run\n"
            "The student's code produced this error when they ran it:\n"
            f"```\n{error}\n```\n"
            "Help them understand what the error means and how to fix it."
        )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return jsonify({"response": response.content[0].text})
    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(port=5001, threaded=True)
