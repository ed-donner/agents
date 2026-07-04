import { includes } from './string-utils'
import { isFunction, isUndefined } from './type-utils'

/**
 * this device detection code is (at time of writing) about 3% of the size of the entire library
 * this is mostly because the identifiers user in regexes and results can't be minified away since
 * they have meaning
 *
 * so, there are some pre-uglifying choices in the code to help reduce the size
 * e.g. many repeated strings are stored as variables and then old-fashioned concatenated together
 *
 * TL;DR here be dragons
 */
const FACEBOOK = 'Facebook'
const MOBILE = 'Mobile'
const IOS = 'iOS'
const ANDROID = 'Android'
const TABLET = 'Tablet'
const ANDROID_TABLET = ANDROID + ' ' + TABLET
const IPAD = 'iPad'
const APPLE = 'Apple'
const APPLE_WATCH = APPLE + ' Watch'
const SAFARI = 'Safari'
const BLACKBERRY = 'BlackBerry'
const SAMSUNG = 'Samsung'
const SAMSUNG_BROWSER = SAMSUNG + 'Browser'
const SAMSUNG_INTERNET = SAMSUNG + ' Internet'
const CHROME = 'Chrome'
const CHROME_OS = CHROME + ' OS'
const CHROME_IOS = CHROME + ' ' + IOS
const INTERNET_EXPLORER = 'Internet Explorer'
const INTERNET_EXPLORER_MOBILE = INTERNET_EXPLORER + ' ' + MOBILE
const OPERA = 'Opera'
const OPERA_MINI = OPERA + ' Mini'
const EDGE = 'Edge'
const MICROSOFT_EDGE = 'Microsoft ' + EDGE
const FIREFOX = 'Firefox'
const FIREFOX_IOS = FIREFOX + ' ' + IOS
const NINTENDO = 'Nintendo'
const PLAYSTATION = 'PlayStation'
const XBOX = 'Xbox'
const ANDROID_MOBILE = ANDROID + ' ' + MOBILE
const MOBILE_SAFARI = MOBILE + ' ' + SAFARI
const WINDOWS = 'Windows'
const WINDOWS_PHONE = WINDOWS + ' Phone'
const NOKIA = 'Nokia'
const OUYA = 'Ouya'
const GENERIC = 'Generic'
const GENERIC_MOBILE = GENERIC + ' ' + MOBILE.toLowerCase()
const GENERIC_TABLET = GENERIC + ' ' + TABLET.toLowerCase()
const KONQUEROR = 'Konqueror'
const OCULUS_BROWSER = 'Oculus Browser'
const VIVALDI = 'Vivaldi'
const YANDEX = 'Yandex'
const WHALE = 'Whale'
const DUCKDUCKGO = 'DuckDuckGo'
const PALE_MOON = 'Pale Moon'
const WATERFOX = 'Waterfox'
const BRAVE = 'Brave'
const GOOGLE_SEARCH_APP = 'Google Search App'

const BROWSER_VERSION_REGEX_SUFFIX = '(\\d+(\\.\\d+)?)'
const DEFAULT_BROWSER_VERSION_REGEX = new RegExp('Version/' + BROWSER_VERSION_REGEX_SUFFIX)

/**
 * Hints from sources outside the User-Agent string. These let us identify Brave
 * on desktop / Android — Chromium-based with no UA marker, but it exposes
 * `navigator.brave`. (Brave on iOS is detected via its `Brave/X` UA marker —
 * WebKit doesn't expose `navigator.brave` — so no hint is needed there.)
 */
export interface BrowserDetectionHints {
  // Set to `true` when `navigator.brave` exists. This is the sync detection
  // signal Brave recommends. Not available on iOS — see UA fallback below.
  brave?: boolean
}

function browserFromHints(hints: BrowserDetectionHints | undefined): string | null {
  if (hints?.brave) {
    return BRAVE
  }
  return null
}

/**
 * Opt-in tweaks to UA-string detection. These change how existing traffic is
 * attributed, so the host SDK gates them (behind its `2026-05-30` config
 * defaults) rather than enabling them unconditionally — turning one on
 * reattributes browsers that were previously reported as something else.
 */
export interface BrowserDetectionOptions {
  // Surface the Google Search App as its own browser via its `GSA/` UA marker
  // instead of the underlying webview (Mobile Safari on iOS, Chrome on Android).
  detectGoogleSearchApp?: boolean
}

const XBOX_REGEX = new RegExp(XBOX, 'i')
const PLAYSTATION_REGEX = new RegExp(PLAYSTATION + ' \\w+', 'i')
const NINTENDO_REGEX = new RegExp(NINTENDO + ' \\w+', 'i')
const BLACKBERRY_REGEX = new RegExp(BLACKBERRY + '|PlayBook|BB10', 'i')

const windowsVersionMap: Record<string, string> = {
  'NT3.51': 'NT 3.11',
  'NT4.0': 'NT 4.0',
  '5.0': '2000',
  '5.1': 'XP',
  '5.2': 'XP',
  '6.0': 'Vista',
  '6.1': '7',
  '6.2': '8',
  '6.3': '8.1',
  '6.4': '10',
  '10.0': '10',
}

/**
 * Safari detection turns out to be complicated. For e.g. https://stackoverflow.com/a/29696509
 * We can be slightly loose because some options have been ruled out (e.g. firefox on iOS)
 * before this check is made
 */
function isSafari(userAgent: string): boolean {
  return includes(userAgent, SAFARI) && !includes(userAgent, CHROME) && !includes(userAgent, ANDROID)
}

const safariCheck = (ua: string, vendor?: string) => (vendor && includes(vendor, APPLE)) || isSafari(ua)

/**
 * This function detects which browser is running this script.
 * The order of the checks are important since many user agents
 * include keywords used in later checks.
 *
 * `hints` is an optional bag of out-of-band signals (`navigator.brave`) used to
 * detect browsers that intentionally do not identify themselves in the UA
 * string. When omitted, only UA-string detection runs — preserving the previous
 * behaviour.
 *
 * `options` toggles opt-in UA-detection tweaks (see `BrowserDetectionOptions`).
 */
export const detectBrowser = function (
  user_agent: string,
  vendor: string | undefined,
  hints?: BrowserDetectionHints,
  options?: BrowserDetectionOptions
): string {
  vendor = vendor || '' // vendor is undefined for at least IE9

  // Out-of-band signals win over UA sniffing because desktop Brave is
  // deliberately invisible in the UA string and would otherwise be
  // misdetected as Chrome.
  const fromHints = browserFromHints(hints)
  if (fromHints) {
    return fromHints
  }

  // The Google Search App embeds a platform webview, so its UA otherwise looks
  // like Mobile Safari (iOS) or Chrome (Android). The `GSA/` marker is present
  // on every platform, so checking it first lets us attribute GSA consistently
  // — it must precede the Chrome and Safari branches that would match instead.
  if (options?.detectGoogleSearchApp && includes(user_agent, 'GSA/')) {
    return GOOGLE_SEARCH_APP
  }

  if (includes(user_agent, ' OPR/') && includes(user_agent, 'Mini')) {
    return OPERA_MINI
  } else if (includes(user_agent, ' OPR/')) {
    return OPERA
  } else if (BLACKBERRY_REGEX.test(user_agent)) {
    return BLACKBERRY
  } else if (includes(user_agent, 'IE' + MOBILE) || includes(user_agent, 'WPDesktop')) {
    return INTERNET_EXPLORER_MOBILE
  }
  // Oculus Browser (Meta Quest) is Chromium-based, so its UA includes
  // `OculusBrowser` alongside `Chrome` (and sometimes `SamsungBrowser`).
  // We must check for it before those, otherwise it would be misdetected.
  // See https://github.com/PostHog/posthog-js/issues/3574
  else if (includes(user_agent, 'OculusBrowser')) {
    return OCULUS_BROWSER
  }
  // https://developer.samsung.com/internet/user-agent-string-format
  else if (includes(user_agent, SAMSUNG_BROWSER)) {
    return SAMSUNG_INTERNET
  } else if (includes(user_agent, EDGE) || includes(user_agent, 'Edg/')) {
    return MICROSOFT_EDGE
  }
  // Chromium forks that DO stamp themselves into the UA. These must be
  // checked before Chrome because their UA also contains `Chrome/`.
  else if (includes(user_agent, VIVALDI + '/')) {
    return VIVALDI
  } else if (includes(user_agent, 'YaBrowser/')) {
    return YANDEX
  } else if (includes(user_agent, WHALE + '/')) {
    return WHALE
  } else if (includes(user_agent, DUCKDUCKGO + '/') || includes(user_agent, 'Ddg/')) {
    return DUCKDUCKGO
  } else if (includes(user_agent, 'FBIOS')) {
    return FACEBOOK + ' ' + MOBILE
  } else if (includes(user_agent, 'UCWEB') || includes(user_agent, 'UCBrowser')) {
    return 'UC Browser'
  } else if (includes(user_agent, 'CriOS')) {
    return CHROME_IOS // why not just Chrome?
  } else if (includes(user_agent, 'CrMo')) {
    return CHROME
  } else if (includes(user_agent, CHROME)) {
    return CHROME
  } else if (includes(user_agent, ANDROID) && includes(user_agent, SAFARI)) {
    return ANDROID_MOBILE
  } else if (includes(user_agent, 'FxiOS')) {
    return FIREFOX_IOS
  } else if (includes(user_agent.toLowerCase(), KONQUEROR.toLowerCase())) {
    return KONQUEROR
  }
  // Brave on iOS does stamp itself into the UA as `Brave/X` — desktop and
  // Android Brave intentionally do not. Must come before the Safari branch
  // because iOS Brave's UA otherwise looks like Mobile Safari.
  else if (includes(user_agent, BRAVE + '/')) {
    return BRAVE
  } else if (safariCheck(user_agent, vendor)) {
    return includes(user_agent, MOBILE) ? MOBILE_SAFARI : SAFARI
  }
  // Firefox forks that stamp themselves into the UA. Must precede the
  // generic Firefox check because they also include `Firefox/` (or `Gecko`).
  else if (includes(user_agent, 'PaleMoon/')) {
    return PALE_MOON
  } else if (includes(user_agent, WATERFOX + '/')) {
    return WATERFOX
  } else if (includes(user_agent, FIREFOX)) {
    return FIREFOX
  } else if (includes(user_agent, 'MSIE') || includes(user_agent, 'Trident/')) {
    return INTERNET_EXPLORER
  } else if (includes(user_agent, 'Gecko')) {
    return FIREFOX
  }

  return ''
}

const versionRegexes: Record<string, RegExp[]> = {
  [INTERNET_EXPLORER_MOBILE]: [new RegExp('rv:' + BROWSER_VERSION_REGEX_SUFFIX)],
  [MICROSOFT_EDGE]: [new RegExp(EDGE + '?\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [CHROME]: [new RegExp('(' + CHROME + '|CrMo)\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [CHROME_IOS]: [new RegExp('CriOS\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  'UC Browser': [new RegExp('(UCBrowser|UCWEB)\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [SAFARI]: [DEFAULT_BROWSER_VERSION_REGEX],
  [MOBILE_SAFARI]: [DEFAULT_BROWSER_VERSION_REGEX],
  [OPERA]: [new RegExp('(' + OPERA + '|OPR)\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [FIREFOX]: [new RegExp(FIREFOX + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [FIREFOX_IOS]: [new RegExp('FxiOS\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [KONQUEROR]: [new RegExp('Konqueror[:/]?' + BROWSER_VERSION_REGEX_SUFFIX, 'i')],
  // not every blackberry user agent has the version after the name
  [BLACKBERRY]: [new RegExp(BLACKBERRY + ' ' + BROWSER_VERSION_REGEX_SUFFIX), DEFAULT_BROWSER_VERSION_REGEX],
  [ANDROID_MOBILE]: [new RegExp('android\\s' + BROWSER_VERSION_REGEX_SUFFIX, 'i')],
  [SAMSUNG_INTERNET]: [new RegExp(SAMSUNG_BROWSER + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [OCULUS_BROWSER]: [new RegExp('OculusBrowser\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [VIVALDI]: [new RegExp(VIVALDI + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [YANDEX]: [new RegExp('YaBrowser\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [WHALE]: [new RegExp(WHALE + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  // Brave on iOS exposes itself as `Brave/X.X` in the UA. Desktop / Android
  // Brave don't, which is why hint-based Brave detection returns a null
  // version: we have no UA marker to parse.
  [BRAVE]: [new RegExp(BRAVE + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  // DuckDuckGo on iOS uses `Ddg/`, on Android/desktop preview it uses `DuckDuckGo/`.
  [DUCKDUCKGO]: [new RegExp('(DuckDuckGo|Ddg)\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [PALE_MOON]: [new RegExp('PaleMoon\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [WATERFOX]: [new RegExp(WATERFOX + '\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [GOOGLE_SEARCH_APP]: [new RegExp('GSA\\/' + BROWSER_VERSION_REGEX_SUFFIX)],
  [INTERNET_EXPLORER]: [new RegExp('(rv:|MSIE )' + BROWSER_VERSION_REGEX_SUFFIX)],
  Mozilla: [new RegExp('rv:' + BROWSER_VERSION_REGEX_SUFFIX)],
}

/**
 * This function detects which browser version is running this script,
 * parsing major and minor version (e.g., 42.1). User agent strings from:
 * http://www.useragentstring.com/pages/useragentstring.php
 *
 * `navigator.vendor` is passed in and used to help with detecting certain browsers
 * NB `navigator.vendor` is deprecated and not present in every browser
 */
export const detectBrowserVersion = function (
  userAgent: string,
  vendor: string | undefined,
  hints?: BrowserDetectionHints,
  options?: BrowserDetectionOptions
): number | null {
  const browser = detectBrowser(userAgent, vendor, hints, options)

  // Desktop / Android Brave has no parseable UA version, so it returns null
  // below: its `versionRegexes` entry only matches the iOS `Brave/` marker
  // (absent from a desktop Chrome UA).
  const regexes: RegExp[] | undefined = versionRegexes[browser as keyof typeof versionRegexes]
  if (isUndefined(regexes)) {
    return null
  }

  for (let i = 0; i < regexes.length; i++) {
    const regex = regexes[i]
    const matches = userAgent.match(regex)
    if (matches) {
      return parseFloat(matches[matches.length - 2])
    }
  }
  return null
}

// to avoid repeating regexes or calling them twice, we have an array of matches
// the first regex that matches uses its matcher function to return the result
const osMatchers: [
  RegExp,
  [string, string] | ((match: RegExpMatchArray | null, user_agent: string) => [string, string]),
][] = [
  [
    new RegExp(XBOX + '; ' + XBOX + ' (.*?)[);]', 'i'),
    (match) => {
      return [XBOX, (match && match[1]) || '']
    },
  ],
  [new RegExp(NINTENDO, 'i'), [NINTENDO, '']],
  [new RegExp(PLAYSTATION, 'i'), [PLAYSTATION, '']],
  [BLACKBERRY_REGEX, [BLACKBERRY, '']],
  [
    new RegExp(WINDOWS, 'i'),
    (_, user_agent) => {
      if (/Phone/.test(user_agent) || /WPDesktop/.test(user_agent)) {
        return [WINDOWS_PHONE, '']
      }
      // not all JS versions support negative lookbehind, so we need two checks here
      if (new RegExp(MOBILE).test(user_agent) && !/IEMobile\b/.test(user_agent)) {
        return [WINDOWS + ' ' + MOBILE, '']
      }
      const match = /Windows NT ([0-9.]+)/i.exec(user_agent)
      if (match && match[1]) {
        const version = match[1]
        let osVersion = windowsVersionMap[version] || ''
        if (/arm/i.test(user_agent)) {
          osVersion = 'RT'
        }
        return [WINDOWS, osVersion]
      }
      return [WINDOWS, '']
    },
  ],
  [
    /((iPhone|iPad|iPod).*?OS (\d+)_(\d+)_?(\d+)?|iPhone)/,
    (match) => {
      if (match && match[3]) {
        const versionParts = [match[3], match[4], match[5] || '0']
        return [IOS, versionParts.join('.')]
      }
      return [IOS, '']
    },
  ],
  [
    /(watch.*\/(\d+\.\d+\.\d+)|watch os,(\d+\.\d+),)/i,
    (match) => {
      // e.g. Watch4,3/5.3.8 (16U680)
      let version = ''
      if (match && match.length >= 3) {
        version = isUndefined(match[2]) ? match[3] : match[2]
      }
      return ['watchOS', version]
    },
  ],
  [
    new RegExp('(' + ANDROID + ' (\\d+)\\.(\\d+)\\.?(\\d+)?|' + ANDROID + ')', 'i'),
    (match) => {
      if (match && match[2]) {
        const versionParts = [match[2], match[3], match[4] || '0']
        return [ANDROID, versionParts.join('.')]
      }
      return [ANDROID, '']
    },
  ],
  [
    /Mac OS X (\d+)[_.](\d+)[_.]?(\d+)?/i,
    (match) => {
      const result: [string, string] = ['Mac OS X', '']
      if (match && match[1]) {
        const versionParts = [match[1], match[2], match[3] || '0']
        result[1] = versionParts.join('.')
      }
      return result
    },
  ],
  [
    /Mac/i,
    // mop up a few non-standard UAs that should match mac
    ['Mac OS X', ''],
  ],
  [/CrOS/, [CHROME_OS, '']],
  [/Linux|debian/i, ['Linux', '']],
]

export const detectOS = function (user_agent: string): [string, string] {
  for (let i = 0; i < osMatchers.length; i++) {
    const [rgex, resultOrFn] = osMatchers[i]
    const match = rgex.exec(user_agent)
    const result = match && (isFunction(resultOrFn) ? resultOrFn(match, user_agent) : resultOrFn)
    if (result) {
      return result
    }
  }
  return ['', '']
}

export const detectDevice = function (user_agent: string): string {
  if (NINTENDO_REGEX.test(user_agent)) {
    return NINTENDO
  } else if (PLAYSTATION_REGEX.test(user_agent)) {
    return PLAYSTATION
  } else if (XBOX_REGEX.test(user_agent)) {
    return XBOX
  } else if (new RegExp(OUYA, 'i').test(user_agent)) {
    return OUYA
  } else if (new RegExp('(' + WINDOWS_PHONE + '|WPDesktop)', 'i').test(user_agent)) {
    return WINDOWS_PHONE
  } else if (/iPad/.test(user_agent)) {
    return IPAD
  } else if (/iPod/.test(user_agent)) {
    return 'iPod Touch'
  } else if (/iPhone/.test(user_agent)) {
    return 'iPhone'
  } else if (/(watch)(?: ?os[,/]|\d,\d\/)[\d.]+/i.test(user_agent)) {
    return APPLE_WATCH
  } else if (BLACKBERRY_REGEX.test(user_agent)) {
    return BLACKBERRY
  } else if (/(kobo)\s(ereader|touch)/i.test(user_agent)) {
    return 'Kobo'
  } else if (new RegExp(NOKIA, 'i').test(user_agent)) {
    return NOKIA
  } else if (
    // Kindle Fire without Silk / Echo Show
    /(kf[a-z]{2}wi|aeo[c-r]{2})( bui|\))/i.test(user_agent) ||
    // Kindle Fire HD
    /(kf[a-z]+)( bui|\)).+silk\//i.test(user_agent)
  ) {
    return 'Kindle Fire'
  } else if (/(Android|ZTE)/i.test(user_agent)) {
    if (
      !new RegExp(MOBILE).test(user_agent) ||
      /(9138B|TB782B|Nexus [97]|pixel c|HUAWEISHT|BTV|noble nook|smart ultra 6)/i.test(user_agent)
    ) {
      if (
        (/pixel[\daxl ]{1,6}/i.test(user_agent) && !/pixel c/i.test(user_agent)) ||
        /(huaweimed-al00|tah-|APA|SM-G92|i980|zte|U304AA)/i.test(user_agent) ||
        (/lmy47v/i.test(user_agent) && !/QTAQZ3/i.test(user_agent))
      ) {
        return ANDROID
      }
      return ANDROID_TABLET
    } else {
      return ANDROID
    }
  } else if (new RegExp('(pda|' + MOBILE + ')', 'i').test(user_agent)) {
    return GENERIC_MOBILE
  } else if (new RegExp(TABLET, 'i').test(user_agent) && !new RegExp(TABLET + ' pc', 'i').test(user_agent)) {
    return GENERIC_TABLET
  } else {
    return ''
  }
}

export const detectDeviceType = function (
  user_agent: string,
  options?: {
    userAgentDataPlatform?: string
    maxTouchPoints?: number
    screenWidth?: number
    screenHeight?: number
    devicePixelRatio?: number
  }
): string {
  const device = detectDevice(user_agent)
  if (
    device === IPAD ||
    device === ANDROID_TABLET ||
    device === 'Kobo' ||
    device === 'Kindle Fire' ||
    device === GENERIC_TABLET
  ) {
    return TABLET
  } else if (device === NINTENDO || device === XBOX || device === PLAYSTATION || device === OUYA) {
    return 'Console'
  } else if (device === APPLE_WATCH) {
    return 'Wearable'
  } else if (device) {
    return MOBILE
  }

  // Chrome on Android tablets defaults to "request desktop site" mode, sending
  // a desktop-like UA (e.g. "X11; Linux x86_64") indistinguishable from desktop Linux.
  // The Client Hints API reports the true platform even when the UA lies.
  if (options?.userAgentDataPlatform === 'Android' && (options?.maxTouchPoints ?? 0) > 0) {
    const shortSide = Math.min(options?.screenWidth ?? 0, options?.screenHeight ?? 0)
    const shortSideDp = shortSide / (options?.devicePixelRatio ?? 1)
    return shortSideDp >= 600 ? TABLET : MOBILE
  }

  return 'Desktop'
}
