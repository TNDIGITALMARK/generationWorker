import express from 'express';
import dotenv from 'dotenv';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import axios from 'axios';
import { initializeFirebase, testFirebaseConnection, db } from './firebase/firebaseAdmin';

dotenv.config();

// Initialize Firebase on startup
const { app: firebaseApp } = initializeFirebase();

const app = express();
const PORT = process.env.PORT || 5001;
console.log(`Server configured to run on PORT: ${PORT}`);
const PYTHON_SERVICE_PORT = 8000;
const PYTHON_SERVICE_URL = `http://127.0.0.1:${PYTHON_SERVICE_PORT}`;
const COMFYUI_PORT = 8188;
const COMFYUI_URL = `http://127.0.0.1:${COMFYUI_PORT}`;

let pythonProcess: ChildProcess | null = null;
let comfyuiProcess: ChildProcess | null = null;

app.use(express.json());

async function startPythonService(): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log('Starting Python service...');
    
    const pythonServicePath = path.join(__dirname, 'python_service');
    const startScript = path.join(pythonServicePath, 'start.py');
    const venvPython = path.join(pythonServicePath, 'venv', 'bin', 'python');
    
    pythonProcess = spawn(venvPython, [startScript], {
      cwd: pythonServicePath,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python]: ${data.toString().trim()}`);
    });

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Python Error]: ${data.toString().trim()}`);
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python service:', error);
      reject(error);
    });

    pythonProcess.on('exit', (code, signal) => {
      console.log(`Python service exited with code ${code}, signal ${signal}`);
      pythonProcess = null;
    });

    setTimeout(async () => {
      try {
        await checkPythonServiceHealth();
        console.log('Python service is ready');
        resolve();
      } catch (error) {
        console.error('Python service health check failed:', error);
        reject(error);
      }
    }, 60000);
  });
}

async function startComfyUIService(): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log('Starting ComfyUI service...');
    
    const comfyUIPath = path.join(__dirname, 'ComfyUI');
    const mainScript = path.join(comfyUIPath, 'main.py');
    const comfyVenvPython = path.join(comfyUIPath, 'venv', 'bin', 'python');
    
    comfyuiProcess = spawn(comfyVenvPython, [mainScript, '--listen', '0.0.0.0', '--port', COMFYUI_PORT.toString()], {
      cwd: comfyUIPath,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    comfyuiProcess.stdout?.on('data', (data) => {
      console.log(`[ComfyUI]: ${data.toString().trim()}`);
    });

    comfyuiProcess.stderr?.on('data', (data) => {
      console.error(`[ComfyUI Error]: ${data.toString().trim()}`);
    });

    comfyuiProcess.on('error', (error) => {
      console.error('Failed to start ComfyUI service:', error);
      reject(error);
    });

    comfyuiProcess.on('exit', (code, signal) => {
      console.log(`ComfyUI service exited with code ${code}, signal ${signal}`);
      comfyuiProcess = null;
    });

    setTimeout(async () => {
      try {
        await checkComfyUIServiceHealth();
        console.log('ComfyUI service is ready');
        resolve();
      } catch (error) {
        console.error('ComfyUI service health check failed:', error);
        reject(error);
      }
    }, 30000);
  });
}

async function checkPythonServiceHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${PYTHON_SERVICE_URL}/health`, { timeout: 30000 });
    return response.status === 200;
  } catch (error) {
    throw new Error(`Python service health check failed: ${error}`);
  }
}

async function checkComfyUIServiceHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${COMFYUI_URL}/system_stats`, { timeout: 10000 });
    return response.status === 200;
  } catch (error) {
    throw new Error(`ComfyUI service health check failed: ${error}`);
  }
}

function gracefulShutdown() {
  console.log('Shutting down gracefully...');
  
  if (pythonProcess) {
    console.log('Terminating Python service...');
    pythonProcess.kill('SIGTERM');
    
    setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        console.log('Force killing Python service...');
        pythonProcess.kill('SIGKILL');
      }
    }, 5000);
  }

  if (comfyuiProcess) {
    console.log('Terminating ComfyUI service...');
    comfyuiProcess.kill('SIGTERM');
    
    setTimeout(() => {
      if (comfyuiProcess && !comfyuiProcess.killed) {
        console.log('Force killing ComfyUI service...');
        comfyuiProcess.kill('SIGKILL');
      }
    }, 5000);
  }
  
  process.exit(0);
}

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

app.get('/', (req, res) => {
  res.json({ 
    message: 'Generation Worker is running', 
    port: PORT,
    pythonService: pythonProcess ? 'running' : 'stopped',
    pythonServiceUrl: PYTHON_SERVICE_URL
  });
});

app.get('/health', async (req, res) => {
  try {
    const pythonHealth = pythonProcess ? await checkPythonServiceHealth() : false;
    const comfyuiHealth = comfyuiProcess ? await checkComfyUIServiceHealth() : false;
    
    // Test Firebase connection
    const firebaseHealth = await testFirebaseConnection();
    
    res.json({
      status: 'healthy',
      nodeService: true,
      pythonService: pythonHealth,
      comfyuiService: comfyuiHealth,
      firebase: firebaseHealth,
      projectId: process.env.FIREBASE_PROJECT_ID,
      comfyuiUrl: COMFYUI_URL
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      nodeService: true,
      pythonService: false,
      comfyuiService: false,
      firebase: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

async function startServer() {
  try {
    // Start both services in parallel
    await Promise.all([
      startPythonService(),
      startComfyUIService()
    ]);
    
    app.listen(PORT, () => {
      console.log(`Generation Worker server running on port ${PORT}`);
      console.log(`Python service available at ${PYTHON_SERVICE_URL}`);
      console.log(`ComfyUI service available at ${COMFYUI_URL}`);
    });
  } catch (error) {
    console.error('Failed to start services:', error);
    process.exit(1);
  }
}

startServer();