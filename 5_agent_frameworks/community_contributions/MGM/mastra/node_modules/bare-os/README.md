# bare-os

Operating system utilities for Bare. The API closely follows that of the Node.js `os` module.

```
npm i bare-os
```

## Usage

```js
const os = require('bare-os')

console.log(os.platform()) // 'darwin', 'linux', 'win32', ...
console.log(os.arch()) // 'arm64', 'x64', ...
console.log(os.homedir())
console.log(os.tmpdir())
console.log(os.hostname())
console.log(os.networkInterfaces())
```

## API

#### `os.constants`

An object containing the following properties:

- `signals` - Signal constants such as `SIGTERM` and `SIGKILL`.
- `errnos` - Error number constants.
- `priority` - Process priority constants.

These are also available as a separate module:

```js
const constants = require('bare-os/constants')
```

#### `os.EOL`

The platform-specific end-of-line marker. `'\r\n'` on Windows, `'\n'` everywhere else.

#### `os.devNull`

The platform-specific path to the null device. `'\\\\.\\nul'` on Windows, `'/dev/null'` everywhere else.

#### `const p = os.platform()`

Returns the operating system platform as a string. Possible values include `'android'`, `'darwin'`, `'ios'`, `'linux'`, and `'win32'`.

#### `const a = os.arch()`

Returns the CPU architecture as a string. Possible values include `'arm'`, `'arm64'`, `'ia32'`, and `'x64'`.

#### `const t = os.type()`

Returns the operating system name as returned by `uname(3)`.

#### `const v = os.version()`

Returns the operating system version.

#### `const r = os.release()`

Returns the operating system release.

#### `const m = os.machine()`

Returns the machine type as a string.

#### `const p = os.execPath()`

Returns the absolute path of the executable that started the process.

#### `const id = os.pid()`

Returns the process ID.

#### `const id = os.ppid()`

Returns the parent process ID.

#### `const dir = os.cwd()`

Returns the current working directory.

#### `os.chdir(dir)`

Changes the current working directory to `dir`.

#### `const dir = os.tmpdir()`

Returns the operating system's default directory for temporary files.

#### `const dir = os.homedir()`

Returns the home directory of the current user.

#### `const name = os.hostname()`

Returns the hostname of the operating system.

#### `const interfaces = os.networkInterfaces()`

Returns an object containing network interfaces that have been assigned a network address. Each key on the returned object identifies a network interface. The associated value is an array of objects with the following properties:

- `address` - The assigned IPv4 or IPv6 address.
- `netmask` - The IPv4 or IPv6 network mask.
- `family` - Either `'IPv4'` or `'IPv6'`.
- `cidr` - The assigned IPv4 or IPv6 address with the routing prefix in CIDR notation.
- `mac` - The MAC address of the network interface.
- `internal` - `true` if the network interface is a loopback or similar interface that is not remotely accessible; otherwise `false`.
- `scopeid` - The numeric IPv6 scope ID. Only specified when `family` is `'IPv6'`.

#### `os.kill(pid[, signal])`

Sends `signal` to the process identified by `pid`. `signal` can be a string or a number. Defaults to `'SIGTERM'`.

#### `const info = os.userInfo([uid])`

Returns information about a current user. The `uid` value defaults to the current effective uid. The returned object has the following properties:

- `uid` - The user ID.
- `gid` - The group ID.
- `username` - The username.
- `homedir` - The home directory.
- `shell` - The shell, or `null` if unavailable.

#### `const info = os.groupInfo([gid])`

Returns information about a group. The `gid` value defaults to the effective group ID of the calling process. The returned object has the following properties:

- `groupname` - The group name.
- `gid` - The group ID.
- `members` - List with the names of group members.

#### `const e = os.endianness()`

Returns `'LE'` on little-endian systems and `'BE'` on big-endian systems.

#### `const n = os.availableParallelism()`

Returns the number of logical CPU cores available to the process.

#### `const usage = os.cpuUsage([previous])`

Returns an object with `user` and `system` properties, each representing CPU time in microseconds. If `previous` is provided, the returned values are relative to it.

#### `const usage = os.threadCpuUsage([previous])`

Like `os.cpuUsage()` but for the current thread only.

#### `const usage = os.resourceUsage()`

Returns an object describing the resource usage of the current process. The returned object has the following properties:

- `userCPUTime` - User CPU time in microseconds.
- `systemCPUTime` - System CPU time in microseconds.
- `maxRSS` - Maximum resident set size in bytes.
- `sharedMemorySize` - Shared memory size.
- `unsharedDataSize` - Unshared data size.
- `unsharedStackSize` - Unshared stack size.
- `minorPageFault` - Minor page faults.
- `majorPageFault` - Major page faults.
- `swappedOut` - Swap count.
- `fsRead` - File system reads.
- `fsWrite` - File system writes.
- `ipcSent` - IPC messages sent.
- `ipcReceived` - IPC messages received.
- `signalsCount` - Signals received.
- `voluntaryContextSwitches` - Voluntary context switches.
- `involuntaryContextSwitches` - Involuntary context switches.

#### `const usage = os.memoryUsage()`

Returns an object describing the memory usage of the process. The returned object has the following properties:

- `rss` - Resident set size in bytes.
- `heapTotal` - Total heap size in bytes.
- `heapUsed` - Used heap size in bytes.
- `external` - Memory usage of C++ objects bound to JavaScript objects.

#### `const bytes = os.freemem()`

Returns the amount of free system memory in bytes.

#### `const bytes = os.totalmem()`

Returns the total amount of system memory in bytes.

#### `const bytes = os.availableMemory()`

Returns an estimate of the amount of memory available for the process in bytes.

#### `const bytes = os.constrainedMemory()`

Returns the amount of memory available to the process under resource constraints, such as cgroups.

#### `const seconds = os.uptime()`

Returns the system uptime in seconds.

#### `const avgs = os.loadavg()`

Returns an array containing the 1, 5, and 15 minute load averages.

#### `const list = os.cpus()`

Returns an array of objects describing each logical CPU core. Each object has the following properties:

- `model` - The CPU model.
- `speed` - The CPU speed in MHz.
- `times` - An object with `user`, `nice`, `sys`, `idle`, and `irq` CPU time values in milliseconds.

#### `const title = os.getProcessTitle()`

Returns the current process title.

#### `os.setProcessTitle(title)`

Sets the process title. `title` is coerced to a string and must be shorter than 256 characters.

#### `const priority = os.getPriority([pid])`

Returns the scheduling priority of the process specified by `pid`. Defaults to `0`, meaning the current process.

#### `os.setPriority([pid, ]priority)`

Sets the scheduling priority of the process specified by `pid`. If `pid` is omitted, the priority of the current process is set.

#### `const keys = os.getEnvKeys()`

Returns an array of the names of all environment variables.

#### `const value = os.getEnv(name)`

Returns the value of the environment variable `name`, or `undefined` if it is not set.

#### `const exists = os.hasEnv(name)`

Returns `true` if the environment variable `name` is set, otherwise `false`.

#### `os.setEnv(name, value)`

Sets the environment variable `name` to `value`.

#### `os.unsetEnv(name)`

Removes the environment variable `name`.

## License

Apache-2.0
