import process from 'node:process';

const asyncCallbacks = new Set();
const callbacks = new Set();

let isCalled = false;
let isRegistered = false;

async function flushStdio() {
	const flush = stream => new Promise(resolve => {
		if (!stream || !stream.writable || stream.writableEnded || stream.destroyed) {
			resolve();
			return;
		}

		const onError = () => {
			stream.off('error', onError);
			resolve();
		};

		stream.once('error', onError);

		try {
			stream.write('', () => {
				stream.off('error', onError);
				resolve();
			});
		} catch {
			stream.off('error', onError);
			resolve();
		}
	});

	const timeout = new Promise(resolve => {
		setTimeout(resolve, 1000);
	});

	await Promise.race([
		Promise.all([flush(process.stdout), flush(process.stderr)]),
		timeout,
	]);
}

async function exit(shouldManuallyExit, isSynchronous, signal) {
	if (isCalled) {
		return;
	}

	isCalled = true;

	if (asyncCallbacks.size > 0 && isSynchronous) {
		console.error([
			'SYNCHRONOUS TERMINATION NOTICE:',
			'When explicitly exiting the process via process.exit or via a parent process,',
			'asynchronous tasks in your exitHooks will not run. Either remove these tasks,',
			'use gracefulExit() instead of process.exit(), or ensure your parent process',
			'sends a SIGINT to the process running this code.',
		].join(' '));
	}

	let exitCode = 0;

	// A non-graceful signal should be preserved over process.exitCode
	if (signal > 0) {
		exitCode = 128 + signal;
	// Respect process.exitCode for graceful exits
	} else if (typeof process.exitCode === 'number' || typeof process.exitCode === 'string') {
		exitCode = process.exitCode;
	}

	const done = (force = false) => {
		if (force === true || shouldManuallyExit === true) {
			process.exit(exitCode); // eslint-disable-line unicorn/no-process-exit
		}
	};

	for (const callback of callbacks) {
		callback(exitCode);
	}

	if (isSynchronous) {
		done();
		return;
	}

	const promises = [];
	let forceAfter = 0;
	for (const [callback, wait] of asyncCallbacks) {
		forceAfter = Math.max(forceAfter, wait);
		promises.push(Promise.resolve(callback(exitCode)));
	}

	// Force exit if we exceeded our wait value
	const asyncTimer = forceAfter > 0
		? setTimeout(() => {
			done(true);
		}, forceAfter)
		: undefined;

	await Promise.all(promises);
	// Let flushStdio handle its own timeout without the force-exit timer.
	clearTimeout(asyncTimer);
	await flushStdio();
	done();
}

function addHook(options) {
	const {onExit, wait, isSynchronous} = options;
	const asyncCallbackConfig = [onExit, wait];

	if (isSynchronous) {
		callbacks.add(onExit);
	} else {
		asyncCallbacks.add(asyncCallbackConfig);
	}

	if (!isRegistered) {
		isRegistered = true;

		// Exit cases that support asynchronous handling
		process.once('beforeExit', exit.bind(undefined, true, false, -128));
		process.once('SIGINT', exit.bind(undefined, true, false, 2));
		process.once('SIGTERM', exit.bind(undefined, true, false, 15));

		// Explicit exit events. Calling will force an immediate exit and run all
		// synchronous hooks. Explicit exits must not extend the node process
		// artificially. Will log errors if asynchronous calls exist.
		process.once('exit', exit.bind(undefined, false, true, 0));

		// PM2 Cluster shutdown message. Caught to support async handlers with pm2,
		// needed because explicitly calling process.exit() doesn't trigger the
		// beforeExit event, and the exit event cannot support async handlers,
		// since the event loop is never called after it.
		process.on('message', message => {
			if (message === 'shutdown') {
				exit(true, true, -128);
			}
		});
	}

	return () => {
		if (isSynchronous) {
			callbacks.delete(onExit);
		} else {
			asyncCallbacks.delete(asyncCallbackConfig);
		}
	};
}

export default function exitHook(onExit) {
	if (typeof onExit !== 'function') {
		throw new TypeError('onExit must be a function');
	}

	return addHook({
		onExit,
		isSynchronous: true,
	});
}

export function asyncExitHook(onExit, options = {}) {
	if (typeof onExit !== 'function') {
		throw new TypeError('onExit must be a function');
	}

	if (!(typeof options.wait === 'number' && options.wait > 0)) {
		throw new TypeError('wait must be set to a positive numeric value');
	}

	return addHook({
		onExit,
		wait: options.wait,
		isSynchronous: false,
	});
}

export function gracefulExit(signal) {
	if (signal !== undefined) {
		process.exitCode = signal;
	}

	exit(true, false, -128);
}
