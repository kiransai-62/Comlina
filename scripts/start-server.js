/**
 * Comlina FastAPI Dev Server Launcher
 * Finds the local virtual environment (if available) and launches Uvicorn.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

function findUvicornCommand(serverDir) {
  // Candidate paths in order of preference
  const candidates = [
    // Windows virtualenv scripts
    {
      cmd: path.join(serverDir, '.venv', 'Scripts', 'python.exe'),
      args: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
    },
    {
      cmd: path.join(serverDir, '.venv', 'Scripts', 'uvicorn.exe'),
      args: ['app.main:app', '--reload', '--port', '8000']
    },
    {
      cmd: path.join(serverDir, 'venv', 'Scripts', 'python.exe'),
      args: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
    },
    // Unix virtualenv bin
    {
      cmd: path.join(serverDir, '.venv', 'bin', 'python'),
      args: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
    },
    {
      cmd: path.join(serverDir, '.venv', 'bin', 'uvicorn'),
      args: ['app.main:app', '--reload', '--port', '8000']
    },
    {
      cmd: path.join(serverDir, 'venv', 'bin', 'python'),
      args: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
    }
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate.cmd)) {
      return candidate;
    }
  }

  // Fallback to uvicorn in PATH
  return {
    cmd: process.platform === 'win32' ? 'uvicorn.cmd' : 'uvicorn',
    args: ['app.main:app', '--reload', '--port', '8000'],
    fallbackCmd: 'python',
    fallbackArgs: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000']
  };
}

function main() {
  const rootDir = path.resolve(__dirname, '..');
  const serverDir = path.join(rootDir, 'server');

  const { cmd, args, fallbackCmd, fallbackArgs } = findUvicornCommand(serverDir);

  const env = { ...process.env, PYTHONUNBUFFERED: '1' };

  let child;
  try {
    child = spawn(cmd, args, {
      cwd: serverDir,
      stdio: 'inherit',
      shell: false,
      env
    });
  } catch {
    if (fallbackCmd) {
      child = spawn(fallbackCmd, fallbackArgs, {
        cwd: serverDir,
        stdio: 'inherit',
        shell: true,
        env
      });
    } else {
      throw err;
    }
  }

  child.on('error', (err) => {
    if (fallbackCmd) {
      console.warn(`[Server] Failed to launch with ${cmd}, trying fallback ${fallbackCmd}...`);
      const fallbackChild = spawn(fallbackCmd, fallbackArgs, {
        cwd: serverDir,
        stdio: 'inherit',
        shell: true,
        env
      });
      forwardSignals(fallbackChild);
      fallbackChild.on('exit', (code) => process.exit(code || 0));
    } else {
      console.error('[Server] Failed to start Uvicorn process:', err);
      process.exit(1);
    }
  });

  forwardSignals(child);

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}

function forwardSignals(child) {
  const handleSignal = (signal) => {
    if (child && !child.killed) {
      child.kill(signal);
    }
  };
  process.on('SIGINT', () => handleSignal('SIGINT'));
  process.on('SIGTERM', () => handleSignal('SIGTERM'));
}

main();
