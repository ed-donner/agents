<p align="center">
<img src="https://cdn.jsdelivr.net/gh/hexagon/croner@master/croner.png" alt="Croner" width="150" height="150"><br>
Trigger functions or evaluate cron expressions in JavaScript or TypeScript. No dependencies. All features. Node. Deno. Bun. Browser. <br><br>Try it live on <a href="https://jsfiddle.net/hexag0n/hoa8kwsb/">jsfiddle</a>, and check out the full documentation on <a href="https://croner.56k.guru">croner.56k.guru</a>.<br>
</p>

# Croner - Cron for JavaScript and TypeScript

[![npm version](https://badge.fury.io/js/croner.svg)](https://badge.fury.io/js/croner) [![JSR](https://jsr.io/badges/@hexagon/croner)](https://jsr.io/@hexagon/croner) [![NPM Downloads](https://img.shields.io/npm/dw/croner.svg)](https://www.npmjs.org/package/croner)
![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen) [![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Hexagon/croner/blob/master/LICENSE)

*   Trigger functions in JavaScript using [Cron](https://en.wikipedia.org/wiki/Cron#CRON_expression) syntax.
*   Evaluate cron expressions and get a list of upcoming run times.
*   Supports seconds and year fields, `L` (last), `W` (weekday), `#` (nth occurrence), and `+` (AND logic).
*   Works in Node.js >=18.0 (both require and import), Deno >=2.0 and Bun >=1.0.0.
*   Works in browsers as standalone, UMD or ES-module.
*   Target different [time zones](https://croner.56k.guru/usage/examples/#time-zone).
*   Built-in [overrun protection](https://croner.56k.guru/usage/examples/#overrun-protection)
*   Built-in [error handling](https://croner.56k.guru/usage/examples/#error-handling)
*   Includes [TypeScript](https://www.typescriptlang.org/) typings.
*   Support for asynchronous functions.
*   Pause, resume, or stop execution after a task is scheduled.
*   Operates in-memory, with no need for a database or configuration files.
*   Zero dependencies.

Quick examples:

```javascript
// Basic: Run a function at the interval defined by a cron expression
const job = new Cron('*/5 * * * * *', () => {
	console.log('This will run every fifth second');
});

// Enumeration: What dates do the next 100 sundays occur on?
const nextSundays = new Cron('0 0 0 * * 7').nextRuns(100);
console.log(nextSundays);

// Days left to a specific date
const msLeft = new Cron('59 59 23 24 DEC *').nextRun() - new Date();
console.log(Math.floor(msLeft/1000/3600/24) + " days left to next christmas eve");

// Run a function at a specific date/time using a non-local timezone (time is ISO 8601 local time)
// This will run 2024-01-23 00:00:00 according to the time in Asia/Kolkata
new Cron('2024-01-23T00:00:00', { timezone: 'Asia/Kolkata' }, () => { console.log('Yay!') });

// Check if a date matches a cron pattern
const mondayCheck = new Cron('0 0 0 * * MON');
console.log(mondayCheck.match('2024-01-01T00:00:00')); // true  (Monday)
console.log(mondayCheck.match('2024-01-02T00:00:00')); // false (Tuesday)

```

More [examples](https://croner.56k.guru/usage/examples/)...

## Installation

Full documentation on installation and usage is found at <https://croner.56k.guru>

> **Note**
> If you are migrating from a different library such as `cron` or `node-cron`, or upgrading from a older version of croner, see the [migration section](https://croner.56k.guru/migration/) of the manual.

Install croner using your favorite package manager or CDN, then include it in you project: 

Using Node.js or Bun

```javascript
// ESM Import ...
import { Cron } from "croner";

// ... or CommonJS Require, destructure to add type hints
const { Cron } = require("croner");
```

Using Deno

```typescript
// From deno.land/x
import { Cron } from "https://deno.land/x/croner@10.0.0/dist/croner.js";

// ... or jsr.io
import { Cron } from "jsr:@hexagon/croner@10.0.0";
```

In a webpage using the UMD-module

```html
<script src="https://cdn.jsdelivr.net/npm/croner@10/dist/croner.umd.min.js"></script>
```

## Documentation

### Signature

Cron takes three arguments

*   [pattern](#pattern)
*   [options](#options) (optional) 
*   scheduled function (optional)

```javascript
// Parameters
// - First: Cron pattern, js date object (fire once), or ISO 8601 time string (fire once)
// - Second: Options (optional)
// - Third: Function run trigger (optional)
const job = new Cron("* * * * * *", { maxRuns: 1 }, () => {} );

// If function is omitted in constructor, it can be scheduled later
job.schedule(job, /* optional */ context) => {});
```

The job will be sceduled to run at next matching time unless you supply option `{ paused: true }`. The `new Cron(...)` constructor will return a Cron instance, later called `job`, which have a couple of methods and properties listed below.

#### Status

```javascript
job.nextRun( /*optional*/ startFromDate );	// Get a Date object representing the next run.
job.nextRuns(10, /*optional*/ startFromDate ); // Get an array of Dates, containing the next n runs.
job.previousRuns(10, /*optional*/ referenceDate ); // Get an array of Dates, containing previous n scheduled runs.
job.msToNext( /*optional*/ startFromDate ); // Get the milliseconds left until the next execution.
job.currentRun(); 		// Get a Date object showing when the current (or last) run was started.
job.previousRun( ); 		// Get a Date object showing when the previous job was started.

job.match( date ); 		// Check if a Date object or date string matches the cron pattern (true or false).

job.isRunning(); 	// Indicates if the job is scheduled and not paused or killed (true or false).
job.isStopped(); 	// Indicates if the job is permanently stopped using `stop()` (true or false).
job.isBusy(); 		// Indicates if the job is currently busy doing work (true or false).

job.getPattern(); 	// Returns the original pattern string
job.getOnce(); 		// Returns the original run-once date (Date or null)
```

#### Control functions

```javascript
job.trigger();		// Force a trigger instantly
job.pause();		// Pause trigger
job.resume();		// Resume trigger
job.stop();		// Stop the job completely. It is not possible to resume after this.
				// Note that this also removes named jobs from the exported `scheduledJobs` array.
```

#### Properties

```javascript
job.name 			// Optional job name, populated if a name were passed to options
```

#### Options

| Key          | Default value  | Data type      | Remarks                               |
|--------------|----------------|----------------|---------------------------------------|
| name         | undefined      | String         | If you specify a name for the job, Croner will keep a reference to the job in the exported array `scheduledJobs`. The reference will be removed on `.stop()`. |
| maxRuns      | Infinite       | Number         |                                       |
| catch	       | false          | Boolean\|Function        | Catch unhandled errors in triggered function. Passing `true` will silently ignore errors. Passing a callback function will trigger this callback on error. |
| timezone     | undefined      | String         | Timezone in Europe/Stockholm format   |
| startAt      | undefined      | String         | ISO 8601 formatted datetime (2021-10-17T23:43:00)<br>in local time (according to timezone parameter if passed) |
| stopAt       | undefined      | String         | ISO 8601 formatted datetime (2021-10-17T23:43:00)<br>in local time (according to timezone parameter if passed) |
| interval     | 0              | Number         | Minimum number of seconds between triggers. |
| paused       | false          | Boolean        | If the job should be paused from start. |
| context      | undefined      | Any            | Passed as the second parameter to triggered function |
| domAndDow    | false          | boolean        | Combine day-of-month and day-of-week using true = AND, false = OR (default) |
| legacyMode   | (deprecated)   | boolean        | **Deprecated:** Use `domAndDow` instead. Inverse of `domAndDow` (legacyMode: true = domAndDow: false). |
| unref        | false          | boolean        | Setting this to true unrefs the internal timer, which allows the process to exit even if a cron job is running. |
| utcOffset    | undefined      | number        | Schedule using a specific utc offset in minutes. This does not take care of daylight savings time, you probably want to use option `timezone` instead. |
| protect      | undefined      | boolean\|Function | Enabled over-run protection. Will block new triggers as long as an old trigger is in progress. Pass either `true` or a callback function to enable |
| alternativeWeekdays | false   | boolean        | Enable Quartz-style weekday numbering (1=Sunday, 2=Monday, ..., 7=Saturday). When false (default), uses standard cron format (0=Sunday, 1=Monday, ..., 6=Saturday). |

> **Warning**
> Unreferencing timers (option `unref`) is only supported by Node.js and Deno. 
> Browsers have not yet implemented this feature, and it does not make sense to use it in a browser environment.

#### Pattern

Croner uses [Vixie Cron](https://en.wikipedia.org/wiki/Cron#CRON_expression) based expressions with the following powerful extensions:

```javascript
// ┌──────────────── (optional) second (0 - 59)
// │ ┌────────────── minute (0 - 59)
// │ │ ┌──────────── hour (0 - 23)
// │ │ │ ┌────────── day of month (1 - 31)
// │ │ │ │ ┌──────── month (1 - 12, JAN-DEC)
// │ │ │ │ │ ┌────── day of week (0 - 6, SUN-Mon) 
// │ │ │ │ │ │       (0 to 6 are Sunday to Saturday; 7 is Sunday, the same as 0)
// │ │ │ │ │ │ ┌──── (optional) year (1 - 9999)
// │ │ │ │ │ │ │
// * * * * * * *
```

*   **Optional second and year fields** for enhanced precision:
	-   6-field format: `SECOND MINUTE HOUR DAY-OF-MONTH MONTH DAY-OF-WEEK`
	-   7-field format: `SECOND MINUTE HOUR DAY-OF-MONTH MONTH DAY-OF-WEEK YEAR`
	-   Supported year range: 1-9999

*   **Advanced calendar modifiers**:
	-   *L*: Last day of month or last occurrence of a weekday. `L` in day-of-month = last day of month; `5#L` or `FRI#L` = last Friday of the month.
	-	*W*: Nearest weekday. `15W` triggers on the weekday closest to the 15th (moves to Friday if 15th is Saturday, Monday if 15th is Sunday). Won't cross month boundaries.
	-	*#*: Nth occurrence of a weekday. `5#2` = second Friday; `MON#1` = first Monday of the month.

*   **Enhanced logical control**:
	-   *+*: Explicit AND logic modifier. Prefix the day-of-week field with `+` to require both day-of-month AND day-of-week to match. Example: `0 12 1 * +MON` only triggers when the 1st is also a Monday.
	-   *?*: Wildcard alias (behaves identically to `*`). **Non-portable**: Its use is discouraged in patterns intended for cross-system use. Supported in all fields for compatibility, but primarily meaningful in day-of-month and day-of-week fields.
	-   Proper DST handling: Jobs scheduled during DST gaps are skipped; jobs in DST overlaps run once at first occurrence.

*   Croner allows you to pass a JavaScript Date object or an ISO 8601 formatted string as a pattern. The scheduled function will trigger at the specified date/time and only once. If you use a timezone different from the local timezone, you should pass the ISO 8601 local time in the target location and specify the timezone using the options (2nd parameter).

*   By default, Croner uses OR logic for day-of-month and day-of-week. Example: `0 20 1 * MON` triggers on the 1st of the month OR on Mondays. Use the `+` modifier (`0 20 1 * +MON`) or `{ domAndDow: true }` for AND logic. For more information, see issue [#53](https://github.com/Hexagon/croner/issues/53).

| Field        | Required | Allowed values | Allowed special characters | Remarks                               |
|--------------|----------|----------------|----------------------------|---------------------------------------|
| Seconds      | Optional | 0-59           | * , - / ?                  | Optional, defaults to 0    |
| Minutes      | Yes      | 0-59           | * , - / ?                  |                                       |
| Hours        | Yes      | 0-23           | * , - / ?                  |                                       |
| Day of Month | Yes      | 1-31           | * , - / ? L W              | L = last day, W = nearest weekday     |
| Month        | Yes      | 1-12 or JAN-DEC| * , - / ?                  |                                       |
| Day of Week  | Yes      | 0-7 or SUN-MON | * , - / ? L # +            | 0 and 7 = Sunday (standard mode)<br>1-7 = Sunday-Saturday (Quartz mode with `alternativeWeekdays: true`)<br># = nth occurrence (e.g. MON#2)<br>+ = AND logic modifier |
| Year         | Optional | 1-9999         | * , - /                    | Optional, defaults to *    |

> **Note**
> Weekday and month names are case-insensitive. Both `MON` and `mon` work.
> When using `L` in the Day of Week field with a range, it affects all specified weekdays. For example, `5-6#L` means the last Friday and Saturday in the month.
> The `#` character specifies the "nth" weekday of the month. For example, `5#2` = second Friday, `MON#1` = first Monday.
> The `W` character operates within the current month and won't cross month boundaries. If the 1st is a Saturday, `1W` matches Monday the 3rd.
> The `+` modifier (OCPS 1.4) enforces AND logic: `0 12 1 * +MON` only runs when the 1st is also a Monday.
> **Quartz mode**: Enable `alternativeWeekdays: true` to use Quartz-style weekday numbering (1=Sunday, 2=Monday, ..., 7=Saturday) instead of the standard format (0=Sunday, 1=Monday, ..., 6=Saturday). This is useful for compatibility with Quartz cron expressions.

**Predefined schedule nicknames** are supported:

| Nickname | Description |
| -------- | ----------- |
| \@yearly / \@annually | Run once a year, i.e.  "0 0 1 1 *". |
| \@monthly | Run once a month, i.e. "0 0 1 * *". |
| \@weekly | Run once a week, i.e.  "0 0 * * 0". |
| \@daily / \@midnight | Run once a day, i.e.   "0 0 * * *". |
| \@hourly | Run once an hour, i.e. "0 * * * *". |

## Why another JavaScript cron implementation

Because the existing ones are not good enough. They have serious bugs, use bloated dependencies, do not work in all environments, and/or simply do not work as expected.

For example, some popular alternatives include large datetime libraries as dependencies, which significantly increases bundle size. Croner has zero dependencies and a much smaller footprint, making it ideal for applications where bundle size matters.

|                           | croner              | cronosjs            | node-cron | cron                      | node-schedule       |
|---------------------------|:-------------------:|:-------------------:|:---------:|:-------------------------:|:-------------------:|
| **Platforms**                                                                                                                        |
| Node.js (CommonJS)                   |          ✓          |          ✓          |     ✓     |           ✓               |          ✓          |
| Browser (ESMCommonJS)                  |          ✓          |          ✓          |           |                           |                     |
| Deno (ESM)                     |          ✓          |                     |           |                           |                     |
| **Features**                                                                                                                        |
| Over-run protection  |          ✓          |                    |              |                            |                    |
| Error handling  |          ✓          |                    |              |                            |          ✓          |
| Typescript typings        |          ✓          |         ✓            |           |            ✓              |                     |
| Unref timers (optional)    |          ✓          |                     |                     |          ✓          |                     |
| dom-OR-dow                |          ✓          |          ✓          |     ✓     |           ✓               |          ✓          |
| dom-AND-dow (optional)    |          ✓          |                     |           |                           |                     |
| Next run                  |          ✓          |          ✓          |           |           ✓              |           ✓         |
| Next n runs               |          ✓          |          ✓          |           |           ✓               |                     |
| Timezone                  |          ✓          |           ✓         |     ✓       |        ✓                   |         ✓            |
| Minimum interval          |          ✓          |                     |              |                            |                      |
| Controls (stop/resume)    |          ✓          |           ✓         |     ✓        |        ✓                   |         ✓           |   
| Range (0-13)   |          ✓          |          ✓          |     ✓        |        ✓                   |         ✓           |
| Stepping (*/5)   |          ✓          |          ✓          |     ✓        |        ✓                   |         ✓           |
| Seconds field  |          ✓          |                     |              |                            |                    |
| Year field  |          ✓          |                     |              |                            |                    |
| Last day of month (L)  |          ✓          |          ✓          |              |                            |                    |
| Nth weekday of month (#)     |          ✓          |           ✓          |           |                           |                     |
| Nearest weekday (W)  |          ✓          |          ✓          |              |                            |                    |
| AND logic modifier (+)  |          ✓          |                     |              |                            |                    |

<details>
  <summary>In depth comparison of various libraries</summary>
  
|                           | croner              | cronosjs            | node-cron | cron                      | node-schedule       |
|---------------------------|:-------------------:|:-------------------:|:---------:|:-------------------------:|:-------------------:|
| **Size**                                                                                                                        |
| Minified size (KB)        | 22.7                | 14.9            | 20.1      | 93.7 :warning:                      | 107.8 :warning:                |
| Bundlephobia  minzip (KB) | 6.8                 | 5.1                 | 6.1       |                   28.2 | 31.2 :warning:             |
| Dependencies              |                   0 |                   0 |         1 |                         1 |                   3 :warning: |
| **Popularity**                                                                                                                        |
| Downloads/week [^1]        | 2019K                | 31K                 | 447K      | 1366K                     | 1046K                |
| **Quality**                                                                                                                        |
| Issues [^1]                |                   0 |                   2 |   133 :warning: |                 13 |    145 :warning: |
| Code coverage              |                   99%  | 98%                    | 100%                | 81%                              | 94%                 |
| **Performance**                                                                                                                        |
| Ops/s `1 2 3 4 5 6`         | 160 651                    | 55 593                    | N/A :x:          | 6 313 :warning:      | 2 726 :warning:                    |
| Ops/s `0 0 0 29 2 *`         | 176 714                    | 67 920                    | N/A :x:          | 3 104 :warning:      | 737 :warning:                    |
| **Tests**                 | **11/11**             | **10/11**            | **0/11** [^4] :question:    |  **7/11** :warning:                  | **9/11**             |

> **Note**
> *   Table last updated at 2023-10-10
> *   node-cron has no interface to predict when the function will run, so tests cannot be carried out.
> *   All tests and benchmarks were carried out using [https://github.com/Hexagon/cron-comparison](https://github.com/Hexagon/cron-comparison)

[^1]: As of 2023-10-10
[^2]: Requires support for L-modifier
[^3]: In dom-AND-dow mode, only supported by croner at the moment.
[^4]: Node-cron has no way of showing next run time.

</details>

## Development

### Master branch

![Node.js CI](https://github.com/Hexagon/croner/workflows/Node.js%20CI/badge.svg?branch=master) ![Deno CI](https://github.com/Hexagon/croner/workflows/Deno%20CI/badge.svg?branch=master) ![Bun CI](https://github.com/Hexagon/croner/workflows/Bun%20CI/badge.svg?branch=master) 

This branch contains the latest stable code, released on npm's default channel `latest`. You can install the latest stable revision by running the command below.

```
npm install croner --save
```

### Dev branch

![Node.js CI](https://github.com/Hexagon/croner/workflows/Node.js%20CI/badge.svg?branch=dev) ![Deno CI](https://github.com/Hexagon/croner/workflows/Deno%20CI/badge.svg?branch=dev) ![Bun CI](https://github.com/Hexagon/croner/workflows/Bun%20CI/badge.svg?branch=dev) 

This branch contains code currently being tested, and is released at channel `dev` on npm. You can install the latest revision of the development branch by running the command below.

```
npm install croner@dev
```

> **Warning**
> Expect breaking changes if you do not pin to a specific version.

A list of fixes and features currently released in the `dev` branch is available [here](https://github.com/Hexagon/croner/issues?q=is%3Aopen+is%3Aissue+label%3Areleased-in-dev)

## Contributing & Support

Croner is founded and actively maintained by Hexagon. If you find value in Croner and want to contribute:

- Code Contributions: See our [Contribution Guide](https://croner.56k.guru/contributing/) for details on how to contribute code.

- Sponsorship and Donations: See [github.com/sponsors/hexagon](https://github.com/sponsors/hexagon)

Your trust, support, and contributions drive the project. Every bit, irrespective of its size, is deeply appreciated.

## License

MIT License
