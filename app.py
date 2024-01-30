"""
Change this to a world clock app
"""

import time
import pytz
import datetime
import re
import streamlit as st

# Predefined list of locations and their corresponding time zones
locations = {
    "New York": "America/New_York",
    "London": "Europe/London",
    "Tokyo": "Asia/Tokyo",
    "Sydney": "Australia/Sydney",
    "Paris": "Europe/Paris",
    "Berlin": "Europe/Berlin",
    "Moscow": "Europe/Moscow",
    "Beijing": "Asia/Shanghai",
    "New Delhi": "Asia/Kolkata",
    "São Paulo": "America/Sao_Paulo",
}

# Streamlit app
def world_clock():
    st.title("World Clock")
    #Add author
    st.text("Freya Yu 2372732 yeyfreya@uw.edu")

    # Dropdown menu for selecting locations
    selected_locations = st.multiselect("Select locations", options=list(locations.keys()), default=["New York", "London"])

    # Validate the selected locations using regex to ensure they are in our predefined list
    valid_locations = [loc for loc in selected_locations if re.match("|".join(locations.keys()), loc)]

    # Container to display clocks
    placeholder = st.empty()
    
    cnt = 0
    while True:
        with placeholder.container():
            # Display the current time for up to 4 valid locations
            for loc in valid_locations[:4]:  # Limit to 4 locations
                tz = pytz.timezone(locations[loc])
                current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                st.metric(label=loc, value=current_time)

        time.sleep(1)  # Update the time every second

if __name__ == "__main__":
    world_clock()



    