"""Current weather for Nairobi via OpenWeatherMap HTTP API."""

import os

import requests


def fetch_nairobi_weather() -> str:
    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        return (
            "Weather unavailable: set OPENWEATHER_API_KEY (OpenWeatherMap API key)."
        )

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "Nairobi,KE",
        "appid": key,
        "units": "metric",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        d = r.json()
    except requests.RequestException as exc:
        return f"Weather request failed: {exc}"

    main = d.get("main", {})
    wind = d.get("wind", {})
    weather = (d.get("weather") or [{}])[0]
    rain = d.get("rain") or {}
    desc = weather.get("description", "unknown")

    lines = [
        f"Location: Nairobi, Kenya (OpenWeatherMap one-call style current conditions)",
        f"Summary: {desc}",
        f"Temperature: {main.get('temp')}°C (feels like {main.get('feels_like')}°C)",
        f"Humidity: {main.get('humidity')}%",
        f"Pressure: {main.get('pressure')} hPa",
        f"Wind: {wind.get('speed', 'n/a')} m/s",
    ]
    if rain:
        lines.append(f"Rain volume (recent): {rain}")

    lines.append(
        "\nNote: Nairobi long rains and flash-flood risk can affect travel; "
        "check local alerts (Kenya Met, NDOC, county updates) before outdoor plans."
    )
    return "\n".join(lines)


def fetch_nairobi_forecast_digest(hours_ahead: int = 36) -> str:
    """3-hour step forecast (OpenWeatherMap `forecast`) for outfit / activity planning."""
    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        return ""

    # cnt = number of 3h steps; 12 steps ~= 36h
    steps = max(4, min(16, (hours_ahead + 2) // 3))
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": "Nairobi,KE",
        "appid": key,
        "units": "metric",
        "cnt": steps,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as exc:
        return f"Forecast request failed: {exc}"

    items = data.get("list") or []
    if not items:
        return "Forecast: no time steps returned."

    lines = [
        f"## Short-range forecast (next ~{hours_ahead}h, OpenWeatherMap 3h steps)",
        "Use temperature, conditions, rain probability (POP), and expected rain volume for outfit and plans.",
    ]
    for step in items:
        ts = step.get("dt_txt", "")
        main = step.get("main") or {}
        w0 = (step.get("weather") or [{}])[0]
        desc = w0.get("description", "")
        pop = step.get("pop")
        rain = step.get("rain") or {}
        rain_3h = rain.get("3h")
        temp = main.get("temp")
        feels = main.get("feels_like")
        pop_s = f"{int(float(pop) * 100)}%" if pop is not None else "n/a"
        rain_s = f"{rain_3h} mm / 3h" if rain_3h is not None else "no significant rain in API field"
        lines.append(
            f"- **{ts}** — {temp}°C (feels {feels}°C), {desc}, "
            f"rain chance {pop_s}, {rain_s}"
        )

    return "\n".join(lines)
