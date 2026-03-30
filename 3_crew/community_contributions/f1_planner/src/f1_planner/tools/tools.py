import os
import requests
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CurrencyExchangeInput(BaseModel):
    from_currency: str = Field(description="Source currency code (e.g. 'SGD', 'EUR', 'GBP')")
    to_currency: str = Field(description="Target currency code (e.g. 'INR', 'USD')")


class CurrencyExchangeTool(BaseTool):
    name: str = "Get Currency Exchange Rate"
    description: str = (
        "Get the real-time exchange rate between two currencies. "
        "Returns the current rate from a live API. "
        "Use this instead of guessing or searching the web for exchange rates."
    )
    args_schema: Type[BaseModel] = CurrencyExchangeInput

    def _run(self, from_currency: str, to_currency: str) -> str:
        from_code = from_currency.upper()
        to_code = to_currency.upper()
        try:
            resp = requests.get(
                f"https://open.er-api.com/v6/latest/{from_code}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"Error fetching exchange rate: {e}"

        if data.get("result") != "success":
            return f"API error: {data}"

        rate = data.get("rates", {}).get(to_code)
        if rate is None:
            return f"Currency code '{to_code}' not found in API response."

        return (
            f"1 {from_code} = {rate} {to_code} "
            f"(source: open.er-api.com, updated: {data.get('time_last_update_utc', 'N/A')})"
        )


class FlightSearchInput(BaseModel):
    departure_id: str = Field(description="IATA airport code for departure (e.g. 'HYD')")
    arrival_id: str = Field(description="IATA airport code for arrival (e.g. 'SIN')")
    outbound_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: str = Field(description="Return date in YYYY-MM-DD format")
    currency: str = Field(default="USD", description="Currency code (e.g. 'INR', 'USD')")


class GoogleFlightsTool(BaseTool):
    name: str = "Search Flight Prices"
    description: str = (
        "Search for real flight prices, departure/arrival times, and flight numbers "
        "between two airports on specific dates using Google Flights data. "
        "Requires IATA airport codes (e.g. HYD, SIN, LHR) and dates in YYYY-MM-DD format."
    )
    args_schema: Type[BaseModel] = FlightSearchInput

    def _run(self, departure_id: str, arrival_id: str, outbound_date: str,
             return_date: str, currency: str = "USD") -> str:
        try:
            from serpapi import GoogleSearch
        except ImportError:
            return "Error: google-search-results package not installed. Run: pip install google-search-results"

        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY not found in environment variables."

        params = {
            "api_key": api_key,
            "engine": "google_flights",
            "departure_id": departure_id.upper(),
            "arrival_id": arrival_id.upper(),
            "outbound_date": outbound_date,
            "return_date": return_date,
            "currency": currency.upper(),
            "hl": "en",
            "type": "1",  # round trip
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            return f"Error calling SerpApi Google Flights: {e}"

        if "error" in results:
            return f"API error: {results['error']}"

        google_url = results.get("search_metadata", {}).get("google_flights_url", "")

        output_lines = [
            f"# Flight Search Results: {departure_id.upper()} → {arrival_id.upper()}",
            f"**Dates:** {outbound_date} to {return_date} | **Currency:** {currency.upper()}",
        ]
        if google_url:
            output_lines.append(f"**Book on Google Flights:** {google_url}")
        output_lines.append("")

        best = results.get("best_flights", [])
        other = results.get("other_flights", [])
        all_flights = best + other

        if not all_flights:
            output_lines.append("No flights found for these dates and route.")
            price_insights = results.get("price_insights", {})
            if price_insights:
                lowest = price_insights.get("lowest_price")
                typical = price_insights.get("typical_price_range", [])
                if lowest:
                    output_lines.append(f"Price insight — Lowest known price: {currency.upper()} {lowest}")
                if typical:
                    output_lines.append(f"Typical price range: {currency.upper()} {typical[0]} – {typical[1]}")
            return "\n".join(output_lines)

        for i, flight_option in enumerate(all_flights[:5], 1):
            price = flight_option.get("price", "N/A")
            flight_type = flight_option.get("type", "")
            total_duration = flight_option.get("total_duration", 0)
            hours, mins = divmod(total_duration, 60)

            output_lines.append(f"## Option {i} — {currency.upper()} {price} ({flight_type})")
            output_lines.append(f"Total duration: {hours}h {mins}m")

            segments = flight_option.get("flights", [])
            for seg in segments:
                dep = seg.get("departure_airport", {})
                arr = seg.get("arrival_airport", {})
                airline = seg.get("airline", "Unknown")
                flight_num = seg.get("flight_number", "N/A")
                output_lines.append(
                    f"  - {airline} {flight_num}: "
                    f"{dep.get('id', '?')} {dep.get('time', '?')} → "
                    f"{arr.get('id', '?')} {arr.get('time', '?')} "
                    f"(duration: {seg.get('duration', '?')} min)"
                )

            layovers = flight_option.get("layovers", [])
            if layovers:
                for lay in layovers:
                    output_lines.append(
                        f"  - Layover: {lay.get('name', '?')} — {lay.get('duration', '?')} min"
                    )

            output_lines.append("")

        price_insights = results.get("price_insights", {})
        if price_insights:
            lowest = price_insights.get("lowest_price")
            typical = price_insights.get("typical_price_range", [])
            if lowest:
                output_lines.append(f"**Price insight — Lowest price:** {currency.upper()} {lowest}")
            if typical:
                output_lines.append(f"**Typical price range:** {currency.upper()} {typical[0]} – {typical[1]}")

        return "\n".join(output_lines)


class HotelSearchInput(BaseModel):
    query: str = Field(description="Hotel search query — include tier and location, e.g. 'luxury hotel near [circuit/venue name]' or 'budget hostel [city name]'")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
    currency: str = Field(default="USD", description="Currency code (e.g. 'INR', 'USD')")
    adults: int = Field(default=1, description="Number of adults")
    sort_by: str = Field(default="3", description="Sort order: '3' for lowest price, '8' for highest rating, '13' for most reviewed")


class GoogleHotelsPriceTool(BaseTool):
    name: str = "Search Hotel Prices"
    description: str = (
        "Search for real hotel prices for specific check-in and check-out dates "
        "using Google Hotels data. Returns hotel names, nightly rates, total cost, "
        "and booking links. Include the tier and destination in the query, e.g. "
        "'luxury hotel near [venue]', 'mid-range hotel [city centre area]', "
        "'budget hostel [city]'. Use sort_by='8' for highest rated, '13' for most "
        "reviewed, '3' for lowest price."
    )
    args_schema: Type[BaseModel] = HotelSearchInput

    def _run(self, query: str, check_in_date: str, check_out_date: str,
             currency: str = "USD", adults: int = 1, sort_by: str = "3") -> str:
        try:
            from serpapi import GoogleSearch
        except ImportError:
            return "Error: google-search-results package not installed. Run: pip install google-search-results"

        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY not found in environment variables."

        params = {
            "api_key": api_key,
            "engine": "google_hotels",
            "q": query,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "currency": currency.upper(),
            "adults": str(adults),
            "hl": "en",
            "sort_by": sort_by,
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            return f"Error calling SerpApi Google Hotels: {e}"

        if "error" in results:
            return f"API error: {results['error']}"

        properties = results.get("properties", [])
        if not properties:
            return f"No hotel results found for '{query}' on {check_in_date} to {check_out_date}."

        output_lines = [
            f"# Hotel Search Results: {query}",
            f"**Dates:** {check_in_date} to {check_out_date} | **Currency:** {currency.upper()}",
            "",
        ]

        for i, hotel in enumerate(properties[:8], 1):
            name = hotel.get("name", "Unknown")
            rate_per_night = hotel.get("rate_per_night", {})
            total_rate = hotel.get("total_rate", {})
            rating = hotel.get("overall_rating", "N/A")
            hotel_type = hotel.get("type", "")
            link = hotel.get("link", "")

            nightly = rate_per_night.get("lowest", "N/A")
            nightly_before_tax = rate_per_night.get("before_taxes_fees", "")
            total = total_rate.get("lowest", "N/A")
            total_before_tax = total_rate.get("before_taxes_fees", "")

            output_lines.append(f"## {i}. {name}")
            if hotel_type:
                output_lines.append(f"Type: {hotel_type} | Rating: {rating}")
            output_lines.append(f"Nightly rate: {nightly}")
            if nightly_before_tax:
                output_lines.append(f"Nightly (before taxes/fees): {nightly_before_tax}")
            output_lines.append(f"Total stay cost: {total}")
            if total_before_tax:
                output_lines.append(f"Total (before taxes/fees): {total_before_tax}")
            if link:
                output_lines.append(f"Booking link: {link}")

            check_in_time = hotel.get("check_in_time", "")
            check_out_time = hotel.get("check_out_time", "")
            if check_in_time:
                output_lines.append(f"Check-in: {check_in_time} | Check-out: {check_out_time}")

            output_lines.append("")

        return "\n".join(output_lines)
