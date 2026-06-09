import single_motor_functions
import double_motor_functions
import color_sensor_functions
import controller_functions
import legoeducation as le
import time
import io, sys

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# create device instances once — user connects them in their code
# cs = color_sensor_functions.colorSensor()
# dm = double_motor_functions.doubleMotor()
# sm = single_motor_functions.singleMotor()


def wait(seconds):
    time.sleep(seconds)

# everything the user can reference in their typed code
NAMESPACE = {
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
    "time": time,
}

@app.route("/exec", methods=["POST"])
def run_code():
    code = request.json["code"]
    buffer = io.StringIO()
    sys.stdout = buffer
    try:
        exec(code, NAMESPACE)
        output = buffer.getvalue()
        return jsonify({"status": "ok", "output": output or "Done"})
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)})
    finally:
        sys.stdout = sys.__stdout__

if __name__ == "__main__":
    app.run(port=5001)