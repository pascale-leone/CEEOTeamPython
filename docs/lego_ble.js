// LEGO CS+AI kit — Web Bluetooth layer (multi-device)
// Each card (double motor, single motor, color sensor, controller) is its own BLE device.
// Click "Connect" once per card. Device type is auto-detected from INFO_RESPONSE.
// Protocol reverse-engineered from legoeducation Python library (rpc_message.py / basic_ble.py)

const SERVICE_UUID = '0000fd02-0000-1000-8000-00805f9b34fb';
const WRITE_UUID   = '0000fd02-0001-1000-8000-00805f9b34fb';
const NOTIFY_UUID  = '0000fd02-0002-1000-8000-00805f9b34fb';

// RPC message type IDs
const INFO_REQUEST                      = 0;
const INFO_RESPONSE                     = 1;
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

// Inner notification sub-types inside DEVICE_NOTIFICATION
const MOTOR_NOTIFICATION        = 10;
const COLOR_SENSOR_NOTIFICATION = 12;
const CONTROLLER_NOTIFICATION   = 15;

const MOTOR_STATE_READY = 0;

const MOTOR_BITS_LEFT  = 1;
const MOTOR_BITS_RIGHT = 2;
const MOTOR_BITS_BOTH  = 3;

// productGroupDevice values from rpc_message.py
const PGD_SINGLE_MOTOR = 512;
const PGD_DOUBLE_MOTOR = 513;
const PGD_COLOR_SENSOR = 514;
const PGD_CONTROLLER   = 515;

const _PGD_TO_TYPE = {
  512: 'singleMotor',
  513: 'doubleMotor',
  514: 'colorSensor',
  515: 'controller',
};

// ── per-device connection table ───────────────────────────────────────────────
// Each slot holds a device-state object or null.

const _conn = {
  singleMotor: null,
  doubleMotor: null,
  colorSensor: null,
  controller:  null,
};

function _makeDevState(rx, bleDevice) {
  return {
    rx,
    bleDevice,
    pending:     null,   // { ackType, resolve, reject, timer }
    infoResolve: null,   // used once during connect to capture INFO_RESPONSE
    lastColor:   -1,
    ctrlLeft:    0,
    ctrlRight:   0,
  };
}

// ── binary helpers ─────────────────────────────────────────────────────────────

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

function _updateConnectUI() {
  const btn = document.getElementById('connect-btn');
  if (!btn) return;
  const labels = [];
  if (_conn.doubleMotor) labels.push('Motor ●');
  if (_conn.singleMotor) labels.push('Single ●');
  if (_conn.colorSensor) labels.push('Sensor ●');
  if (_conn.controller)  labels.push('Controller ●');
  if (labels.length === 0) {
    btn.textContent = '○ Connect to LEGO';
    btn.style.background = '#bd93f9';
    btn.style.color = '#f8f8f2';
  } else {
    btn.textContent = '+ Connect  |  ' + labels.join('  ');
    btn.style.background = '#50fa7b';
    btn.style.color = '#1e1f29';
  }
  window._legoConnected = !!(
    _conn.doubleMotor || _conn.singleMotor || _conn.colorSensor || _conn.controller
  );
}

// ── notification handler (one per connected device) ───────────────────────────

function _makeNotifyHandler(dev) {
  return function(evt) {
    const d  = new Uint8Array(evt.target.value.buffer);
    const dv = new DataView(evt.target.value.buffer);
    if (!d.length) return;
    const msgType = d[0];

    // INFO_RESPONSE (type 1) — 17 bytes: [1, rpcMaj, rpcMin, rpcBuild(2), fwMaj, fwMin,
    //   fwBuild(2), blMaj, blMin, blBuild(2), maxPktSize(2), productGroupDevice(2)]
    if (msgType === INFO_RESPONSE && dev.infoResolve) {
      dev.infoResolve(d);
      dev.infoResolve = null;
      return;
    }

    // ACK (result) for a pending command — result type = command type + 1.
    // For *_FOR_DEGREES / *_FOR_TIME commands, the hub delays this ACK until the
    // motor has actually finished moving — confirmed against the official
    // legoeducation Python package's _send_commands(), which also blocks only on
    // this same ACK and has no separate "wait for motor ready notification" step.
    // (We used to *also* wait here for a MOTOR_NOTIFICATION with motorState===READY,
    // which could sit at its 30s timeout on real hardware whose settled end-state
    // isn't exactly MOTOR_STATE_READY — that extra wait was unnecessary and buggy;
    // the ACK alone is already the completion signal.)
    if (dev.pending && dev.pending.ackType === msgType) {
      clearTimeout(dev.pending.timer);
      const p = dev.pending; dev.pending = null;
      p.resolve(d);
      return;
    }

    if (msgType !== DEVICE_NOTIFICATION || d.length < 3) return;

    let innerLen = d[1] | (d[2] << 8);
    let offset   = 3;

    while (innerLen > 0 && offset < d.length) {
      const innerType = d[offset];
      offset   += 1;
      innerLen -= 1;

      if (innerType === MOTOR_NOTIFICATION && offset + 12 <= d.length) {
        offset   += 12; innerLen -= 12;

      } else if (innerType === COLOR_SENSOR_NOTIFICATION && offset + 12 <= d.length) {
        dev.lastColor     = dv.getInt8(offset);
        window._lastColor = dev.lastColor;
        offset   += 12; innerLen -= 12;

      } else if (innerType === CONTROLLER_NOTIFICATION && offset + 6 <= d.length) {
        dev.ctrlLeft  = dv.getInt8(offset);
        dev.ctrlRight = dv.getInt8(offset + 1);
        offset   += 6; innerLen -= 6;

      } else {
        break;
      }
    }
  };
}

// ── connection ─────────────────────────────────────────────────────────────────
// Must be called from a user gesture (button click). Detects device type automatically.

async function legoConnect() {
  if (!navigator.bluetooth) {
    throw new Error('Web Bluetooth not available — use Chrome or Edge');
  }

  const bleDevice = await navigator.bluetooth.requestDevice({
    filters: [{ services: [SERVICE_UUID] }]
  });

  const server  = await bleDevice.gatt.connect();
  const service = await server.getPrimaryService(SERVICE_UUID);
  const rx = await service.getCharacteristic(WRITE_UUID);
  const tx = await service.getCharacteristic(NOTIFY_UUID);

  const dev = _makeDevState(rx, bleDevice);

  await tx.startNotifications();
  tx.addEventListener('characteristicvaluechanged', _makeNotifyHandler(dev));

  // Send INFO_REQUEST and wait for INFO_RESPONSE to learn the device type
  const infoPromise = new Promise(resolve => {
    dev.infoResolve = resolve;
    setTimeout(() => { dev.infoResolve = null; resolve(null); }, 3000);
  });
  await rx.writeValueWithoutResponse(new Uint8Array([INFO_REQUEST]));
  const infoData = await infoPromise;

  // productGroupDevice is at bytes 15-16 (little-endian uint16) in INFO_RESPONSE
  let deviceType = 'unknown';
  if (infoData && infoData.length >= 17) {
    const pgd = infoData[15] | (infoData[16] << 8);
    deviceType = _PGD_TO_TYPE[pgd] || 'unknown';
  }

  // Replace any prior connection of the same type
  if (_conn[deviceType]?._device?.gatt?.connected) {
    _conn[deviceType].bleDevice.gatt.disconnect();
  }
  if (deviceType !== 'unknown') {
    _conn[deviceType] = dev;
  }

  bleDevice.addEventListener('gattserverdisconnected', () => {
    for (const [type, d] of Object.entries(_conn)) {
      if (d === dev) {
        _conn[type] = null;
        if (d.pending) { d.pending.reject(new Error('Device disconnected')); d.pending = null; }
      }
    }
    _updateConnectUI();
  });

  // Start 50 ms periodic device notifications
  await rx.writeValueWithoutResponse(new Uint8Array([DEVICE_NOTIFICATION_REQUEST, ..._u16LE(50)]));

  _updateConnectUI();
  return deviceType;
}

async function legoDisconnect() {
  for (const [type, dev] of Object.entries(_conn)) {
    if (dev?.bleDevice?.gatt?.connected) dev.bleDevice.gatt.disconnect();
    _conn[type] = null;
  }
  _updateConnectUI();
}

// ── write helpers ──────────────────────────────────────────────────────────────

function _getConn(type) {
  const dev = _conn[type];
  if (!dev) {
    const label = { doubleMotor: 'Double motor', singleMotor: 'Single motor',
                    colorSensor: 'Color sensor', controller: 'Controller' }[type] || type;
    throw new Error(`${label} not connected — click "Connect to LEGO" and select the ${label.toLowerCase()} card`);
  }
  return dev;
}

async function _sendTo(dev, bytes) {
  await dev.rx.writeValueWithoutResponse(new Uint8Array(bytes));
}

async function _sendAwaitOn(dev, bytes, timeoutMs = 5000) {
  const ackType = bytes[0] + 1;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      if (dev.pending?.ackType === ackType) dev.pending = null;
      resolve(null);
    }, timeoutMs);
    dev.pending = { ackType, resolve, reject, timer };
    dev.rx.writeValueWithoutResponse(new Uint8Array(bytes)).catch(err => {
      clearTimeout(timer); dev.pending = null; reject(err);
    });
  });
}

// ── individual motor commands (doubleMotor card) ───────────────────────────────

async function motorSetSpeed(motorBitMask, speed) {
  const dev = _getConn('doubleMotor');
  speed = Math.max(-100, Math.min(100, Math.round(speed)));
  await _sendTo(dev, [MOTOR_SET_SPEED_COMMAND, motorBitMask, _i8(speed)]);
}

async function motorRun(motorBitMask, direction) {
  await _sendTo(_getConn('doubleMotor'), [MOTOR_RUN_COMMAND, motorBitMask, direction]);
}

async function motorRunForDegrees(motorBitMask, degrees, direction) {
  const dev = _getConn('doubleMotor');
  // The ACK for this command is delayed by the hub until the motor stops moving,
  // so a generous timeout is just a safety ceiling, not the expected wait time.
  await _sendAwaitOn(dev, [MOTOR_RUN_FOR_DEGREES_COMMAND, motorBitMask, ..._i32LE(Math.abs(degrees)), direction], 30000);
}

async function motorRunForTime(motorBitMask, timeMs, direction) {
  const dev = _getConn('doubleMotor');
  await _sendAwaitOn(dev, [MOTOR_RUN_FOR_TIME_COMMAND, motorBitMask, ..._u32LE(timeMs), direction], timeMs + 5000);
}

async function motorStop(motorBitMask) {
  await _sendTo(_getConn('doubleMotor'), [MOTOR_STOP_COMMAND, motorBitMask]);
}

// ── coordinated movement commands (doubleMotor card) ──────────────────────────

async function movementSetSpeed(speed) {
  const dev = _getConn('doubleMotor');
  speed = Math.max(-100, Math.min(100, Math.round(speed)));
  await _sendTo(dev, [MOVEMENT_SET_SPEED_COMMAND, _i8(speed)]);
}

async function movementMove(direction) {
  await _sendTo(_getConn('doubleMotor'), [MOVEMENT_MOVE_COMMAND, direction]);
}

async function movementMoveForDegrees(degrees, direction) {
  const dev = _getConn('doubleMotor');
  await _sendAwaitOn(dev, [MOVEMENT_MOVE_FOR_DEGREES_COMMAND, ..._i32LE(degrees), direction], 30000);
}

async function movementMoveForTime(timeMs, direction) {
  const dev = _getConn('doubleMotor');
  await _sendAwaitOn(dev, [MOVEMENT_MOVE_FOR_TIME_COMMAND, ..._u32LE(timeMs), direction], timeMs + 5000);
}

async function movementStop() {
  await _sendTo(_getConn('doubleMotor'), [MOVEMENT_STOP_COMMAND]);
}

async function movementTurnForDegrees(degrees, direction) {
  const dev = _getConn('doubleMotor');
  await _sendAwaitOn(dev, [MOVEMENT_TURN_FOR_DEGREES_COMMAND, ..._i32LE(Math.abs(degrees)), direction], 30000);
}

// ── sensor / controller readers ───────────────────────────────────────────────

function getLastColor()       { return _conn.colorSensor?.lastColor ?? -1; }
function getControllerLeft()  { return _conn.controller?.ctrlLeft ?? 0; }
function getControllerRight() { return _conn.controller?.ctrlRight ?? 0; }

// ── cancel any in-flight blocking command ─────────────────────────────────────
// Resolves pending promises immediately so Python gets control back from await.

function legoCancelPending() {
  for (const dev of Object.values(_conn)) {
    if (dev?.pending) {
      clearTimeout(dev.pending.timer);
      const p = dev.pending;
      dev.pending = null;
      p.resolve(null);
    }
  }
}

// ── stop all motors on all connected devices ───────────────────────────────────

async function legoStopAll() {
  legoCancelPending();
  const tasks = [];
  if (_conn.doubleMotor) {
    tasks.push(_sendTo(_conn.doubleMotor, [MOVEMENT_STOP_COMMAND]).catch(() => {}));
    tasks.push(_sendTo(_conn.doubleMotor, [MOTOR_STOP_COMMAND, MOTOR_BITS_BOTH]).catch(() => {}));
  }
  if (_conn.singleMotor) {
    tasks.push(_sendTo(_conn.singleMotor, [MOTOR_STOP_COMMAND, MOTOR_BITS_LEFT]).catch(() => {}));
  }
  await Promise.all(tasks);
}

// ── exports ───────────────────────────────────────────────────────────────────

Object.assign(window, {
  legoConnect, legoDisconnect, legoStopAll,
  motorSetSpeed, motorRun, motorRunForDegrees, motorRunForTime, motorStop,
  movementSetSpeed, movementMove, movementMoveForDegrees,
  movementMoveForTime, movementStop, movementTurnForDegrees,
  getLastColor, getControllerLeft, getControllerRight,
});
