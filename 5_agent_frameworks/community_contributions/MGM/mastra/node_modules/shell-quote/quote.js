'use strict';

var OPS = [
	'||',
	'&&',
	';;',
	'|&',
	'<(',
	'<<<',
	'>>',
	'>&',
	'<&',
	'&',
	';',
	'(',
	')',
	'|',
	'<',
	'>'
];
var LINE_TERMINATORS = /[\n\r\u2028\u2029]/;
var GLOB_SHELL_SPECIAL = /[\s#!"$&'():;<=>@\\^`|]/g;

module.exports = function quote(xs) {
	return xs.map(function (s) {
		if (s === '') {
			return '\'\'';
		}
		if (s && typeof s === 'object') {
			if (s.op === 'glob') {
				if (typeof s.pattern !== 'string') {
					throw new TypeError('glob token requires a string `pattern`');
				}
				if (LINE_TERMINATORS.test(s.pattern)) {
					throw new TypeError('glob `pattern` must not contain line terminators');
				}
				return s.pattern.replace(GLOB_SHELL_SPECIAL, '\\$&');
			}
			if (typeof s.op === 'string') {
				if (OPS.indexOf(s.op) < 0) {
					throw new TypeError('invalid `op` value: ' + JSON.stringify(s.op));
				}
				return s.op.replace(/[\s\S]/g, '\\$&');
			}
			if (typeof s.comment === 'string') {
				if (LINE_TERMINATORS.test(s.comment)) {
					throw new TypeError('`comment` must not contain line terminators');
				}
				return '#' + s.comment;
			}
			throw new TypeError('unrecognized object token shape');
		}
		if ((/["\s\\]/).test(s) && !(/'/).test(s)) {
			return "'" + s.replace(/(['])/g, '\\$1') + "'";
		}
		if ((/["'\s]/).test(s)) {
			return '"' + s.replace(/(["\\$`!])/g, '\\$1') + '"';
		}
		return String(s).replace(/([A-Za-z]:)?([#!"$&'()*,:;<=>?@[\\\]^`{|}])/g, '$1\\$2');
	}).join(' ');
};
