// LEGO CS+AI kit — Web Bluetooth layer
// Service: 0000FD02-0000-1000-8000-00805F9B34FB (LEGO Education proprietary RPC)
// Protocol reverse-engineered from legoeducation Python library (rpc_message.py / basic_ble.py)

const SERVICE_UUID = '0000fd02-0000-1000-8000-00805f9b34fb';
const WRITE_UUID   = '0000fd02-0001-1000-8000-00805f9b34fb'; // computer → hub
const NOTIFY_UUID  = '0000fd02-0002-1000-8000-00805f9b34fb'; // hub → computer

// RPC message type IDs (from rpc_message.py)
const INFO_REQUEST                      = 0;
const DEVICE_NOTIFICATION_REQUEST       = 40;
const DEVICE_NOTIFICATION               = 60;
const MOTOR_RUN_COMMAND                 = 122;
const MOTOR_RUN_FOR_DEGREES_COMMAND     = 124;
const MOTOR_RUN_FOR_TIME_COMMAND        = 126;
const MOTOR_STOP_COMMAND                = 138;
const MOTOR_SET_SPEED_COMMAND           = 140;
const MOVEMENT_MOVE_COMMAND             = 150;
const MOVEMENT_MOVE_FOR_TIME_COMMAND    = 152;
const MOVEMENT_MOVE_FOR_DEGREES_COMMAND = 154;
const MOVEMENT_TURN_FOR_DEGREES_COMMAND = 160;
const MOVEMENT_STOP_COMMAND             = 168;
const MOVEMENT_SET_SPEED_COMMAND        = 170;

// Inner notification sub-types (carried inside DEVICE_NOTIFICATION payload)
const MOTOR_NOTIFICATION        = 10; // B motorBitMask, B motorState, H absPos, h power, b speed, l position, b gesture → 12 bytes
const COLOR_SENSOR_NOTIFICATION = 12; // b color, B reflection, 4×H (rawRGB+hue), B sat, B val → 12 bytes
const CONTROLLER_NOTIFICATION   = 15; // b leftPct, b rightPct, h leftAngle, h rightAngle → 6 bytes

const MOTOR_STATE_READY = 0; // motorState value meaning "done"

// Motor bit masks
const MOTOR_BITS_LEFT  = 1;
const MOTOR_BITS_RIGHT = 2;
const MOTOR_BITS_BOTH  = 3;

// ── state ──────────────────────────────────────────────────────────────────────

let _device = null;
let _rx     = null;   // WRITE characteristic
let _pending = null;  // one pending operation at a time

let _lastColorVal    = -1;
let _ctrlLeft        = 0;
let _ctrlRight       = 0;

window._legoConnected = false;
window._lastColor     = -1;

// ── binary helpers ────────────────────────────────────────────────────────────

function _i8(n) {
  n = Math.max(-128, Math.min(127, Math.round(n)));
  return n < 0 ? n + 256 : n;
}

function _i32LE(n) {
  const v = new DataView(new ArrayBuffer(4));
  v.setInt32(0, Math.round(n), true);
  return [...new Uint8Array(v.buffer)];
}

function _u32LE(n) {
  const v = new DataView(new ArrayBuffer(4));
  v.setUint32(0, Math.max(0, Math.round(n)), true);
  return [...new Uint8Array(v.buffer)];
}

function _u16LE(n) {
  n = Math.max(0, Math.round(n));
  return [n & 0xFF, (n >> 8) & 0xFF];
}

// ── UI ─────────────────────────────────────────────────────────────────────────

function _updateConnectBtn(connected) {
  const btn = document.getElementById('connect-btn');
  if (!btn) return;
  btn.textContent = connected ? '● Connected' : '○ Connect to LEGO';
  btn.style.background = connected ? '#50fa7b' : '#bd93f9';
  btn.style.color      = connected ? '#1e1f29' : '#f8f8f2';
}

// ── connection ────────────────────────────────────────────────────────────────

async function legoConnect() {
  if (!navigator.bluetooth) {
    throw new Error('Web Bluetooth not available — use Chrome or Edge');
  }
  if (_device?.gatt?.connected) return;

  _device = await navigator.bluetooth.requestDevice({
    filters: [{ services: [SERVICE_UUID] }]
  });

  _device.addEventListener('gattserverdisconnected', () => {
    _device = null; _rx = null;
    window._legoConnected = false;
    _updateConnectBtn(false);
    if (_pending) { _pending.reject(new Error('Device disconnected')); _pending = null; }
  });

  const server  = await _device.gatt.connect();
  const service = await server.getPrimaryService(SERVICE_UUID);
  _rx = await service.getCharacteristic(WRITE_UUID);
  const tx = await service.getCharacteristic(NOTIFY_UUID);

  await tx.startNotifications();
  tx.addEventListener('characteristicvaluechanged', _onNotify);

  // Wake hub + start 50 ms periodic device notifications (gives motor-ready events)
  await _rx.writeValueWithoutResponse(new Uint8Array([INFO_REQUEST]));
  await _rx.writeValueWithoutResponse(new Uint8Array([DEVICE_NOTIFICATION_REQUEST, ..._u16LE(50)]));

  window._legoConnected = true;
  _updateConnectBtn(true);
}

async function legoDisconnect() {
  if (_device?.gatt?.connected) _device.gatt.disconnect();
  _device = null; _rx = null;
  window._legoConnected = false;
  _updateConnectBtn(false);
}

// ── notification parser ───────────────────────────────────────────────────────

function _onNotify(evt) {
  const d  = new Uint8Array(evt.target.value.buffer);
  const dv = new DataView(evt.target.value.buffer);
  if (!d.length) return;

  const msgType = d[0];

  // ACK (result) for a sent command — result type is always command type + 1
  if (_pending && !_pending.waitMotor && _pending.ackType === msgType) {
    clearTimeout(_pending.timer);
    const p = _pending; _pending = null;
    p.resolve(d);
    return;
  }

  // DEVICE_NOTIFICATION (60): carries a sequence of inner sub-notifications
  if (msgType !== DEVICE_NOTIFICATION || d.length < 3) return;

  let innerLen = d[1] | (d[2] << 8);
  let offset   = 3;

  while (innerLen > 0 && offset < d.length) {
    const innerType = d[offset];
    offset   += 1;
    innerLen -= 1;

    if (innerType === MOTOR_NOTIFICATION && offset + 12 <= d.length) {
      // B motorBitMask, B motorState, H absPos, h power, b speed, l position, b gesture
      const motorBitMask = d[offset];
      const motorState   = d[offset + 1];
      if (_pending?.waitMotor &&
          motorState === MOTOR_STATE_READY &&
          (motorBitMask & _pending.motorMask) !== 0) {
        clearTimeout(_pending.timer);
        const p = _pending; _pending = null;
        p.resolve(d);
      }
      offset   += 12;
      innerLen -= 12;

    } else if (innerType === COLOR_SENSOR_NOTIFICATION && offset + 12 <= d.length) {
      // b color (signed: -1=none, 0-10=index), B reflection, 4×H, B, B
      _lastColorVal     = dv.getInt8(offset);
      window._lastColor = _lastColorVal;
      offset   += 12;
      innerLen -= 12;

    } else if (innerType === CONTROLLER_NOTIFICATION && offset + 6 <= d.length) {
      // b leftPct, b rightPct, h leftAngle, h rightAngle
      _ctrlLeft  = dv.getInt8(offset);
      _ctrlRight = dv.getInt8(offset + 1);
      offset   += 6;
      innerLen -= 6;

    } else {
      break; // unknown inner type — stop parsing
    }
  }
}

// ── write helpers ─────────────────────────────────────────────────────────────

function _requireConn() {
  if (!_rx) throw new Error('Not connected. Click "○ Connect to LEGO" before running hardware code.');
}

async function _send(bytes) {
  _requireConn();
  await _rx.writeValueWithoutResponse(new Uint8Array(bytes));
}

// Send and wait for ACK (result type = command type + 1)
async function _sendAwait(bytes, timeoutMs = 5000) {
  _requireConn();
  const ackType = bytes[0] + 1;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      if (_pending?.ackType === ackType) _pending = null;
      resolve(null); // timeout is non-fatal
    }, timeoutMs);
    _pending = { ackType, motorMask: 0, waitMotor: false, resolve, reject, timer };
    _rx.writeValueWithoutResponse(new Uint8Array(bytes)).catch(err => {
      clearTimeout(timer); _pending = null; reject(err);
    });
  });
}

// Send a motor command that blocks until the hub sends MOTOR_STATE_READY
async function _sendBlock(bytes, motorMask, timeoutMs = 30000) {
  await _sendAwait(bytes); // wait for ACK (~100 ms)
  return new Promise(resolve => {
    const timer = setTimeout(() => {
      if (_pending?.waitMotor) _pending = null;
      resolve(null);
    }, timeoutMs);
    _pending = { ackType: -1, motorMask, waitMotor: true, resolve, reject: resolve, timer };
  });
}

// ── individual motor commands ─────────────────────────────────────────────────

async function motorSetSpeed(motorBitMask, speed) {
  speed = Math.max(-100, Math.min(100, Math.round(speed)));
  await _send([MOTOR_SET_SPEED_COMMAND, motorBitMask, _i8(speed)]);
}

async function motorRun(motorBitMask, direction) {
  // direction: 0=clockwise, 1=counterclockwise
  await _send([MOTOR_RUN_COMMAND, motorBitMask, direction]);
}

async function motorRunForDegrees(motorBitMask, degrees, direction) {
  await _sendBlock(
    [MOTOR_RUN_FOR_DEGREES_COMMAND, motorBitMask, ..._i32LE(Math.abs(degrees)), direction],
    motorBitMask
  );
}

async function motorRunForTime(motorBitMask, timeMs, direction) {
  await _sendBlock(
    [MOTOR_RUN_FOR_TIME_COMMAND, motorBitMask, ..._u32LE(timeMs), direction],
    motorBitMask,
    timeMs + 5000
  );
}

async function motorStop(motorBitMask) {
  await _send([MOTOR_STOP_COMMAND, motorBitMask]);
}

// ── coordinated movement commands (DoubleMotor) ───────────────────────────────

async function movementSetSpeed(speed) {
  speed = Math.max(-100, Math.min(100, Math.round(speed)));
  await _send([MOVEMENT_SET_SPEED_COMMAND, _i8(speed)]);
}

async function movementMove(direction) {
  // direction: 0=forward, 1=backward (1 makes the car go "forward" per hw mounting)
  await _send([MOVEMENT_MOVE_COMMAND, direction]);
}

// degrees is signed int32; negative reverses within the given direction
async function movementMoveForDegrees(degrees, direction) {
  await _sendBlock(
    [MOVEMENT_MOVE_FOR_DEGREES_COMMAND, ..._i32LE(degrees), direction],
    MOTOR_BITS_BOTH
  );
}

async function movementMoveForTime(timeMs, direction) {
  await _sendBlock(
    [MOVEMENT_MOVE_FOR_TIME_COMMAND, ..._u32LE(timeMs), direction],
    MOTOR_BITS_BOTH,
    timeMs + 5000
  );
}

async function movementStop() {
  await _send([MOVEMENT_STOP_COMMAND]);
}

async function movementTurnForDegrees(degrees, direction) {
  // direction: 2=left, 3=right
  await _sendBlock(
    [MOVEMENT_TURN_FOR_DEGREES_COMMAND, ..._i32LE(Math.abs(degrees)), direction],
    MOTOR_BITS_BOTH
  );
}

// ── sensor / controller readers ───────────────────────────────────────────────

function getLastColor()      { return window._lastColor; }
function getControllerLeft() { return _ctrlLeft; }
function getControllerRight(){ return _ctrlRight; }

// ── exports ───────────────────────────────────────────────────────────────────

Object.assign(window, {
  legoConnect, legoDisconnect,
  motorSetSpeed, motorRun, motorRunForDegrees, motorRunForTime, motorStop,
  movementSetSpeed, movementMove, movementMoveForDegrees,
  movementMoveForTime, movementStop, movementTurnForDegrees,
  getLastColor, getControllerLeft, getControllerRight,
});
