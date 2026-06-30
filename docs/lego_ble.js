// LEGO Wireless Protocol 3.0 (LWP3) over Web Bluetooth
// Connects to LEGO SPIKE Prime hubs in Chrome / Edge

const SERVICE_UUID = '00001623-1212-efde-1623-785feabcd123';
const CHAR_RX_UUID = '00001624-1212-efde-1623-785feabcd123'; // computer → hub
const CHAR_TX_UUID = '00001625-1212-efde-1623-785feabcd123'; // hub → computer (notifications)

let _device = null, _rx = null;
window._legoConnected = false;
window._lastColor = 0;

// ── connection ───────────────────────────────────────────────────────────────

async function legoConnect() {
  if (!navigator.bluetooth) {
    throw new Error('Web Bluetooth not available — please use Chrome or Edge');
  }
  _device = await navigator.bluetooth.requestDevice({
    acceptAllDevices: true,
    optionalServices: [SERVICE_UUID]
  });
  _device.addEventListener('gattserverdisconnected', () => {
    window._legoConnected = false;
    _rx = null;
    _updateConnectBtn(false);
  });
  const server  = await _device.gatt.connect();
  const service = await server.getPrimaryService(SERVICE_UUID);
  _rx = await service.getCharacteristic(CHAR_RX_UUID);
  const tx = await service.getCharacteristic(CHAR_TX_UUID);
  await tx.startNotifications();
  tx.addEventListener('characteristicvaluechanged', _onNotify);
  window._legoConnected = true;
  _updateConnectBtn(true);
}

async function legoDisconnect() {
  if (_device?.gatt?.connected) _device.gatt.disconnect();
  window._legoConnected = false;
  _rx = null;
  _updateConnectBtn(false);
}

function _onNotify(evt) {
  const d = new Uint8Array(evt.target.value.buffer);
  // Port Value Single (0x45): byte 4 holds sensor value
  if (d[2] === 0x45) window._lastColor = d[4];
}

function _updateConnectBtn(connected) {
  const btn = document.getElementById('connect-btn');
  if (!btn) return;
  btn.textContent = connected ? '● Connected' : '○ Connect to LEGO';
  btn.style.background = connected ? '#50fa7b' : '#bd93f9';
}

// ── low-level write ──────────────────────────────────────────────────────────

async function _write(bytes) {
  if (!_rx) throw new Error('Not connected — click "Connect to LEGO" before running hardware code');
  await _rx.writeValueWithoutResponse(new Uint8Array(bytes));
}

function _i32(n) {
  n = Math.round(n);
  return [n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF, (n >> 24) & 0xFF];
}

// LWP3 Port Output Command
// Format: [len, hubId=0, msgType=0x81, port, startupCompletion=0x11, subCmd, ...params]
async function _portOut(port, subCmd, params) {
  const len = 6 + params.length;
  return _write([len, 0x00, 0x81, port, 0x11, subCmd, ...params]);
}

// ── motor commands ───────────────────────────────────────────────────────────

// SubCmd 0x0B — RunForDegrees
async function motorRunForDegrees(port, degrees, speed) {
  speed   = Math.round(Math.max(-100, Math.min(100, speed ?? 50)));
  degrees = Math.abs(Math.round(degrees));
  // params: degrees(int32 LE), speed(int8), maxPower, endState(0x7E=brake), useProfile
  return _portOut(port, 0x0B, [..._i32(degrees), speed & 0xFF, 100, 0x7E, 0x00]);
}

// SubCmd 0x01 — StartSpeed (run continuously)
async function motorRun(port, speed) {
  speed = Math.round(Math.max(-100, Math.min(100, speed ?? 50)));
  // params: speed(int8), maxPower, useProfile
  return _portOut(port, 0x01, [speed & 0xFF, 100, 0x00]);
}

// SubCmd 0x09 — RunForTime
async function motorRunTime(port, ms, speed) {
  speed = Math.round(Math.max(-100, Math.min(100, speed ?? 50)));
  ms    = Math.round(ms);
  // params: time(uint16 LE), speed(int8), maxPower, endState, useProfile
  return _portOut(port, 0x09, [ms & 0xFF, (ms >> 8) & 0xFF, speed & 0xFF, 100, 0x7E, 0x00]);
}

// SubCmd 0x02 — StopSpeed (brake)
async function motorStop(port) {
  return _portOut(port, 0x02, [0x7E]);
}

// ── color sensor ─────────────────────────────────────────────────────────────

// Set sensor to Color mode (mode 2) with delta=1, notifications enabled
async function sensorSetupMode(port) {
  return _write([0x0A, 0x00, 0x41, port, 0x02, 0x01, 0x00, 0x00, 0x00, 0x01]);
}

// ── exports ──────────────────────────────────────────────────────────────────

window.legoConnect          = legoConnect;
window.legoDisconnect       = legoDisconnect;
window.motorRunForDegrees   = motorRunForDegrees;
window.motorRun             = motorRun;
window.motorRunTime         = motorRunTime;
window.motorStop            = motorStop;
window.sensorSetupMode      = sensorSetupMode;
window.getLastColor         = () => window._lastColor;
