"""
F1 Tire Degradation Data Collection Script
Collects historical F1 data using FastF1 and Jolpica APIs
"""

import fastf1
import pandas as pd
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable FastF1 cache to avoid re-downloading
cache_dir = Path('./fastf1_cache')
cache_dir.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))


class F1DataCollector:
    """Collects and processes F1 tire degradation data"""
    
    def __init__(self, output_dir: str = './data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # Updated to use Jolpica API
        self.jolpica_base_url = "http://api.jolpi.ca/ergast/f1"
        self.rate_limit_delay = 0.5  # 200 requests per hour = ~2 per second
        
    def get_season_schedule(self, year: int) -> List[Dict]:
        """Get race schedule for a season from Jolpica API"""
        url = f"{self.jolpica_base_url}/{year}.json"
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            races = data['MRData']['RaceTable']['Races']
            schedule = []
            
            for race in races:
                schedule.append({
                    'round': int(race['round']),
                    'race_name': race['raceName'],
                    'circuit_id': race['Circuit']['circuitId'],
                    'circuit_name': race['Circuit']['circuitName'],
                    'country': race['Circuit']['Location']['country'],
                    'date': race['date']
                })
            
            logger.info(f"Found {len(schedule)} races for {year}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error fetching schedule for {year}: {e}")
            return []
    
    def collect_race_lap_data(self, year: int, race_round: int, 
                              race_name: str) -> Optional[pd.DataFrame]:
        """Collect detailed lap data for a specific race"""
        
        try:
            logger.info(f"Loading {year} {race_name} (Round {race_round})...")
            
            # Load race session
            session = fastf1.get_session(year, race_round, 'R')
            session.load()
            
            # Get laps data
            laps = session.laps
            
            if laps.empty:
                logger.warning(f"No lap data for {year} {race_name}")
                return None
            
            # Extract relevant columns
            lap_data = pd.DataFrame({
                'year': year,
                'race_round': race_round,
                'race_name': race_name,
                'driver': laps['Driver'],
                'driver_number': laps['DriverNumber'],
                'team': laps['Team'],
                'lap_number': laps['LapNumber'],
                'lap_time_seconds': laps['LapTime'].dt.total_seconds(),
                'sector1_time_seconds': laps['Sector1Time'].dt.total_seconds(),
                'sector2_time_seconds': laps['Sector2Time'].dt.total_seconds(),
                'sector3_time_seconds': laps['Sector3Time'].dt.total_seconds(),
                'compound': laps['Compound'],
                'tyre_life': laps['TyreLife'],
                'stint': laps['Stint'],
                'fresh_tyre': laps['FreshTyre'],
                'track_status': laps['TrackStatus'],
                'is_personal_best': laps['IsPersonalBest'],
                'is_accurate': laps['IsAccurate'],
                'lap_start_time': laps['Time']
            })
            
            # Get weather data
            try:
                weather = session.weather_data
                if not weather.empty:
                    # Merge weather data based on closest time
                    lap_data['air_temp'] = None
                    lap_data['track_temp'] = None
                    lap_data['humidity'] = None
                    lap_data['rainfall'] = None
                    lap_data['wind_speed'] = None
                    
                    for idx, row in lap_data.iterrows():
                        lap_time = row['lap_start_time']
                        closest_weather = weather.iloc[(weather['Time'] - lap_time).abs().argsort()[0]]
                        lap_data.at[idx, 'air_temp'] = closest_weather['AirTemp']
                        lap_data.at[idx, 'track_temp'] = closest_weather['TrackTemp']
                        lap_data.at[idx, 'humidity'] = closest_weather['Humidity']
                        lap_data.at[idx, 'rainfall'] = closest_weather['Rainfall']
                        lap_data.at[idx, 'wind_speed'] = closest_weather['WindSpeed']
            except Exception as e:
                logger.warning(f"Could not load weather data: {e}")
            
            # Clean data
            lap_data = lap_data.dropna(subset=['lap_time_seconds'])
            lap_data = lap_data[lap_data['lap_time_seconds'] > 0]
            
            logger.info(f"Collected {len(lap_data)} laps from {race_name}")
            return lap_data
            
        except Exception as e:
            logger.error(f"Error collecting data for {year} {race_name}: {e}")
            return None
    
    def collect_pit_stop_data(self, year: int, race_round: int) -> Optional[pd.DataFrame]:
        """Collect pit stop data from Jolpica API"""
        
        url = f"{self.jolpica_base_url}/{year}/{race_round}/pitstops.json"
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pit_stops = data['MRData']['RaceTable']['Races']
            if not pit_stops or 'PitStops' not in pit_stops[0]:
                return None
            
            stops = []
            for stop in pit_stops[0]['PitStops']:
                stops.append({
                    'year': year,
                    'race_round': race_round,
                    'driver': stop['driverId'],
                    'lap': int(stop['lap']),
                    'stop_number': int(stop['stop']),
                    'duration_seconds': float(stop['duration']),
                    'time_of_day': stop.get('time', None)
                })
            
            logger.info(f"Collected {len(stops)} pit stops")
            return pd.DataFrame(stops)
            
        except Exception as e:
            logger.error(f"Error collecting pit stop data: {e}")
            return None
    
    def get_race_results(self, year: int, race_round: int) -> Optional[pd.DataFrame]:
        """Get race results from Jolpica API (useful for additional context)"""
        
        url = f"{self.jolpica_base_url}/{year}/{race_round}/results.json"
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            races = data['MRData']['RaceTable']['Races']
            if not races or 'Results' not in races[0]:
                return None
            
            results = []
            for result in races[0]['Results']:
                results.append({
                    'year': year,
                    'race_round': race_round,
                    'position': int(result['position']),
                    'driver': result['Driver']['driverId'],
                    'driver_code': result['Driver']['code'],
                    'driver_number': result.get('number', None),
                    'constructor': result['Constructor']['constructorId'],
                    'grid': int(result['grid']),
                    'laps': int(result['laps']),
                    'status': result['status'],
                    'points': float(result['points'])
                })
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Error collecting race results: {e}")
            return None
    
    def calculate_degradation_metrics(self, lap_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate tire degradation metrics for each stint"""
        
        # Group by driver and stint
        lap_data = lap_data.sort_values(['driver', 'stint', 'lap_number'])
        
        # Calculate metrics per stint
        stint_groups = lap_data.groupby(['driver', 'stint'])
        
        # First lap time in stint (baseline)
        lap_data['stint_first_lap_time'] = stint_groups['lap_time_seconds'].transform('first')
        
        # Delta from first lap
        lap_data['time_delta_from_first'] = (
            lap_data['lap_time_seconds'] - lap_data['stint_first_lap_time']
        )
        
        # Rolling average (3-lap window)
        lap_data['lap_time_rolling_avg'] = (
            stint_groups['lap_time_seconds'].transform(lambda x: x.rolling(3, min_periods=1).mean())
        )
        
        # Degradation rate (seconds per lap on tires)
        def calc_degradation_rate(group):
            if len(group) < 2:
                return pd.Series([0] * len(group), index=group.index)
            
            # Simple linear regression: lap_time vs tyre_life
            from scipy.stats import linregress
            valid = group[['tyre_life', 'lap_time_seconds']].dropna()
            
            if len(valid) < 2:
                return pd.Series([0] * len(group), index=group.index)
            
            slope, _, _, _, _ = linregress(valid['tyre_life'], valid['lap_time_seconds'])
            return pd.Series([slope] * len(group), index=group.index)
        
        lap_data['degradation_rate'] = stint_groups.apply(calc_degradation_rate).values
        
        return lap_data
    
    def collect_season_data(self, year: int, max_races: Optional[int] = None) -> tuple:
        """Collect data for entire season"""
        
        # Get season schedule
        schedule = self.get_season_schedule(year)
        
        if not schedule:
            logger.error(f"Could not fetch schedule for {year}")
            return pd.DataFrame(), pd.DataFrame()
        
        if max_races:
            schedule = schedule[:max_races]
        
        all_lap_data = []
        all_pit_data = []
        
        for race in schedule:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {race['race_name']} (Round {race['round']})")
            logger.info(f"{'='*60}")
            
            # Collect lap data
            lap_data = self.collect_race_lap_data(
                year, 
                race['round'], 
                race['race_name']
            )
            
            if lap_data is not None:
                # Add circuit information
                lap_data['circuit_name'] = race['circuit_name']
                lap_data['country'] = race['country']
                
                # Calculate degradation metrics
                lap_data = self.calculate_degradation_metrics(lap_data)
                all_lap_data.append(lap_data)
            
            # Collect pit stop data
            pit_data = self.collect_pit_stop_data(year, race['round'])
            if pit_data is not None:
                all_pit_data.append(pit_data)
            
            # Respectful rate limiting
            time.sleep(2)
        
        # Combine all data
        if all_lap_data:
            combined_laps = pd.concat(all_lap_data, ignore_index=True)
            logger.info(f"\n{'='*60}")
            logger.info(f"Total laps collected for {year}: {len(combined_laps)}")
            logger.info(f"{'='*60}\n")
        else:
            combined_laps = pd.DataFrame()
        
        if all_pit_data:
            combined_pits = pd.concat(all_pit_data, ignore_index=True)
        else:
            combined_pits = pd.DataFrame()
        
        return combined_laps, combined_pits
    
    def save_data(self, lap_data: pd.DataFrame, pit_data: pd.DataFrame, 
                  year: int, version: str = 'v1'):
        """Save collected data to CSV files"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save lap data
        if not lap_data.empty:
            lap_filename = self.output_dir / f'f1_lap_data_{year}_{version}_{timestamp}.csv'
            lap_data.to_csv(lap_filename, index=False)
            logger.info(f"Saved lap data to {lap_filename}")
        
        # Save pit data
        if not pit_data.empty:
            pit_filename = self.output_dir / f'f1_pit_data_{year}_{version}_{timestamp}.csv'
            pit_data.to_csv(pit_filename, index=False)
            logger.info(f"Saved pit data to {pit_filename}")
        
        return lap_filename if not lap_data.empty else None


def main():
    """Main execution function"""
    
    collector = F1DataCollector(output_dir='./data')
    
    # Collect data for recent seasons
    # Start with just 2023, then expand to 2022, 2021
    years_to_collect = [2023]  # Can add 2022, 2021 later
    
    logger.info("\n" + "="*60)
    logger.info("F1 Tire Degradation Data Collection")
    logger.info("Using Jolpica API (Ergast replacement)")
    logger.info("="*60 + "\n")
    
    for year in years_to_collect:
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Starting collection for {year} season")
        logger.info(f"{'#'*60}\n")
        
        lap_data, pit_data = collector.collect_season_data(year)
        
        if not lap_data.empty:
            collector.save_data(lap_data, pit_data, year)
            
            # Print summary statistics
            logger.info(f"\n{'='*60}")
            logger.info(f"Summary for {year}:")
            logger.info(f"  Total laps: {len(lap_data)}")
            logger.info(f"  Total pit stops: {len(pit_data) if not pit_data.empty else 0}")
            logger.info(f"  Unique drivers: {lap_data['driver'].nunique()}")
            logger.info(f"  Unique races: {lap_data['race_round'].nunique()}")
            logger.info(f"  Tire compounds used: {lap_data['compound'].unique().tolist()}")
            logger.info(f"{'='*60}\n")
        else:
            logger.warning(f"No data collected for {year}")
        
        # Brief pause between seasons
        time.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("Data collection complete!")
    logger.info("="*60)


if __name__ == "__main__":
    main()