import multiprocessing
import signal
import os
import threading
import json
import sys
from io import StringIO

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

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


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(port=5001, threaded=True)
