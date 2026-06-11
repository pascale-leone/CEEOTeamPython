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


@app.route("/exec", methods=["POST"])
def run_code():
    code = request.json["code"]
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
        "azure" :   le.LEGO_COLOR_AZURE,
        "teal" :   le.LEGO_COLOR_TEAL,
        "green" :  le.LEGO_COLOR_GREEN,
        "red" :     le.LEGO_COLOR_RED,
        "yellow" :  le.LEGO_COLOR_YELLOW,
        "white" :   le.LEGO_COLOR_WHITE,
        "magenta" : le.LEGO_COLOR_MAGENTA,
        "time": time,
    }

    try:
        exec(code, fresh_namespace)
        output = buffer.getvalue()
        return jsonify({"status": "ok", "output": output or "Done"})
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)})
    finally:
        sys.stdout = sys.__stdout__
        for val in fresh_namespace.values():
            if hasattr(val, 'disconnect'):
                try:
                    val.disconnect()
                except:
                    pass

if __name__ == "__main__":
    app.run(port=5001)