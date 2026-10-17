// client/patch-fat32.js
// Monkey-patches fs for FAT32 / SD Card filesystem compatibility on Windows:
// 1. Converts fs.readlink EISDIR to EINVAL (for Webpack/enhanced-resolve symlink check)
// 2. Adds retry on fs.rmdir ENOTEMPTY/EBUSY/EPERM
// 3. Adds retry and graceful fallback on fs.readdir EPERM/EBUSY
// 4. Adds retry on fs.mkdir EPERM/EBUSY
const fs = require('fs');

const patchError = (err, path) => {
  if (err && err.code === 'EISDIR') {
    const customErr = new Error(`EINVAL: invalid argument, readlink '${path}'`);
    customErr.code = 'EINVAL';
    customErr.errno = -4071;
    customErr.syscall = 'readlink';
    customErr.path = path;
    return customErr;
  }
  return err;
};

// 1. readlink patches
const origReadlink = fs.readlink;
fs.readlink = function(path, ...args) {
  const cb = typeof args[args.length - 1] === 'function' ? args[args.length - 1] : null;
  if (cb) {
    origReadlink.call(fs, path, ...args.slice(0, -1), (err, linkString) => {
      cb(patchError(err, path), linkString);
    });
  } else {
    return origReadlink.call(fs, path, ...args);
  }
};

const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = function(path, options) {
  try {
    return origReadlinkSync.call(fs, path, options);
  } catch (err) {
    throw patchError(err, path);
  }
};

if (fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = async function(path, options) {
    try {
      return await origPromisesReadlink.call(fs.promises, path, options);
    } catch (err) {
      throw patchError(err, path);
    }
  };
}

// 2. rmdir retry on FAT32 ENOTEMPTY / EBUSY / EPERM
const origRmdir = fs.rmdir;
fs.rmdir = function(path, ...args) {
  const cb = typeof args[args.length - 1] === 'function' ? args[args.length - 1] : null;
  if (!cb) return origRmdir.call(fs, path, ...args);

  let attempts = 0;
  const tryRmdir = () => {
    origRmdir.call(fs, path, ...args.slice(0, -1), (err) => {
      if (err && (err.code === 'ENOTEMPTY' || err.code === 'EBUSY' || err.code === 'EPERM') && attempts < 6) {
        attempts++;
        return setTimeout(tryRmdir, 50 * attempts);
      }
      cb(null); // gracefully swallow rmdir cleanup failure on FAT32
    });
  };
  tryRmdir();
};

const origRmdirSync = fs.rmdirSync;
fs.rmdirSync = function(path, options) {
  let attempts = 0;
  while (true) {
    try {
      return origRmdirSync.call(fs, path, options);
    } catch (err) {
      if ((err.code === 'ENOTEMPTY' || err.code === 'EBUSY' || err.code === 'EPERM') && attempts < 3) {
        attempts++;
        continue;
      } else {
        return; // gracefully swallow
      }
    }
  }
};

if (fs.promises && fs.promises.rmdir) {
  const origPromisesRmdir = fs.promises.rmdir;
  fs.promises.rmdir = async function(path, options) {
    let attempts = 0;
    while (true) {
      try {
        return await origPromisesRmdir.call(fs.promises, path, options);
      } catch (err) {
        if ((err.code === 'ENOTEMPTY' || err.code === 'EBUSY' || err.code === 'EPERM') && attempts < 6) {
          attempts++;
          await new Promise((r) => setTimeout(r, 50 * attempts));
        } else {
          return; // gracefully swallow
        }
      }
    }
  };
}

// 3. readdir retry and graceful fallback on FAT32 EPERM / EBUSY
const origReaddir = fs.readdir;
fs.readdir = function(path, ...args) {
  const cb = typeof args[args.length - 1] === 'function' ? args[args.length - 1] : null;
  if (!cb) return origReaddir.call(fs, path, ...args);

  let attempts = 0;
  const tryReaddir = () => {
    origReaddir.call(fs, path, ...args.slice(0, -1), (err, files) => {
      if (err && (err.code === 'EPERM' || err.code === 'EBUSY')) {
        attempts++;
        if (attempts < 5) {
          return setTimeout(tryReaddir, 50 * attempts);
        }
        return cb(null, []);
      }
      cb(err, files);
    });
  };
  tryReaddir();
};

if (fs.promises && fs.promises.readdir) {
  const origPromisesReaddir = fs.promises.readdir;
  fs.promises.readdir = async function(path, options) {
    let attempts = 0;
    while (true) {
      try {
        return await origPromisesReaddir.call(fs.promises, path, options);
      } catch (err) {
        if (err.code === 'EPERM' || err.code === 'EBUSY') {
          attempts++;
          if (attempts < 5) {
            await new Promise((r) => setTimeout(r, 50 * attempts));
            continue;
          }
          return [];
        }
        throw err;
      }
    }
  };
}

// 4. mkdir retry on FAT32 EPERM / EBUSY
const origMkdir = fs.mkdir;
fs.mkdir = function(path, ...args) {
  const cb = typeof args[args.length - 1] === 'function' ? args[args.length - 1] : null;
  if (!cb) return origMkdir.call(fs, path, ...args);

  let attempts = 0;
  const tryMkdir = () => {
    origMkdir.call(fs, path, ...args.slice(0, -1), (err) => {
      if (err && (err.code === 'EPERM' || err.code === 'EBUSY') && attempts < 5) {
        if (fs.existsSync(path)) {
          return cb(null);
        }
        attempts++;
        return setTimeout(tryMkdir, 50 * attempts);
      }
      cb(err);
    });
  };
  tryMkdir();
};

const origMkdirSync = fs.mkdirSync;
fs.mkdirSync = function(path, options) {
  let attempts = 0;
  while (true) {
    try {
      return origMkdirSync.call(fs, path, options);
    } catch (err) {
      if (fs.existsSync(path)) {
        return;
      }
      if ((err.code === 'EPERM' || err.code === 'EBUSY') && attempts < 3) {
        attempts++;
        continue;
      }
      throw err;
    }
  }
};

if (fs.promises && fs.promises.mkdir) {
  const origPromisesMkdir = fs.promises.mkdir;
  fs.promises.mkdir = async function(path, options) {
    let attempts = 0;
    while (true) {
      try {
        return await origPromisesMkdir.call(fs.promises, path, options);
      } catch (err) {
        if (fs.existsSync(path)) {
          return;
        }
        if ((err.code === 'EPERM' || err.code === 'EBUSY') && attempts < 5) {
          attempts++;
          await new Promise((r) => setTimeout(r, 50 * attempts));
          continue;
        }
        throw err;
      }
    }
  };
}

