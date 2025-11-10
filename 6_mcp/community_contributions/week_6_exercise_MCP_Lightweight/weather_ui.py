import gradio as gr
from sorrounding import Atmosphere

def show_weather(city: str):
    temp = Atmosphere.fetch_temperature(city)
    cond = Atmosphere.fetch_condition(city)
    humid = Atmosphere.fetch_humidity(city)
    wind = Atmosphere.fetch_wind_speed(city)

    if not temp["success"]:
        return f"Error: {temp['error']}"
    if not cond["success"]:
        return f"Error: {cond['error']}"
    if not humid["success"]:
        return f"Error: {humid['error']}"
    if not wind["success"]:
        return f"Error: {wind['error']}"

    return (
        f"City: {city}\n"
        f"Temperature: {temp['temperature_celsius']} °C\n"
        f"Weather: {cond['weather']}\n"
        f"Humidity: {humid['humidity']} %\n"
        f"Wind: {wind['wind_kph']} kph"
    )

iface = gr.Interface(
    fn=show_weather,
    inputs=gr.Textbox(label="Enter city name"),
    outputs=gr.Textbox(label="Weather Info"),
    title="City Weather Checker",
    description="Enter a city to get temperature, weather, humidity, and wind speed."
)

iface.launch()
