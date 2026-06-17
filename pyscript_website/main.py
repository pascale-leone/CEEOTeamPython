# main.py — runs on the main thread via <script type="py">
import ast
import asyncio
import math
import sys
from pyscript import document, window
import legoeducation as le

# ══════════════════════════════════════════════════════════════
# WASM WORKER PATCH
# ══════════════════════════════════════════════════════════════
import legoeducation.background_worker as bw

def _wasm_start_thread(self):
    if getattr(self, '_wasm_loop_started', False):
        return
    self._wasm_loop_started = True
    if not hasattr(self, '_js_ble_registry'):
        self._js_ble_registry = {}
    try:
        loop = asyncio.get_running_loop()
        self.loop = loop
        self.loop_ready.set()
        asyncio.ensure_future(_wasm_worker_loop(self))
    except RuntimeError:
        pass

def _wasm_put_request(self, request):
    if not self.loop_ready.is_set():
        try:
            loop = asyncio.get_running_loop()
            self.loop = loop
            self.loop_ready.set()
            if not hasattr(self, '_js_ble_registry'):
                self._js_ble_registry = {}
            asyncio.ensure_future(_wasm_worker_loop(self))
        except RuntimeError:
            return
    asyncio.ensure_future(self.async_put_request(request))

bw.Worker.start_thread = _wasm_start_thread
bw.Worker.put_request  = _wasm_put_request

async def _wasm_worker_loop(worker):
    while True:
        try:
            req = await worker.request_queue.get()
            if req is None:
                break
            topic = req.get('topic')
            if topic == 'send':
                device  = req.get('msg')
                message = req.get('msg2')
                js_ble  = worker._js_ble_registry.get(id(device))
                if js_ble is not None and message is not None:
                    try:
                        await js_ble.send(list(message))
                    except Exception as e:
                        print(f"BLE send error: {e}")
            elif topic == 'connect':
                cb = req.get('msg3')
                if cb: cb(True)
            elif topic == 'disconnect':
                device = req.get('msg')
                js_ble = worker._js_ble_registry.pop(id(device), None)
                if js_ble is not None:
                    js_ble.disconnect()
            elif topic == 'scan':
                cb = req.get('msg2')
                if cb: cb([])
        except Exception as e:
            print(f"Worker loop error: {e}")

# ══════════════════════════════════════════════════════════════
# BLE CONSTANTS
# ══════════════════════════════════════════════════════════════
SERVICE_UUID = '0000fd02-0000-1000-8000-00805f9b34fb'
WRITE_UUID   = '0000fd02-0001-1000-8000-00805f9b34fb'
NOTIFY_UUID  = '0000fd02-0002-1000-8000-00805f9b34fb'

# ══════════════════════════════════════════════════════════════
# PLOTTING FLAG
# ══════════════════════════════════════════════════════════════
_plotting_active = True   # set False when Plots panel is collapsed

# ══════════════════════════════════════════════════════════════
# LEGO DEVICE BASE
# ══════════════════════════════════════════════════════════════
from pyscript.js_modules.ble import BLEDevice as _BLEDeviceJS
from pyodide.ffi import create_proxy

CARD_HTML = """
<div class="device-card" id="card-{uid}">
  <div class="card-header">
    <span class="device-type-label">{label}</span>
    <span class="device-name" id="dname-{uid}"></span>
    <div class="led" id="led-{uid}"></div>
  </div>
  <button class="btn btn-connect" id="btn-{uid}">Connect</button>
  <button class="btn btn-remove"  id="rmv-{uid}" title="Remove">✕</button>
</div>
"""

class LegoDevice:
    label = "Device"

    def __init__(self, uid, container_id, on_remove):
        self.uid        = uid
        self.connected  = False
        self.js_ble     = None
        self._on_remove = on_remove
        self._notification_proxy = None
        self._disconnect_proxy   = None
        self._plot               = None   # DevicePlot instance, set after connect

        container = document.getElementById(container_id)
        wrapper   = document.createElement('div')
        wrapper.innerHTML = CARD_HTML.format(uid=uid, label=self.label)
        container.appendChild(wrapper.firstElementChild)

        document.getElementById(f'btn-{uid}').onclick = create_proxy(self._toggle)
        document.getElementById(f'rmv-{uid}').onclick = create_proxy(self._remove)

    def _set_led(self, color):
        document.getElementById(f'led-{self.uid}').style.backgroundColor = color

    def _set_name(self, name):
        document.getElementById(f'dname-{self.uid}').innerText = name or ''

    def _set_btn(self, text):
        document.getElementById(f'btn-{self.uid}').innerText = text

    async def _toggle(self, event=None):
        if not self.connected:
            await self._connect()
        else:
            self._disconnect()

    async def _connect(self):
        self._set_led('orange')
        self._set_btn('Connecting…')
        try:
            js_ble = _BLEDeviceJS.new()
            self._notification_proxy = create_proxy(
                lambda data: asyncio.ensure_future(
                    self._on_notification(bytes(data.to_py()))
                )
            )
            self._disconnect_proxy = create_proxy(self._on_disconnect)
            js_ble.callback           = self._notification_proxy
            js_ble.disconnectCallback = self._disconnect_proxy

            success = await js_ble.connect(SERVICE_UUID, WRITE_UUID, NOTIFY_UUID)
            if success:
                self.js_ble    = js_ble
                self.connected = True
                self.device    = self
                self._register_js_ble()
                try:
                    self.device_notification_request(100, blocking=False)
                except Exception:
                    pass
                # Create per-device plot
                self._plot = _create_device_plot(self.uid, self._plot_type(), self.label)
                self._set_led('limegreen')
                self._set_name(js_ble.name)
                self._set_btn('Disconnect')
            else:
                raise RuntimeError("connect() returned false")
        except Exception as e:
            print(f"[{self.label}] Connection failed: {e}")
            self._set_led('red')
            self._set_btn('Connect')

    def _disconnect(self):
        if self.js_ble:
            self.js_ble.disconnect()
        self._on_disconnect(None)

    def _on_disconnect(self, event):
        self.connected = False
        self.js_ble    = None
        if self._plot:
            self._plot.destroy()
            self._plot = None
        self._set_led('red')
        self._set_name('')
        self._set_btn('Connect')

    def _remove(self, event=None):
        if self.connected:
            self._disconnect()
        card = document.getElementById(f'card-{self.uid}')
        if card: card.remove()
        self._on_remove(self.uid)

    def send_command(self, packet):
        if self.js_ble is None:
            return
        if isinstance(packet, (bytes, bytearray)):
            packet = list(packet)
        asyncio.ensure_future(self.js_ble.send(packet))

    def _register_js_ble(self):
        import legoeducation.basic_device as bd
        reg = getattr(bd.my_worker, '_js_ble_registry', None)
        if reg is not None:
            reg[id(self.device)] = self.js_ble

    def _plot_type(self):
        return 'unknown'

    async def _on_notification(self, data: bytes):
        pass

    def stop(self):
        pass


# ══════════════════════════════════════════════════════════════
# CONCRETE DEVICE CLASSES
# ══════════════════════════════════════════════════════════════
from double_motor_functions import doubleMotor as _DM
from single_motor_functions import singleMotor as _SM
from color_sensor_functions import colorSensor as _CS
from controller_functions   import controller  as _C

class DoubleMotorDevice(LegoDevice, _DM):
    label = "Double Motor (dm)"
    def __init__(self, uid, container_id, on_remove):
        _DM.__init__(self)
        LegoDevice.__init__(self, uid, container_id, on_remove)
    def _plot_type(self): return 'dm'
    async def _on_notification(self, data):
        await self._device_callback(NOTIFY_UUID, data)
        if _plotting_active and self._plot:
            try:
                self._plot.push_motor(self.motor[0], side_idx=0)
                self._plot.push_motor(self.motor[1], side_idx=1)
            except Exception:
                pass
    def stop(self):
        self.motor_stop(blocking=False)

class SingleMotorDevice(LegoDevice, _SM):
    label = "Single Motor (sm)"
    def __init__(self, uid, container_id, on_remove):
        _SM.__init__(self)
        LegoDevice.__init__(self, uid, container_id, on_remove)
    def _plot_type(self): return 'sm'
    async def _on_notification(self, data):
        await self._device_callback(NOTIFY_UUID, data)
        if _plotting_active and self._plot:
            try:
                self._plot.push_motor(self.motor, side_idx=None)
            except Exception:
                pass
    def stop(self):
        self.motor_stop(blocking=False)

class ColorSensorDevice(LegoDevice, _CS):
    label = "Color Sensor (cs)"
    def __init__(self, uid, container_id, on_remove):
        _CS.__init__(self)
        LegoDevice.__init__(self, uid, container_id, on_remove)
    def _plot_type(self): return 'cs'
    async def _on_notification(self, data):
        await self._device_callback(NOTIFY_UUID, data)
        if _plotting_active and self._plot:
            try:
                self._plot.push_color_sensor(self.sensor)
            except Exception:
                pass
    def stop(self):
        pass

class ControllerDevice(LegoDevice, _C):
    label = "Controller (c)"
    def __init__(self, uid, container_id, on_remove):
        _C.__init__(self)
        LegoDevice.__init__(self, uid, container_id, on_remove)
    def _plot_type(self): return 'c'
    async def _on_notification(self, data):
        await self._device_callback(NOTIFY_UUID, data)
        if _plotting_active and self._plot:
            try:
                self._plot.push_controller(self.sensor)
            except Exception:
                pass
    def stop(self):
        pass

DEVICE_TYPES = {
    'dm': DoubleMotorDevice,
    'sm': SingleMotorDevice,
    'cs': ColorSensorDevice,
    'c' : ControllerDevice,
}

# ══════════════════════════════════════════════════════════════
# PLOT MANAGEMENT
# ══════════════════════════════════════════════════════════════
from plot import DevicePlot, _plot_registry

def _create_device_plot(uid, device_type, device_label):
    """Create and register a DevicePlot for a newly connected device."""
    plot = DevicePlot(uid, device_type, device_label)
    _plot_registry[uid] = plot
    return plot

# ══════════════════════════════════════════════════════════════
# DEVICE REGISTRY
# ══════════════════════════════════════════════════════════════
_devices: dict = {}
_uid_counter   = 0

def _next_uid():
    global _uid_counter
    _uid_counter += 1
    return str(_uid_counter)

def _on_remove(uid):
    _devices.pop(uid, None)
    _plot_registry.pop(uid, None)

def add_device(event=None):
    sel   = document.getElementById('device-type-select')
    dtype = sel.value
    if dtype not in DEVICE_TYPES:
        return
    uid = _next_uid()
    dev = DEVICE_TYPES[dtype](uid=uid, container_id='device-container', on_remove=_on_remove)
    _devices[uid] = dev

document.getElementById('add-device-btn').onclick = create_proxy(add_device)

# ══════════════════════════════════════════════════════════════
# TERMINAL OUTPUT
# ══════════════════════════════════════════════════════════════
class _WebTerminal:
    def __init__(self):
        self._buf = ''

    def write(self, text):
        self._buf += text
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            if line:
                terminal = document.getElementById('terminal')
                div = document.createElement('div')
                div.innerText = line
                terminal.appendChild(div)
                terminal.scrollTop = terminal.scrollHeight

    def flush(self):
        if self._buf.strip():
            terminal = document.getElementById('terminal')
            div = document.createElement('div')
            div.innerText = self._buf
            terminal.appendChild(div)
            terminal.scrollTop = terminal.scrollHeight
            self._buf = ''

def _terminal_print(msg, color=None):
    terminal = document.getElementById('terminal')
    div = document.createElement('div')
    div.innerText = msg
    if color:
        div.style.color = color
    terminal.appendChild(div)
    terminal.scrollTop = terminal.scrollHeight

# ══════════════════════════════════════════════════════════════
# AST AWAIT INJECTOR
# ══════════════════════════════════════════════════════════════
import inspect

async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value

class _AwaitInjector(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            wrapped = ast.Call(
                func=ast.Name(id='_maybe_await', ctx=ast.Load()),
                args=[node.value],
                keywords=[],
            )
            node.value = ast.Await(value=wrapped)
            ast.fix_missing_locations(node)
        return node

def _inject_awaits(source: str) -> ast.AST:
    tree = ast.parse(source)
    tree = _AwaitInjector().visit(tree)
    ast.fix_missing_locations(tree)
    return tree

# ══════════════════════════════════════════════════════════════
# RUN / STOP
# ══════════════════════════════════════════════════════════════
_running_task = None

def _stop_all_devices():
    for dev in _devices.values():
        if dev.connected:
            try:
                dev.stop()
            except Exception as e:
                print(f"Stop error on {dev.label}: {e}")

def _build_sandbox():
    latest = {}
    for dev in _devices.values():
        for key, cls in DEVICE_TYPES.items():
            if isinstance(dev, cls):
                latest[key] = dev
    return {
        'dm': latest.get('dm'),
        'sm': latest.get('sm'),
        'cs': latest.get('cs'),
        'c' : latest.get('c'),
        'wait':         wait,
        'print':        print,
        '_maybe_await': _maybe_await,
        'azure':   le.LEGO_COLOR_AZURE,
        'blue':    le.LEGO_COLOR_BLUE,
        'green':   le.LEGO_COLOR_GREEN,
        'red':     le.LEGO_COLOR_RED,
        'yellow':  le.LEGO_COLOR_YELLOW,
        'white':   le.LEGO_COLOR_WHITE,
        'orange':  le.LEGO_COLOR_ORANGE,
        'purple':  le.LEGO_COLOR_PURPLE,
        'magenta': le.LEGO_COLOR_MAGENTA,
    }

async def execute_user_code(event=None):
    global _running_task

    if _running_task is not None and not _running_task.done():
        _running_task.cancel()
        try:
            await _running_task
        except (asyncio.CancelledError, Exception):
            pass
        _stop_all_devices()
        _running_task = None

    document.getElementById('terminal').innerHTML = ''
    raw_code = window.cmEditor.state.doc.toString()

    terminal = _WebTerminal()

    def _student_print(*args, sep=' ', end='\n', **kwargs):
        terminal.write(sep.join(str(a) for a in args) + end)
        terminal.flush()

    old_stdout = sys.stdout
    sys.stdout = terminal

    sandbox = _build_sandbox()
    sandbox['print'] = _student_print

    warnings = []
    if 'dm' in raw_code and sandbox.get('dm') is None:
        warnings.append("⚠ dm (Double Motor) is not connected — add and connect it first")
    if 'sm' in raw_code and sandbox.get('sm') is None:
        warnings.append("⚠ sm (Single Motor) is not connected — add and connect it first")
    if 'cs' in raw_code and sandbox.get('cs') is None:
        warnings.append("⚠ cs (Color Sensor) is not connected — add and connect it first")
    if 'c.' in raw_code and sandbox.get('c') is None:
        warnings.append("⚠ c (Controller) is not connected — add and connect it first")
    if warnings:
        for w in warnings:
            _student_print(w)
        sys.stdout = old_stdout
        return

    try:
        tree = _inject_awaits(raw_code)
    except SyntaxError as e:
        _student_print(f"Syntax Error: {e}")
        sys.stdout = old_stdout
        return

    async_func = ast.AsyncFunctionDef(
        name='__user_program',
        args=ast.arguments(
            posonlyargs=[], args=[], vararg=None,
            kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
        ),
        body=tree.body if tree.body else [ast.Pass()],
        decorator_list=[],
        returns=None,
    )
    wrapper_module = ast.Module(body=[async_func], type_ignores=[])
    ast.fix_missing_locations(wrapper_module)
    code_obj = compile(wrapper_module, filename='<student>', mode='exec')
    exec(code_obj, sandbox)

    async def _run_and_report():
        try:
            await sandbox['__user_program']()
            _terminal_print('✓ Program finished.', color='#6B7280')
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _terminal_print(f'Runtime Error: {err}', color='#F87171')
        finally:
            sys.stdout = old_stdout

    _running_task = asyncio.ensure_future(_run_and_report())


def stop_user_code(event=None):
    global _running_task
    if _running_task is not None and not _running_task.done():
        _running_task.cancel()
    _running_task = None
    _stop_all_devices()
    _terminal_print('⏹ Stopped.', color='#F97316')


# ══════════════════════════════════════════════════════════════
# AI TUTOR BRIDGE
# ══════════════════════════════════════════════════════════════
def send_to_tutor(event=None):
    """Read the student's message + editor code and call window.sendToTutor."""
    input_el = document.getElementById('chat-input')
    msg = input_el.value.strip()
    if not msg:
        return
    input_el.value = ''
    code = window.cmEditor.state.doc.toString()
    window.sendToTutor(msg, code)


document.getElementById('chat-send-btn').onclick = create_proxy(send_to_tutor)

# Allow Enter (without Shift) to send
def _chat_keydown(event):
    if event.key == 'Enter' and not event.shiftKey:
        event.preventDefault()
        send_to_tutor()

document.getElementById('chat-input').onkeydown = create_proxy(_chat_keydown)

# ══════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════
async def wait(seconds: float):
    await asyncio.sleep(seconds)