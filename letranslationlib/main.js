const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow;
let flaskProcess;

function waitForServer(url, retries, callback) {
  http.get(url, () => callback(true)).on('error', () => {
    if (retries === 0) return callback(false);
    setTimeout(() => waitForServer(url, retries - 1, callback), 500);
  });
}


function startFlask() {
    const serverPath = app.isPackaged
      ? path.join(process.resourcesPath, 'server')
      : path.join(__dirname, 'dist', 'server');
  
    flaskProcess = spawn(serverPath, []);
  
    flaskProcess.stdout.on('data', d => console.log('Flask:', d.toString()));
    flaskProcess.stderr.on('data', d => console.error('Flask error:', d.toString()));
  }

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    title: 'EasyLego',
    webPreferences: { nodeIntegration: false }
  });

  const indexPath = app.isPackaged
    ? path.join(process.resourcesPath, 'index.html')
    : path.join(__dirname, 'index.html');

  // Wait for Flask to be ready before loading the page
  waitForServer('http://localhost:5001/', 20, (ok) => {
    mainWindow.loadFile(indexPath);
  });
}

app.whenReady().then(() => {
  startFlask();
  setTimeout(createWindow, 1000); // give Flask a moment to start
});

app.on('window-all-closed', () => {
  if (flaskProcess) flaskProcess.kill();
  app.quit();
});