```
class TripDashboard:
    def __init__(self):
        self.trips = []

    def submit_trip(self, source_location, trip_start_date, trip_end_date, trip_type, destination_weather, trip_preferences):
        trip = {
            "source_location": source_location,
            "trip_start_date": trip_start_date,
            "trip_end_date": trip_end_date,
            "trip_type": trip_type,
            "destination_weather": destination_weather,
            "trip_preferences": trip_preferences
        }
        
        self.trips.append(trip)
        return "Trip submitted successfully!", trip

# Example usage:
if __name__ == "__main__":
    dashboard = TripDashboard()
    response = dashboard.submit_trip(
        source_location="New York",
        trip_start_date="2023-06-01",
        trip_end_date="2023-06-10",
        trip_type="international",
        destination_weather="sunny",
        trip_preferences="beach, adventure"
    )
    
    print(response)
```