# Required imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# function definitions
def get_lat_lon(location_name, city='Seattle', state='WA', country='USA'):
    base_url = "https://nominatim.openstreetmap.org/search.php"
    query_params = {
        "q": f"{location_name}, {city}, {state}, {country}",  # More specific query
        "format": "jsonv2"
    }
    response = requests.get(base_url, params=query_params)
    if response.status_code == 200 and len(response.json()) > 0:
        data = response.json()[0]
        lat, lon = float(data.get('lat')), float(data.get('lon'))
        # Validate coordinates (example range for Seattle)
        if 47.4 <= lat <= 47.8 and -122.5 <= lon <= -122.2:
            return lat, lon
        else:
            return None, None  # Coordinates are outside the expected range
    else:
        return None, None  # API request failed or returned no data

def get_weather_forecast(lat, lon, event_date):
    try:
        url_weather = f"https://api.weather.gov/points/{lat},{lon}"
        response = requests.get(url_weather)
        if response.status_code == 200:
            # Extract the forecast URL from the response
            forecast_url = response.json()['properties']['forecast']
            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()['properties']['periods']
                for period in forecast_data:
                    forecast_date = datetime.strptime(period['startTime'], '%Y-%m-%dT%H:%M:%S%z').date()
                    if forecast_date == event_date and 'daytime' in period['name'].lower():
                        weather = period['shortForecast']
                        temperature = period['temperature']
                        wind_speed = period['windSpeed']
                        wind_direction = period['windDirection']
                        return weather, temperature, wind_speed, wind_direction
        return None, None, None, None
    except Exception as e:
        print(f"Error fetching weather data for lat: {lat}, lon: {lon}, date: {event_date}. Error: {e}")
        return None, None, None, None
    
def get_latest_weather_forecast(lat, lon):
    try:
        url_weather = f"https://api.weather.gov/points/{lat},{lon}"
        response = requests.get(url_weather)
        if response.status_code == 200:
            forecast_url = response.json()['properties']['forecast']
            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()['properties']['periods'][0] # Get the latest forecast
                return forecast_data['shortForecast'], forecast_data['temperature'], forecast_data['windSpeed'], forecast_data['windDirection']
        return 'Not available', 'Not available', 'Not available', 'Not available'
    except Exception as e:
        print(f"Error fetching latest weather data for lat: {lat}, lon: {lon}. Error: {e}")
        return 'Not available', 'Not available', 'Not available', 'Not available'

def get_seattle_weather_forecast():
   
    seattle_lat = '47.6062'
    seattle_lon = '-122.3321'
    return get_latest_weather_forecast(seattle_lat, seattle_lon)


# 1. Get Event Details

events = []

for page in range(1, 50):  # 50 pages of events, date: 30 Jan 2024
    url = 'https://visitseattle.org/events/page/' + str(page)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    selector = 'div.search-result-preview > div > h3 > a'
    a_eles=soup.select(selector)
    events = events + [x['href'] for x in a_eles]

eventdata = []

for event in events:
    res = requests.get(event)

    if res.status_code == 200:
        soup = BeautifulSoup(res.content, 'html.parser')
        
        name = soup.select_one('div.medium-6.columns.event-top > h1')
        date_time = soup.select_one('div.medium-6.columns.event-top > h4 > span:nth-child(1)')
        location = soup.select_one('div.medium-6.columns.event-top > h4 > span:nth-child(2)')
        event_type = soup.select_one('div.medium-6.columns.event-top > a:nth-child(3)')
        region = soup.select_one('div.medium-6.columns.event-top > a:nth-child(4)')

        eventdata.append({
            "Name": name.get_text(strip=True) if name else "Not found",
            "Date & Time": date_time.get_text(strip=True) if date_time else "Not found",
            "Location": location.get_text(strip=True) if location else "Not found",
            "Type": event_type.get_text(strip=True) if event_type else "Not found",
            "Region": region.get_text(strip=True) if region else "Not found"
        })



df = pd.DataFrame(eventdata)
df.to_csv("events_basic.csv", index=False)

# 2. Get Weather Info
# Using the National Weather Service API to get weather information for a location

url_weather = "https://api.weather.gov/points/39.7456,-97.0892"
weather_response = requests.get(url_weather)
weather_data = weather_response.json()  # Parse JSON response

# Extract forecast URL from weather data and fetch forecast details
forecast_url = weather_data['properties']['forecast']
forecast_response = requests.get(forecast_url)
forecast_data = forecast_response.json()  # Parse forecast JSON


# 3. Get Location Lat & Lon

# Read CSV file
csv_file = 'events_basic.csv' 
df = pd.read_csv(csv_file)

# Adding new columns for latitude and longitude
df['Latitude'] = None
df['Longitude'] = None

for index, row in df.iterrows():
    lat, lon = get_lat_lon(row['Location'])
    if lat is not None and lon is not None:
        df.at[index, 'Latitude'] = lat
        df.at[index, 'Longitude'] = lon
    else:
        # Handle cases where coordinates are not found or invalid
        print(f"Coordinates not found or invalid for location: {row['Location']}")

# Save the updated DataFrame to a new CSV file
df.to_csv('events_latlon.csv', index=False)

# 4. Use Lat & Lon to Fetch Weather Info

csv_file = 'events_latlon.csv'
df = pd.read_csv(csv_file)

# Adding new columns for weather details
df['weather'] = None
df['temperature'] = None
df['wind_speed'] = None
df['wind_direction'] = None

for index, row in df.iterrows():
    lat = row.get('Latitude')
    lon = row.get('Longitude')
    date_str = row['Date & Time'].split(' ')[0]

    if pd.notna(lat) and pd.notna(lon):
        try:
            if date_str.lower() == 'now' or date_str.lower() == 'ongoing':
                weather_info = get_latest_weather_forecast(lat, lon)
            else:
                event_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                weather_info = get_weather_forecast(lat, lon, event_date)

            # Check if weather info is not returned
            if not all(weather_info):
                weather_info = get_seattle_weather_forecast()  # Default to Seattle weather
        except Exception:
            weather_info = get_seattle_weather_forecast()  # Default to Seattle weather
    else:
        weather_info = get_seattle_weather_forecast()  # Default to Seattle weather

    # Update the DataFrame with the weather information
    df.at[index, 'weather'], df.at[index, 'temperature'], df.at[index, 'wind_speed'], df.at[index, 'wind_direction'] = weather_info

# Export the updated dataframe to a CSV file
df.to_csv('events.csv', index=False)


if __name__ == "__main__":
    # Fetch and process event details, then save initial data to CSV
    print("Fetching event details...")
    # Assuming a function that encapsulates fetching event details exists
    # fetch_and_save_event_details()  # You would define this function
    
    # Update the events data with latitude and longitude
    print("Updating events with location data...")
    # update_events_with_lat_lon('events_basic.csv')  # Define this too
    
    # Finally, update the events data with weather information and save the final CSV
    print("Updating events with weather information...")
    # update_events_with_weather('events_latlon.csv')  # And this function
    
    print("Process completed. Check the output CSV file 'events.csv'.")

