# bare-url

WHATWG URL implementation for JavaScript, built on <https://github.com/holepunchto/liburl>. Provides `URL` and `URLSearchParams` classes compatible with the WHATWG URL Standard.

```
npm i bare-url
```

## Usage

```js
const { URL, URLSearchParams } = require('bare-url')

const url = new URL('https://example.com/path?foo=bar#hash')

console.log(url.hostname) // 'example.com'
console.log(url.pathname) // '/path'
console.log(url.searchParams.get('foo')) // 'bar'
```

To register `URL` and `URLSearchParams` as globals:

```js
require('bare-url/global')
```

## API

#### `const url = new URL(input[, base])`

Parse `input` as a URL. If `base` is provided, `input` is resolved relative to `base`. Throws if `input` is not a valid URL.

#### `url.href`

The full serialized URL string. Setting this property reparses the URL.

#### `url.protocol`

The URL scheme followed by `':'`, e.g. `'https:'`.

#### `url.username`

The username portion of the URL, or an empty string.

#### `url.password`

The password portion of the URL, or an empty string.

#### `url.host`

The hostname and port, e.g. `'example.com:8080'`.

#### `url.hostname`

The hostname without the port.

#### `url.port`

The port as a string, or an empty string if not present.

#### `url.pathname`

The path portion of the URL.

#### `url.search`

The query string including the leading `'?'`, or an empty string.

#### `url.searchParams`

A `URLSearchParams` object for the query string. Mutations to the params are reflected in the URL.

#### `url.hash`

The fragment including the leading `'#'`, or an empty string.

#### `url.toString()`

Returns the serialized URL string. Equivalent to `url.href`.

#### `url.toJSON()`

Returns the serialized URL string. Suitable for JSON serialization.

#### `const params = new URLSearchParams([init])`

Create a new `URLSearchParams` instance. `init` may be a query string, an iterable of `[name, value]` pairs, or an object of key-value pairs.

#### `params.size`

The total number of search parameters.

#### `params.append(name, value)`

Append a new `name`/`value` pair.

#### `params.delete(name[, value])`

Remove all pairs with `name`. If `value` is provided, only pairs with both the matching `name` and `value` are removed.

#### `params.get(name)`

Return the first value for `name`, or `null` if not present.

#### `params.getAll(name)`

Return all values for `name` as an array.

#### `params.has(name[, value])`

Return `true` if a pair with `name` exists. If `value` is provided, the pair must also match `value`.

#### `params.set(name, value)`

Set the value for `name`, replacing any existing pairs with that name.

#### `params.toString()`

Return the serialized query string without the leading `'?'`.

#### `params.toJSON()`

Return the parameters as an array of `[name, value]` pairs.

#### `URL.isURL(value)`

Return `true` if `value` is a `URL` instance.

#### `URLSearchParams.isURLSearchParams(value)`

Return `true` if `value` is a `URLSearchParams` instance.

#### `const url = URL.parse(input[, base])`

Parse `input` as a URL without throwing. Returns a `URL` instance on success, or `null` on failure.

#### `const valid = URL.canParse(input[, base])`

Return `true` if `input` can be parsed as a valid URL, optionally relative to `base`.

#### `const pathname = URL.fileURLToPath(url)`

Convert a `file:` URL to a platform-specific file path. `url` may be a `URL` instance or a string. Throws if the URL does not use the `file:` protocol or contains invalid path characters.

#### `const url = URL.pathToFileURL(pathname)`

Convert a platform-specific file path to a `file:` URL.

#### `const href = URL.format(parts)`

Format a URL from individual `parts`:

```js
parts = {
  protocol,
  auth,
  host,
  hostname,
  port,
  pathname,
  search,
  query,
  hash,
  slashes
}
```

All properties are optional. If `host` is provided, `hostname` and `port` are ignored. If `search` is provided, `query` is ignored. Set `slashes` to `true` to include `'//'` after the protocol.

## License

Apache-2.0
