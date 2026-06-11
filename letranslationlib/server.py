import multiprocessing
import signal
import os
import threading

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

current_process = None
_process_lock = threading.Lock()


def _run_code_worker(code, queue):
    import single_motor_functions, double_motor_functions
    import color_sensor_functions, controller_functions
    import legoeducation as le
    import time, io, sys

    def wait(seconds):
        time.sleep(seconds)

    buffer = io.StringIO()
    sys.stdout = buffer

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
        output = buffer.getvalue()
        queue.put({"status": "ok", "output": output or "Done"})
    except KeyboardInterrupt:
        queue.put({"status": "stopped", "output": "Stopped."})
    except Exception as e:
        queue.put({"status": "error", "output": str(e)})
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
    global current_process
    code = request.json["code"]
    queue = multiprocessing.Queue()

    with _process_lock:
        current_process = multiprocessing.Process(target=_run_code_worker, args=(code, queue))
        current_process.start()

    current_process.join()

    with _process_lock:
        current_process = None

    try:
        result = queue.get(timeout=1)
    except:
        result = {"status": "stopped", "output": "Stopped."}
    return jsonify(result)


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
