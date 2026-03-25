import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional


class FlightTracker:
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the flight tracker
        
        Args:
            username: OpenSky Network username (optional, for higher rate limits)
            password: OpenSky Network password (optional, for higher rate limits)
        """
        self.base_url = "https://opensky-network.org/api"
        self.auth = (username, password) if username and password else None
        
    def get_flight_by_callsign(self, callsign: str) -> Optional[Dict]:
        try:
            callsign = callsign.strip().upper()
            
            url = f"{self.base_url}/states/all"
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'states' not in data:
                return None
            
            # Search through all current flights
            for state in data['states']:
                flight_callsign = state[1]
                if flight_callsign and flight_callsign.strip().upper() == callsign:
                    return self._parse_state_vector(state)
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def get_multiple_flights(self, callsigns: List[str]) -> Dict[str, Optional[Dict]]:

        results = {}
        
        try:
            # Clean up callsigns
            callsigns = [cs.strip().upper() for cs in callsigns]
            
            url = f"{self.base_url}/states/all"
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'states' not in data:
                return {cs: None for cs in callsigns}
            
            # Initialize all callsigns as not found
            for cs in callsigns:
                results[cs] = None
            
            # Search through all current flights
            for state in data['states']:
                flight_callsign = state[1]
                if flight_callsign:
                    flight_callsign = flight_callsign.strip().upper()
                    if flight_callsign in callsigns:
                        results[flight_callsign] = self._parse_state_vector(state)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {cs: None for cs in callsigns}
    
    def _parse_state_vector(self, state: List) -> Dict:
        """
        Parse OpenSky state vector into readable format
        
        State vector format:
        [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
        [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
        [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate,
        [12] sensors, [13] geo_altitude, [14] squawk, [15] spi, [16] position_source
        """
        return {
            'icao24': state[0],
            'callsign': state[1].strip() if state[1] else None,
            'origin_country': state[2],
            'longitude': state[5],
            'latitude': state[6],
            'altitude_barometric': state[7],  # meters
            'altitude_geometric': state[13],  # meters
            'on_ground': state[8],
            'velocity': state[9],  # m/s
            'heading': state[10],  # degrees
            'vertical_rate': state[11],  # m/s
            'squawk': state[14],
            'last_contact': datetime.fromtimestamp(state[4]).strftime('%Y-%m-%d %H:%M:%S'),
            'time_position': datetime.fromtimestamp(state[3]).strftime('%Y-%m-%d %H:%M:%S') if state[3] else None
        }
    
    def format_flight_info(self, flight_data: Dict) -> str:
        """Format flight data for display"""
        if not flight_data:
            return "Flight not found or not currently airborne"
        
        # Convert units
        altitude_ft = int(flight_data['altitude_barometric'] * 3.28084) if flight_data['altitude_barometric'] else 0
        speed_knots = int(flight_data['velocity'] * 1.94384) if flight_data['velocity'] else 0
        vertical_rate_fpm = int(flight_data['vertical_rate'] * 196.85) if flight_data['vertical_rate'] else 0
        
        info = f"""
{'='*60}
Call Sign: {flight_data['callsign']}
ICAO24: {flight_data['icao24']}
Origin Country: {flight_data['origin_country']}
{'='*60}
Position:
  Latitude:  {flight_data['latitude']:.4f}° {'N' if flight_data['latitude'] >= 0 else 'S'}
  Longitude: {flight_data['longitude']:.4f}° {'E' if flight_data['longitude'] >= 0 else 'W'}
  
Altitude:
  Barometric: {altitude_ft:,} ft ({flight_data['altitude_barometric']:.0f} m)
  
Speed & Direction:
  Ground Speed: {speed_knots} knots ({flight_data['velocity']:.1f} m/s)
  Heading: {flight_data['heading']:.1f}°
  Vertical Rate: {vertical_rate_fpm:+,} ft/min
  
Status:
  On Ground: {'Yes' if flight_data['on_ground'] else 'No'}
  Squawk: {flight_data['squawk'] if flight_data['squawk'] else 'N/A'}
  
Last Contact: {flight_data['last_contact']}
Position Time: {flight_data['time_position']}
{'='*60}
"""
        return info
    
    def track_continuously(self, callsigns: List[str], interval: int = 10):
        print(f"Starting continuous tracking for: {', '.join(callsigns)}")
        print(f"Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updating...")
                print("-" * 60)
                
                results = self.get_multiple_flights(callsigns)
                
                for callsign, data in results.items():
                    if data:
                        print(self.format_flight_info(data))
                    else:
                        print(f"\nCall Sign: {callsign}")
                        print("Status: Not found or not currently airborne\n")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nTracking stopped by user")


def main():

    tracker = FlightTracker()
    
    print("Flight Radar Scraper - Track Jets by Call Sign")
    print("=" * 60)
    
    print("\nExample 1: Single flight lookup")
    callsign = input("Enter call sign to track (e.g., UAL123): ").strip()
    
    if callsign:
        flight_data = tracker.get_flight_by_callsign(callsign)
        print(tracker.format_flight_info(flight_data))
    
    print("\n" + "=" * 60)
    print("Example 2: Track multiple flights continuously")
    callsigns_input = input("Enter call signs separated by commas (e.g., UAL123,DAL456): ").strip()
    
    if callsigns_input:
        callsigns = [cs.strip() for cs in callsigns_input.split(',') if cs.strip()]
        
        if callsigns:
            interval = input("Update interval in seconds (default 10, min 10): ").strip()
            interval = int(interval) if interval.isdigit() and int(interval) >= 10 else 10
            
            tracker.track_continuously(callsigns, interval)


if __name__ == "__main__":
    main()
