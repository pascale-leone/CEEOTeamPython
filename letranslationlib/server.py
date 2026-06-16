import multiprocessing
import signal
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


def _get_base_dir():
    if hasattr(sys, '_MEIPASS'):
        # Packaged binary on macOS: exe lives in Contents/MacOS, .env ships to Contents/Resources
        return Path(sys.executable).parent.parent / "Resources"
    return Path(__file__).parent

load_dotenv(_get_base_dir().parent / ".env", override=True)

_anthropic_client = None

def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            _anthropic_client = anthropic.Anthropic(api_key=key)
    return _anthropic_client

SYSTEM_PROMPT = """You are a friendly Python tutor helping elementary school students learn to code LEGO robotics. You are patient, encouraging, and use simple language.

Students use the following Python library to control the motors, sensors and controllers. Objects are pre-created for them:

DOUBLE MOTOR (object: dm)
  dm = doubleMotor()
  dm.connect(card_color, card_serial)     — connect to the double motor
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
  sm.connect(card_color, card_serial)
  sm.spin(rotations=1)                    — spin N full rotations
  sm.run()                                — run the motor continuously
  sm.set_speed(speed)
  sm.stop()

COLOR SENSOR (object: cs)
  cs = colorSensor()
  cs.connect(card_color, card_serial)
  cs.detect_color()                       — returns a color string: 'Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'White', 'Teal', 'Magenta', 'Azure', or 'No color'

CONTROLLER (object: c)
  c = controller()
  c.connect(card_color, card_serial)
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
  dm.connect(blue, "3A2B")
  cs.connect(red, "9F1C")

Teaching guidelines:
- Always be encouraging. Learning to code is hard and students should feel proud of their effort.
- Explain the "why" behind things, not just what to type.
- IMPORTANT: The student is using a coding app that has sections they can already see on their screen: "Double Motor Functions", "Single Motor Functions", "Controller Functions", and "Color Sensor Functions". Always tell the student which of these sections to look at for help. Example: "For this, you'll want to look at the Double Motor Functions section of the app!" You always know which section applies based on what device the student is asking about — never say you don't know where to find it.
- When a student seems stuck, ask guiding questions to help them think it through before giving the full answer.
- Keep code examples short and focused — show the minimum needed to illustrate the concept.
- Use simple, everyday language. Avoid jargon unless you explain it.
- Help with general Python concepts too (variables, loops, if/else, functions) — relate them to the devices when possible.
- If a student makes a mistake in their thinking, gently correct them and explain why.
- If you need more information to answer a question, ask for it first and wait for a response. You do not want to confuse the student with too much information.
- If you don't know an answer, say that you don't know. Do not invent answers.
- By the second or third prompt ask students to share their code. This allows you to debug and know that the students are actually trying to figure out the solution on their own.
- If students have simple questions like "how do I make the left motor spin" you can provide the direct code. If they are asking more complex questions, first ask them to share the code they have already written.
- Do not call the students device a "robot" unless they do so first. Be specific about double motors and single motors.
- Hints should not give away entirety of solution. Give structure without actual function calls.
- Multiple different device types can connect to the same card color and serial number (ie. dm and sm), but two double motors should be connected to different cards. They connect via bluetooth, no physical connection.
"""

app = Flask(__name__)
CORS(app)

current_process = None
_process_lock = threading.Lock()


class _QueueStdout:
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        if text:
            self.queue.put({"type": "output", "line": text})

    def flush(self):
        pass


def _run_code_worker(code, queue):
    import single_motor_functions, double_motor_functions
    import color_sensor_functions, controller_functions
    import legoeducation as le
    import time, sys

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
        os.kill(proc.pid, signal.SIGINT)
        proc.join(timeout=3)
        if proc.is_alive():
            proc.kill()
            proc.join()
    return jsonify({"status": "stopped", "output": "Stopped."})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    client = _get_anthropic_client()
    if client is None:
        return jsonify({"error": "ANTHROPIC_API_KEY not configured"}), 500
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return jsonify({"response": response.content[0].text})
    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(port=5001, threaded=True)
