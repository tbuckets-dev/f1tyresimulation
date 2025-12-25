"""
F1 Data Loader - Load CSV data into PostgreSQL database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
import logging
from pathlib import Path
from typing import Dict, List, Optional
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class F1DataLoader:
    """Load F1 data from CSV into PostgreSQL database"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database connection
        
        Args:
            db_config: Dictionary with keys: host, database, user, password, port
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a SQL query"""
        try:
            self.cursor.execute(query, params)
            if fetch:
                return self.cursor.fetchall()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_or_create_circuit(self, circuit_name: str, country: str) -> int:
        """Get circuit_id or create new circuit"""
        
        # Check if exists
        query = "SELECT circuit_id FROM circuits WHERE circuit_name = %s"
        result = self.execute_query(query, (circuit_name,), fetch=True)
        
        if result:
            return result[0][0]
        
        # Create new
        query = """
            INSERT INTO circuits (circuit_name, country) 
            VALUES (%s, %s) 
            RETURNING circuit_id
        """
        result = self.execute_query(query, (circuit_name, country), fetch=True)
        logger.info(f"Created circuit: {circuit_name}")
        return result[0][0]
    
    def get_or_create_team(self, team_name: str, year: int) -> int:
        """Get team_id or create new team"""
        
        query = "SELECT team_id FROM teams WHERE team_name = %s AND year = %s"
        result = self.execute_query(query, (team_name, year), fetch=True)
        
        if result:
            return result[0][0]
        
        query = """
            INSERT INTO teams (team_name, year) 
            VALUES (%s, %s) 
            RETURNING team_id
        """
        result = self.execute_query(query, (team_name, year), fetch=True)
        logger.info(f"Created team: {team_name} ({year})")
        return result[0][0]
    
    def get_or_create_driver(self, driver_code: str, driver_number: int, 
                            full_name: str, year: int, team_id: int) -> int:
        """Get driver_id or create new driver"""
        
        query = "SELECT driver_id FROM drivers WHERE driver_code = %s AND year = %s"
        result = self.execute_query(query, (driver_code, year), fetch=True)
        
        if result:
            return result[0][0]
        
        query = """
            INSERT INTO drivers (driver_code, driver_number, full_name, year, team_id) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING driver_id
        """
        result = self.execute_query(
            query, 
            (driver_code, driver_number, full_name, year, team_id), 
            fetch=True
        )
        logger.info(f"Created driver: {driver_code} ({year})")
        return result[0][0]
    
    def get_compound_id(self, compound_name: str) -> Optional[int]:
        """Get compound_id from compound name"""
        
        if pd.isna(compound_name) or compound_name is None:
            return None
        
        query = "SELECT compound_id FROM tire_compounds WHERE compound_name = %s LIMIT 1"
        result = self.execute_query(query, (compound_name.upper(),), fetch=True)
        
        if result:
            return result[0][0]
        return None
    
    def get_or_create_race(self, year: int, race_round: int, race_name: str, 
                          circuit_id: int, race_date: str) -> int:
        """Get race_id or create new race"""
        
        query = "SELECT race_id FROM races WHERE year = %s AND race_round = %s"
        result = self.execute_query(query, (year, race_round), fetch=True)
        
        if result:
            return result[0][0]
        
        query = """
            INSERT INTO races (year, race_round, race_name, circuit_id, race_date) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING race_id
        """
        result = self.execute_query(
            query, 
            (year, race_round, race_name, circuit_id, race_date), 
            fetch=True
        )
        logger.info(f"Created race: {year} {race_name}")
        return result[0][0]
    
    def load_lap_data_from_csv(self, csv_file: str):
        """Load lap data from CSV file into database"""
        
        logger.info(f"Loading lap data from {csv_file}")
        df = pd.read_csv(csv_file)
        
        logger.info(f"Loaded {len(df)} rows from CSV")
        
        # Track created entities
        race_map = {}  # (year, race_round) -> race_id
        driver_map = {}  # (driver_code, year) -> driver_id
        
        # Process in chunks
        chunk_size = 1000
        total_inserted = 0
        
        for chunk_start in range(0, len(df), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(df))
            chunk = df.iloc[chunk_start:chunk_end]
            
            lap_data = []
            weather_data = []
            
            for _, row in chunk.iterrows():
                try:
                    year = int(row['year'])
                    race_round = int(row['race_round'])
                    race_name = row['race_name']
                    circuit_name = row['circuit_name']
                    country = row['country']
                    
                    # Get or create entities
                    race_key = (year, race_round)
                    if race_key not in race_map:
                        circuit_id = self.get_or_create_circuit(circuit_name, country)
                        # Assume race date is today for now (should be updated with real data)
                        race_date = datetime.now().date()
                        race_id = self.get_or_create_race(
                            year, race_round, race_name, circuit_id, race_date
                        )
                        race_map[race_key] = race_id
                    else:
                        race_id = race_map[race_key]
                    
                    # Driver
                    driver_code = row['driver']
                    driver_key = (driver_code, year)
                    if driver_key not in driver_map:
                        team_name = row['team']
                        team_id = self.get_or_create_team(team_name, year)
                        driver_number = int(row['driver_number']) if pd.notna(row['driver_number']) else None
                        driver_id = self.get_or_create_driver(
                            driver_code, driver_number, driver_code, year, team_id
                        )
                        driver_map[driver_key] = driver_id
                    else:
                        driver_id = driver_map[driver_key]
                    
                    # Compound
                    compound_id = self.get_compound_id(row.get('compound'))
                    
                    # Prepare lap data
                    lap_data.append((
                        race_id,
                        driver_id,
                        int(row['lap_number']),
                        float(row['lap_time_seconds']) if pd.notna(row['lap_time_seconds']) else None,
                        float(row['sector1_time_seconds']) if pd.notna(row.get('sector1_time_seconds')) else None,
                        float(row['sector2_time_seconds']) if pd.notna(row.get('sector2_time_seconds')) else None,
                        float(row['sector3_time_seconds']) if pd.notna(row.get('sector3_time_seconds')) else None,
                        compound_id,
                        int(row['tyre_life']) if pd.notna(row.get('tyre_life')) else None,
                        int(row['stint']) if pd.notna(row.get('stint')) else 1,
                        bool(row.get('fresh_tyre', False)),
                        str(row.get('track_status', '1')),
                        bool(row.get('is_personal_best', False)),
                        bool(row.get('is_accurate', True))
                    ))
                    
                    # Prepare weather data if available
                    if pd.notna(row.get('air_temp')):
                        weather_data.append((
                            race_id,
                            int(row['lap_number']),
                            float(row['air_temp']) if pd.notna(row.get('air_temp')) else None,
                            float(row['track_temp']) if pd.notna(row.get('track_temp')) else None,
                            float(row['humidity']) if pd.notna(row.get('humidity')) else None,
                            bool(row.get('rainfall', False)),
                            float(row['wind_speed']) if pd.notna(row.get('wind_speed')) else None
                        ))
                
                except Exception as e:
                    logger.warning(f"Skipping row due to error: {e}")
                    continue
            
            # Batch insert lap data
            if lap_data:
                insert_query = """
                    INSERT INTO lap_times (
                        race_id, driver_id, lap_number, lap_time_seconds,
                        sector1_time_seconds, sector2_time_seconds, sector3_time_seconds,
                        compound_id, tyre_life, stint_number, fresh_tyre,
                        track_status, is_personal_best, is_accurate
                    ) VALUES %s
                    ON CONFLICT (race_id, driver_id, lap_number) DO NOTHING
                """
                execute_values(self.cursor, insert_query, lap_data)
                total_inserted += len(lap_data)
                self.conn.commit()
            
            # Batch insert weather data
            if weather_data:
                insert_query = """
                    INSERT INTO weather_conditions (
                        race_id, lap_number, air_temp_celsius, track_temp_celsius,
                        humidity_percent, rainfall, wind_speed_kmh
                    ) VALUES %s
                    ON CONFLICT (race_id, lap_number) DO NOTHING
                """
                execute_values(self.cursor, insert_query, weather_data)
                self.conn.commit()
            
            logger.info(f"Processed {chunk_end}/{len(df)} rows")
        
        logger.info(f"Successfully inserted {total_inserted} lap records")
    
    def load_pit_data_from_csv(self, csv_file: str):
        """Load pit stop data from CSV file into database"""
        
        logger.info(f"Loading pit stop data from {csv_file}")
        df = pd.read_csv(csv_file)
        
        pit_data = []
        
        for _, row in df.iterrows():
            try:
                # Get race_id
                query = "SELECT race_id FROM races WHERE year = %s AND race_round = %s"
                result = self.execute_query(
                    query, 
                    (int(row['year']), int(row['race_round'])), 
                    fetch=True
                )
                if not result:
                    continue
                race_id = result[0][0]
                
                # Get driver_id
                query = "SELECT driver_id FROM drivers WHERE driver_code = %s AND year = %s"
                result = self.execute_query(
                    query, 
                    (row['driver'], int(row['year'])), 
                    fetch=True
                )
                if not result:
                    continue
                driver_id = result[0][0]
                
                pit_data.append((
                    race_id,
                    driver_id,
                    int(row['lap']),
                    int(row['stop_number']),
                    float(row['duration_seconds'])
                ))
            
            except Exception as e:
                logger.warning(f"Skipping pit stop row due to error: {e}")
                continue
        
        # Batch insert
        if pit_data:
            insert_query = """
                INSERT INTO pit_stops (
                    race_id, driver_id, lap_number, stop_number, duration_seconds
                ) VALUES %s
            """
            execute_values(self.cursor, insert_query, pit_data)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(pit_data)} pit stop records")
    
    def calculate_all_stint_metrics(self):
        """Calculate stint metrics for all races"""
        
        logger.info("Calculating stint metrics...")
        
        query = """
            SELECT DISTINCT race_id, driver_id, stint_number
            FROM lap_times
            ORDER BY race_id, driver_id, stint_number
        """
        
        stints = self.execute_query(query, fetch=True)
        
        for race_id, driver_id, stint_number in stints:
            try:
                self.cursor.execute(
                    "SELECT calculate_stint_metrics(%s, %s, %s)",
                    (race_id, driver_id, stint_number)
                )
                self.conn.commit()
            except Exception as e:
                logger.warning(f"Failed to calculate metrics for stint: {e}")
                self.conn.rollback()
        
        logger.info(f"Calculated metrics for {len(stints)} stints")


def main():
    """Main execution function"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'f1_tire_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    # Initialize loader
    loader = F1DataLoader(db_config)
    
    try:
        loader.connect()
        
        # Load lap data
        data_dir = Path('./data')
        lap_files = list(data_dir.glob('f1_lap_data_*.csv'))
        
        for lap_file in lap_files:
            logger.info(f"\nProcessing {lap_file.name}")
            loader.load_lap_data_from_csv(str(lap_file))
        
        # Load pit stop data
        pit_files = list(data_dir.glob('f1_pit_data_*.csv'))
        
        for pit_file in pit_files:
            logger.info(f"\nProcessing {pit_file.name}")
            loader.load_pit_data_from_csv(str(pit_file))
        
        # Calculate stint metrics
        loader.calculate_all_stint_metrics()
        
        logger.info("\nData loading complete!")
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise
    
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()