/**
 * Comlina Python Runner
 * Finds the local virtual environment (if available) and runs the python command.
 * Passes all arguments through to python.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

function findPython() {
  const rootDir = path.resolve(__dirname, '..');
  const serverDir = path.join(rootDir, 'server');
  const workerDir = path.join(rootDir, 'worker');

  const candidates = [
    path.join(serverDir, '.venv', 'Scripts', 'python.exe'),
    path.join(serverDir, 'venv', 'Scripts', 'python.exe'),
    path.join(workerDir, '.venv', 'Scripts', 'python.exe'),
    path.join(rootDir, '.venv', 'Scripts', 'python.exe'),
    path.join(serverDir, '.venv', 'bin', 'python'),
    path.join(serverDir, 'venv', 'bin', 'python'),
    path.join(workerDir, '.venv', 'bin', 'python'),
    path.join(rootDir, '.venv', 'bin', 'python')
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return process.platform === 'win32' ? 'python' : 'python3';
}

function main() {
  const pythonPath = findPython();
  const args = process.argv.slice(2);
  const rootDir = path.resolve(__dirname, '..');

  const proc = spawn(pythonPath, args, {
    cwd: rootDir,
    stdio: 'inherit',
    env: { ...process.env, PYTHONPATH: [path.join(rootDir, 'server'), path.join(rootDir, 'worker'), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter) }
  });

  proc.on('close', (code) => {
    process.exit(code ?? 0);
  });

  proc.on('error', (err) => {
    console.error(`Failed to start python process: ${err.message}`);
    process.exit(1);
  });
}

main();
