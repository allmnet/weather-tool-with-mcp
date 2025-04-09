"""
MCP server to get weather data
"""

from mcp.server.fastmcp import FastMCP
from dotenv import dotenv_values
import requests

WEATER_KEY = '--'

mcp = FastMCP(name="weather", host="127.0.0.1", port=50000, timeout=30)
env = dotenv_values()
WEATHER_URL = "https://api.weatherapi.com/v1/current.json?key=WEATHER_KEY&q=CITY_NAME"


@mcp.tool()
def get_todays_weather(city_name: str) -> str:
    """
    Get today's weather for `city_name` city
    """
    url = WEATHER_URL.replace("WEATHER_KEY", WEATER_KEY).replace(
        "CITY_NAME", city_name
    )
    response = requests.get(url, timeout=10)
    return response.text


if __name__ == "__main__":
    print("Running server...")
    mcp.run()
