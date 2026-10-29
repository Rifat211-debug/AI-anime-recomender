import os
import json
from datetime import date

import requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@tool
def search_latest_anime(query: str) -> str:
    """
        Search the live web for newly released or upcoming anime,
        release dates, anime movies, announcements, and current details
        that may not exist in the local anime dataset.
        Use web results as external information and include source URLs.
    """

    try:
        if not os.getenv("TAVILY_API_KEY"):
            return "Anime web search is unavailable: TAVILY_API_KEY is missing."

        today = date.today().isoformat()
        search_tool = TavilySearch(
            max_results = 5,
            topic = "general",
            search_depth = "basic",
            include_answer = True
        )

        search_query = (
            f"Today is {today}. Search for current and recent anime"
            f"releases, upcoming anime, official announcements, "
            f"release dates, and reliable details related to: {query}"
            "Prioritize official anime websites, studios, and "
            "reliable anime news sources. Distinguish released anime "
            "from upcoming titles. Include publication dates and "
            "source URLs when available."
        )
        results = search_tool.invoke({"query": search_query})
        return json.dumps(results, ensure_ascii = False, default = str)[:12000]
    except Exception as e:
        return f"Anime web search failed: {str(e)}"


@tool
def get_current_weather(city: str) -> str:
    """
        Get the current weather conditions for a specified city.
        Returns temperature in Celsius, feels-like temperature,
        humidity, wind speed, and a weather description.
        Use this tool when the user wants anime recommendations
        based on current weather or asks about the weather.
    """

    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return (
                    "Weather lookup is unavailable: "
                    "OPENWEATHER_API_KEY is missing."
                    )
        if not city or not city.strip():
            return "Please provide a city name for weather lookup."

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params = {
                "q": city.strip(),
                "appid": api_key,
                "units": "metric"
            },
            timeout = 15
        )
        if response.status_code == 404:
            return f"Could not find weather data for '{city}'. Check the city name."
        response.raise_for_status()
        data = response.json()

        weather = data["weather"][0]
        main = data["main"]
        wind = data.get("wind", {})

        result = {
                    "city": data.get("name", city),
                    "country_code": data.get("sys", {}).get("country"),
                    "conditions": weather.get("description"),
                    "temperature_celsius": main.get("temp"),
                    "feels_like_celsius": main.get("feels_like"),
                    "humidity_percent": main.get("humidity"),
                    "wind_speed_m_s": wind.get("speed"),
                    "data_source": "OpenWeatherMap current weather API",
                }
        return json.dumps(result, ensure_ascii = False)

    except requests.RequestException as e:
        return f"Weather API request failed: {str(e)}"
    
    except (KeyError, IndexError, ValueError) as e:
        return f"Could not process the weather response: {str(e)}"

def build_external_tools():
    """Return the tools that use external APIs."""
    return [
        search_latest_anime,
        get_current_weather,
    ]
    