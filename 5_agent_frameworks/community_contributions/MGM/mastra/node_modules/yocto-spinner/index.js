import process from 'node:process';
import {stripVTControlCharacters} from 'node:util';
import yoctocolors from 'yoctocolors';

const isUnicodeSupported = process.platform !== 'win32'
	|| Boolean(process.env.WT_SESSION) // Windows Terminal
	|| process.env.TERM_PROGRAM === 'vscode';

const isInteractive = stream => Boolean(
	stream.isTTY
	&& process.env.TERM !== 'dumb'
	&& !('CI' in process.env),
);

const infoSymbol = yoctocolors.blue(isUnicodeSupported ? 'ℹ' : 'i');
const successSymbol = yoctocolors.green(isUnicodeSupported ? '✔' : '√');
const warningSymbol = yoctocolors.yellow(isUnicodeSupported ? '⚠' : '‼');
const errorSymbol = yoctocolors.red(isUnicodeSupported ? '✖' : '×');

const defaultSpinner = {
	frames: isUnicodeSupported
		? [
			'⠋',
			'⠙',
			'⠹',
			'⠸',
			'⠼',
			'⠴',
			'⠦',
			'⠧',
			'⠇',
			'⠏',
		]
		: [
			'-',
			'\\',
			'|',
			'/',
		],
	interval: 80,
};

const SYNCHRONIZED_OUTPUT_ENABLE = '\u001B[?2026h';
const SYNCHRONIZED_OUTPUT_DISABLE = '\u001B[?2026l';

const activeHooksPerStream = new Set();

class YoctoSpinner {
	#frames;
	#interval;
	#currentFrame = -1;
	#timer;
	#handleSignals;
	#text;
	#stream;
	#color;
	#lines = 0;
	#exitHandlerBound;
	#isInteractive;
	#lastSpinnerFrameTime = 0;
	#isSpinning = false;
	#hookedStreams = new Map();
	#isInternalWrite = false;
	#isDeferringRender = false;

	constructor(options = {}) {
		const spinner = options.spinner ?? defaultSpinner;

		if (!Array.isArray(spinner.frames) || spinner.frames.length === 0 || spinner.frames.some(frame => typeof frame !== 'string')) {
			throw new Error('The `spinner.frames` option must be a non-empty array of strings');
		}

		if (spinner.interval !== undefined && !(Number.isInteger(spinner.interval) && spinner.interval > 0)) {
			throw new Error('The `spinner.interval` option must be a positive integer');
		}

		this.#frames = spinner.frames;
		this.#interval = spinner.interval ?? defaultSpinner.interval;
		this.#handleSignals = options.handleSignals ?? true; // SOMEDAY: Remove this option if Node.js ever adds passive signal listeners: https://github.com/nodejs/node/issues/62909
		this.#text = options.text ?? '';
		this.#stream = options.stream ?? process.stderr;
		this.#color = options.color ?? 'cyan';
		this.#isInteractive = isInteractive(this.#stream);
		this.#exitHandlerBound = this.#exitHandler.bind(this);
	}

	#internalWrite(action) {
		this.#isInternalWrite = true;
		try {
			return action();
		} finally {
			this.#isInternalWrite = false;
		}
	}

	#stringifyChunk(chunk, encoding) {
		if (chunk === undefined || chunk === null) {
			return '';
		}

		if (typeof chunk === 'string') {
			return chunk;
		}

		if (Buffer.isBuffer(chunk) || ArrayBuffer.isView(chunk)) {
			const normalizedEncoding = typeof encoding === 'string' && encoding !== '' && encoding !== 'buffer' ? encoding : 'utf8';
			return Buffer.from(chunk).toString(normalizedEncoding);
		}

		return String(chunk);
	}

	#withSynchronizedOutput(action) {
		if (!this.#isInteractive) {
			return action();
		}

		try {
			this.#write(SYNCHRONIZED_OUTPUT_ENABLE);
			return action();
		} finally {
			this.#write(SYNCHRONIZED_OUTPUT_DISABLE);
		}
	}

	#hookStream(stream) {
		if (!stream || this.#hookedStreams.has(stream) || typeof stream.write !== 'function') {
			return;
		}

		if (activeHooksPerStream.has(stream)) {
			return;
		}

		const originalWrite = stream.write;
		const hookedWrite = (...writeArguments) => this.#hookedWrite(stream, originalWrite, writeArguments);
		this.#hookedStreams.set(stream, {originalWrite, hookedWrite});
		activeHooksPerStream.add(stream);
		stream.write = hookedWrite;
	}

	#installHook() {
		if (!this.#isInteractive || this.#hookedStreams.size > 0) {
			return;
		}

		const streamsToHook = new Set([this.#stream]);

		if (this.#stream === process.stdout || this.#stream === process.stderr) {
			if (isInteractive(process.stdout)) {
				streamsToHook.add(process.stdout);
			}

			if (isInteractive(process.stderr)) {
				streamsToHook.add(process.stderr);
			}
		}

		for (const stream of streamsToHook) {
			this.#hookStream(stream);
		}
	}

	#uninstallHook() {
		for (const [stream, hookInfo] of this.#hookedStreams) {
			if (stream.write === hookInfo.hookedWrite) {
				stream.write = hookInfo.originalWrite;
			}

			activeHooksPerStream.delete(stream);
		}

		this.#hookedStreams.clear();
	}

	#hookedWrite(stream, originalWrite, writeArguments) {
		const [chunk, encoding, callback] = writeArguments;
		let resolvedEncoding = encoding;
		let resolvedCallback = callback;

		if (typeof resolvedEncoding === 'function') {
			resolvedCallback = resolvedEncoding;
			resolvedEncoding = undefined;
		}

		if (this.#isInternalWrite || !this.isSpinning) {
			return originalWrite.call(stream, chunk, resolvedEncoding, resolvedCallback);
		}

		if (this.#lines > 0) {
			this.clear();
		}

		const chunkString = this.#stringifyChunk(chunk, resolvedEncoding);
		const chunkTerminatesLine = chunkString.at(-1) === '\n';
		const writeResult = originalWrite.call(stream, chunk, resolvedEncoding, resolvedCallback);

		if (chunkTerminatesLine) {
			this.#isDeferringRender = false;
		} else if (chunkString !== '') {
			this.#isDeferringRender = true;
		}

		if (this.isSpinning && !this.#isDeferringRender) {
			this.#render();
		}

		return writeResult;
	}

	start(text) {
		if (text) {
			this.#text = text;
		}

		if (this.isSpinning) {
			return this;
		}

		this.#isSpinning = true;
		this.#hideCursor();
		this.#installHook();
		this.#render();
		this.#subscribeToProcessEvents();

		// Only start the timer in interactive mode
		if (this.#isInteractive) {
			this.#timer = setInterval(() => {
				this.#render();
			}, this.#interval);
		}

		return this;
	}

	stop(finalText) {
		if (!this.isSpinning) {
			return this;
		}

		const shouldWriteNewline = this.#isDeferringRender;
		this.#isSpinning = false;
		if (this.#timer) {
			clearInterval(this.#timer);
			this.#timer = undefined;
		}

		this.#isDeferringRender = false;
		this.#uninstallHook();
		this.#showCursor();
		this.clear();
		this.#unsubscribeFromProcessEvents();

		if (finalText) {
			const prefix = shouldWriteNewline ? '\n' : '';
			this.#stream.write(`${prefix}${finalText}\n`);
		}

		return this;
	}

	#symbolStop(symbol, text) {
		return this.stop(`${symbol} ${text ?? this.#text}`);
	}

	success(text) {
		return this.#symbolStop(successSymbol, text);
	}

	error(text) {
		return this.#symbolStop(errorSymbol, text);
	}

	warning(text) {
		return this.#symbolStop(warningSymbol, text);
	}

	info(text) {
		return this.#symbolStop(infoSymbol, text);
	}

	get isSpinning() {
		return this.#isSpinning;
	}

	get text() {
		return this.#text;
	}

	set text(value) {
		this.#text = value ?? '';
		this.#render();
	}

	get color() {
		return this.#color;
	}

	set color(value) {
		this.#color = value;
		this.#render();
	}

	clear() {
		if (!this.#isInteractive) {
			return this;
		}

		if (this.#lines === 0) {
			return this;
		}

		this.#internalWrite(() => {
			this.#stream.cursorTo(0);

			for (let index = 0; index < this.#lines; index++) {
				if (index > 0) {
					this.#stream.moveCursor(0, -1);
				}

				this.#stream.clearLine(1);
			}
		});

		this.#lines = 0;

		return this;
	}

	#render() {
		if (this.#isDeferringRender) {
			return;
		}

		const useSynchronizedOutput = this.#isInteractive;
		// Ensure we only update the spinner frame at the wanted interval,
		// even if the frame method is called more often.
		const now = Date.now();
		if (this.#currentFrame === -1 || now - this.#lastSpinnerFrameTime >= this.#interval) {
			this.#currentFrame = ++this.#currentFrame % this.#frames.length;
			this.#lastSpinnerFrameTime = now;
		}

		const applyColor = yoctocolors[this.#color] ?? yoctocolors.cyan;
		const frame = this.#frames[this.#currentFrame];
		let string = `${applyColor(frame)} ${this.#text}`;

		if (!this.#isInteractive) {
			string += '\n';
		}

		if (useSynchronizedOutput) {
			this.#withSynchronizedOutput(() => {
				this.clear();
				this.#write(string);
			});
		} else {
			this.#write(string);
		}

		if (this.#isInteractive) {
			this.#lines = this.#lineCount(string);
		}
	}

	#write(text) {
		this.#internalWrite(() => {
			this.#stream.write(text);
		});
	}

	#lineCount(text) {
		const width = this.#stream.columns ?? 80;
		const lines = stripVTControlCharacters(text).split('\n');

		let lineCount = 0;
		for (const line of lines) {
			lineCount += Math.max(1, Math.ceil(line.length / width));
		}

		return lineCount;
	}

	#hideCursor() {
		if (this.#isInteractive) {
			this.#write('\u001B[?25l');
		}
	}

	#showCursor() {
		if (this.#isInteractive) {
			this.#write('\u001B[?25h');
		}
	}

	#subscribeToProcessEvents() {
		if (!this.#handleSignals) {
			return;
		}

		process.once('SIGINT', this.#exitHandlerBound);
		process.once('SIGTERM', this.#exitHandlerBound);
	}

	#unsubscribeFromProcessEvents() {
		if (!this.#handleSignals) {
			return;
		}

		process.off('SIGINT', this.#exitHandlerBound);
		process.off('SIGTERM', this.#exitHandlerBound);
	}

	#exitHandler(signal) {
		if (this.isSpinning) {
			this.stop();
		}

		// SIGINT: 128 + 2
		// SIGTERM: 128 + 15
		const exitCode = signal === 'SIGINT' ? 130 : (signal === 'SIGTERM' ? 143 : 1);
		process.exit(exitCode);
	}
}

export default function yoctoSpinner(options) {
	return new YoctoSpinner(options);
}
