/**
 * Comlina Local Dev Dependency Checker
 * Verifies that PostgreSQL and Redis are reachable before starting the dev server.
 */

const fs = require('fs');
const path = require('path');
const net = require('net');

function parseEnvFile(filePath) {
  const env = {};
  if (!fs.existsSync(filePath)) {
    return env;
  }
  const content = fs.readFileSync(filePath, 'utf-8');
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    let val = trimmed.slice(eqIdx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

function parseHostAndPort(urlStr, defaultPort, defaultHost = 'localhost') {
  if (!urlStr) {
    return { host: defaultHost, port: defaultPort };
  }
  try {
    // Replace custom scheme (e.g. postgresql+asyncpg:// or redis://) with http:// for URL parsing
    const normalized = urlStr.replace(/^[a-zA-Z0-9_+]+:\/\//, 'http://');
    const parsed = new URL(normalized);
    const host = parsed.hostname || defaultHost;
    const port = parsed.port ? parseInt(parsed.port, 10) : defaultPort;
    return { host, port };
  } catch {
    // Regex fallback
    const match = urlStr.match(/@([^:/]+)(?::(\d+))?/);
    if (match) {
      return {
        host: match[1] || defaultHost,
        port: match[2] ? parseInt(match[2], 10) : defaultPort
      };
    }
    return { host: defaultHost, port: defaultPort };
  }
}

function checkPort(host, port, timeoutMs = 1500) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    let settled = false;

    socket.setTimeout(timeoutMs);

    socket.once('connect', () => {
      if (!settled) {
        settled = true;
        socket.destroy();
        resolve(true);
      }
    });

    socket.once('timeout', () => {
      if (!settled) {
        settled = true;
        socket.destroy();
        resolve(false);
      }
    });

    socket.once('error', () => {
      if (!settled) {
        settled = true;
        socket.destroy();
        resolve(false);
      }
    });

    socket.connect(port, host);
  });
}

async function main() {
  const rootDir = path.resolve(__dirname, '..');
  const serverEnvPath = path.join(rootDir, 'server', '.env');
  const rootEnvPath = path.join(rootDir, '.env');

  // Load environment variables prioritizing server/.env then root .env
  const serverEnv = parseEnvFile(serverEnvPath);
  const rootEnv = parseEnvFile(rootEnvPath);
  const mergedEnv = { ...rootEnv, ...serverEnv, ...process.env };

  const dbUrl = mergedEnv.DATABASE_URL || 'postgresql+asyncpg://postgres:postgres@localhost:5432/comlina';
  const redisUrl = mergedEnv.REDIS_URL || 'redis://localhost:6379/0';

  const pg = parseHostAndPort(dbUrl, 5432, 'localhost');
  const redis = parseHostAndPort(redisUrl, 6379, 'localhost');

  const envMode = (mergedEnv.ENVIRONMENT || process.env.NODE_ENV || 'development').toLowerCase();
  const isDev = envMode !== 'production';
  const isSqlite = dbUrl.toLowerCase().includes('sqlite');

  console.log('🔍 [Startup Check] Verifying backend dependencies...');

  const [pgOk, redisOk] = await Promise.all([
    isSqlite ? Promise.resolve(true) : checkPort(pg.host, pg.port),
    checkPort(redis.host, redis.port)
  ]);

  let hasError = false;

  if (isSqlite) {
    console.log(`\x1b[32m✔ SQLite database configured (${dbUrl})\x1b[0m`);
  } else if (pgOk) {
    console.log(`\x1b[32m✔ PostgreSQL is reachable on ${pg.host}:${pg.port}\x1b[0m`);
  } else if (isDev || mergedEnv.SKIP_DEP_CHECK === 'true' || process.env.SKIP_DEP_CHECK === 'true') {
    console.warn(
      `\x1b[33m⚠ Postgres is not reachable on ${pg.host}:${pg.port} — local development will proceed using SQLite fallback (comlina_dev.db)\x1b[0m`
    );
  } else {
    hasError = true;
    console.error(
      `\x1b[31m✖ Postgres not reachable on ${pg.host}:${pg.port} — start it with \`docker-compose up -d postgres\`\x1b[0m`
    );
  }

  if (redisOk) {
    console.log(`\x1b[32m✔ Redis is reachable on ${redis.host}:${redis.port}\x1b[0m`);
  } else if (isDev || mergedEnv.SKIP_DEP_CHECK === 'true' || process.env.SKIP_DEP_CHECK === 'true') {
    console.warn(
      `\x1b[33m⚠ Redis is not reachable on ${redis.host}:${redis.port} — webhook queueing and background workers will be skipped\x1b[0m`
    );
  } else {
    hasError = true;
    console.error(
      `\x1b[31m✖ Redis not reachable on ${redis.host}:${redis.port} — start it with \`docker-compose up -d redis\`\x1b[0m`
    );
  }

  if (hasError) {
    console.error('\n\x1b[31mRequired backend dependencies are not running in production mode. Please start PostgreSQL and Redis.\x1b[0m\n');
    process.exit(1);
  }

  if (!pgOk || !redisOk) {
    console.warn('\x1b[33m[WARN] External backend dependencies (PostgreSQL/Redis) are offline.\x1b[0m');
    if (!pgOk && !isSqlite) {
      console.warn('\x1b[33m[WARN] Local development will proceed using the SQLite fallback (server/comlina_dev.db).\x1b[0m');
    }
    if (!redisOk) {
      console.warn('\x1b[33m[WARN] Redis is unreachable; webhook queueing and background workers will be skipped.\x1b[0m');
    }
    process.exit(0);
  }

  console.log('\x1b[32m✔ All required backend dependencies are reachable.\x1b[0m\n');
  process.exit(0);
}

if (require.main === module) {
  main().catch((err) => {
    console.error('[Startup Check] Unexpected error:', err);
    process.exit(1);
  });
}

module.exports = { checkPort, parseHostAndPort, parseEnvFile, main };
