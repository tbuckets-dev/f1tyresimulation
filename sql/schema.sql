-- F1 Tire Degradation Database Schema
-- PostgreSQL 13+

-- ============================================
-- REFERENCE TABLES
-- ============================================

-- Circuits table
CREATE TABLE circuits (
    circuit_id SERIAL PRIMARY KEY,
    circuit_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    circuit_type VARCHAR(50), -- street, permanent, semi-permanent
    lap_distance_km DECIMAL(6,3),
    total_laps INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_circuits_country ON circuits(country);

-- Teams/Constructors table
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_code VARCHAR(10),
    year INTEGER NOT NULL,
    UNIQUE(team_name, year),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_year ON teams(year);

-- Drivers table
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    driver_code VARCHAR(3) NOT NULL, -- VER, HAM, etc.
    driver_number INTEGER,
    full_name VARCHAR(100),
    year INTEGER NOT NULL,
    team_id INTEGER REFERENCES teams(team_id),
    UNIQUE(driver_code, year),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drivers_year ON drivers(year);
CREATE INDEX idx_drivers_team ON drivers(team_id);

-- Tire compounds reference
CREATE TABLE tire_compounds (
    compound_id SERIAL PRIMARY KEY,
    compound_name VARCHAR(20) NOT NULL, -- SOFT, MEDIUM, HARD
    compound_code VARCHAR(5), -- C1, C2, C3, C4, C5
    color VARCHAR(20), -- Red, Yellow, White
    relative_performance INTEGER, -- 1 (hardest) to 5 (softest)
    UNIQUE(compound_name, compound_code)
);

-- Insert standard tire compounds
INSERT INTO tire_compounds (compound_name, compound_code, color, relative_performance) VALUES
('HARD', 'C1', 'White', 1),
('HARD', 'C2', 'White', 2),
('MEDIUM', 'C2', 'Yellow', 2),
('MEDIUM', 'C3', 'Yellow', 3),
('SOFT', 'C3', 'Red', 3),
('SOFT', 'C4', 'Red', 4),
('SOFT', 'C5', 'Red', 5),
('INTERMEDIATE', 'INT', 'Green', NULL),
('WET', 'WET', 'Blue', NULL);

-- ============================================
-- RACE EVENT TABLES
-- ============================================

-- Races table
CREATE TABLE races (
    race_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    race_round INTEGER NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    circuit_id INTEGER REFERENCES circuits(circuit_id),
    race_date DATE NOT NULL,
    race_time TIME,
    UNIQUE(year, race_round),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_races_year ON races(year);
CREATE INDEX idx_races_date ON races(race_date);
CREATE INDEX idx_races_circuit ON races(circuit_id);

-- ============================================
-- LAP DATA TABLES
-- ============================================

-- Main lap times table
CREATE TABLE lap_times (
    lap_id BIGSERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(race_id),
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
    lap_number INTEGER NOT NULL,
    lap_time_seconds DECIMAL(8,3) NOT NULL,
    sector1_time_seconds DECIMAL(6,3),
    sector2_time_seconds DECIMAL(6,3),
    sector3_time_seconds DECIMAL(6,3),
    compound_id INTEGER REFERENCES tire_compounds(compound_id),
    tyre_life INTEGER, -- Number of laps on this tire set
    stint_number INTEGER NOT NULL,
    fresh_tyre BOOLEAN DEFAULT FALSE,
    track_status VARCHAR(10), -- '1' = normal, '2' = yellow, '4' = safety car, etc.
    is_personal_best BOOLEAN DEFAULT FALSE,
    is_accurate BOOLEAN DEFAULT TRUE,
    lap_start_time TIMESTAMP,
    position INTEGER, -- Position at end of lap
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_race_driver_lap UNIQUE(race_id, driver_id, lap_number)
);

CREATE INDEX idx_lap_times_race ON lap_times(race_id);
CREATE INDEX idx_lap_times_driver ON lap_times(driver_id);
CREATE INDEX idx_lap_times_stint ON lap_times(race_id, driver_id, stint_number);
CREATE INDEX idx_lap_times_compound ON lap_times(compound_id);
CREATE INDEX idx_lap_times_tyre_life ON lap_times(tyre_life);

-- Weather conditions table
CREATE TABLE weather_conditions (
    weather_id BIGSERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(race_id),
    lap_number INTEGER NOT NULL,
    air_temp_celsius DECIMAL(5,2),
    track_temp_celsius DECIMAL(5,2),
    humidity_percent DECIMAL(5,2),
    rainfall BOOLEAN DEFAULT FALSE,
    wind_speed_kmh DECIMAL(5,2),
    wind_direction INTEGER, -- Degrees
    recorded_at TIMESTAMP,
    CONSTRAINT unique_race_lap_weather UNIQUE(race_id, lap_number)
);

CREATE INDEX idx_weather_race ON weather_conditions(race_id);

-- Pit stops table
CREATE TABLE pit_stops (
    pit_stop_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(race_id),
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
    lap_number INTEGER NOT NULL,
    stop_number INTEGER NOT NULL, -- 1st stop, 2nd stop, etc.
    duration_seconds DECIMAL(6,3) NOT NULL,
    time_of_day TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pit_stops_race ON pit_stops(race_id);
CREATE INDEX idx_pit_stops_driver ON pit_stops(driver_id);

-- ============================================
-- CALCULATED METRICS TABLES
-- ============================================

-- Tire degradation metrics per stint
CREATE TABLE stint_metrics (
    stint_metric_id BIGSERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(race_id),
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
    stint_number INTEGER NOT NULL,
    compound_id INTEGER REFERENCES tire_compounds(compound_id),
    stint_start_lap INTEGER NOT NULL,
    stint_end_lap INTEGER NOT NULL,
    total_laps INTEGER NOT NULL,
    first_lap_time_seconds DECIMAL(8,3),
    last_lap_time_seconds DECIMAL(8,3),
    avg_lap_time_seconds DECIMAL(8,3),
    median_lap_time_seconds DECIMAL(8,3),
    fastest_lap_time_seconds DECIMAL(8,3),
    degradation_rate DECIMAL(10,6), -- Seconds lost per lap
    total_time_loss DECIMAL(8,3), -- Total seconds lost over stint
    avg_track_temp DECIMAL(5,2),
    avg_air_temp DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_race_driver_stint UNIQUE(race_id, driver_id, stint_number)
);

CREATE INDEX idx_stint_metrics_race ON stint_metrics(race_id);
CREATE INDEX idx_stint_metrics_driver ON stint_metrics(driver_id);
CREATE INDEX idx_stint_metrics_compound ON stint_metrics(compound_id);

-- Model predictions table (for storing ML model predictions)
CREATE TABLE tire_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(race_id),
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
    compound_id INTEGER REFERENCES tire_compounds(compound_id),
    predicted_lap INTEGER NOT NULL,
    current_tyre_life INTEGER NOT NULL,
    predicted_lap_time DECIMAL(8,3) NOT NULL,
    predicted_degradation_rate DECIMAL(10,6),
    confidence_score DECIMAL(5,4), -- 0-1 confidence
    model_version VARCHAR(50) NOT NULL,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_race ON tire_predictions(race_id);
CREATE INDEX idx_predictions_model ON tire_predictions(model_version);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View for lap times with full context
CREATE VIEW vw_lap_details AS
SELECT 
    lt.lap_id,
    r.year,
    r.race_round,
    r.race_name,
    c.circuit_name,
    c.country,
    d.driver_code,
    d.full_name AS driver_name,
    t.team_name,
    lt.lap_number,
    lt.lap_time_seconds,
    lt.sector1_time_seconds,
    lt.sector2_time_seconds,
    lt.sector3_time_seconds,
    tc.compound_name,
    tc.compound_code,
    lt.tyre_life,
    lt.stint_number,
    lt.fresh_tyre,
    wc.track_temp_celsius,
    wc.air_temp_celsius,
    wc.humidity_percent,
    lt.track_status,
    lt.is_personal_best
FROM lap_times lt
JOIN races r ON lt.race_id = r.race_id
JOIN circuits c ON r.circuit_id = c.circuit_id
JOIN drivers d ON lt.driver_id = d.driver_id
JOIN teams t ON d.team_id = t.team_id
LEFT JOIN tire_compounds tc ON lt.compound_id = tc.compound_id
LEFT JOIN weather_conditions wc ON r.race_id = wc.race_id AND lt.lap_number = wc.lap_number;

-- View for stint analysis
CREATE VIEW vw_stint_analysis AS
SELECT 
    sm.stint_metric_id,
    r.year,
    r.race_name,
    c.circuit_name,
    d.driver_code,
    t.team_name,
    sm.stint_number,
    tc.compound_name,
    sm.total_laps,
    sm.first_lap_time_seconds,
    sm.last_lap_time_seconds,
    sm.degradation_rate,
    sm.total_time_loss,
    sm.avg_track_temp,
    ROUND((sm.last_lap_time_seconds - sm.first_lap_time_seconds)::NUMERIC, 3) AS time_delta,
    ROUND((sm.degradation_rate * sm.total_laps)::NUMERIC, 3) AS calculated_time_loss
FROM stint_metrics sm
JOIN races r ON sm.race_id = r.race_id
JOIN circuits c ON r.circuit_id = c.circuit_id
JOIN drivers d ON sm.driver_id = d.driver_id
JOIN teams t ON d.team_id = t.team_id
LEFT JOIN tire_compounds tc ON sm.compound_id = tc.compound_id;

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to circuits table
CREATE TRIGGER update_circuits_updated_at BEFORE UPDATE ON circuits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate stint metrics
CREATE OR REPLACE FUNCTION calculate_stint_metrics(
    p_race_id INTEGER,
    p_driver_id INTEGER,
    p_stint_number INTEGER
)
RETURNS void AS $$
BEGIN
    INSERT INTO stint_metrics (
        race_id, driver_id, stint_number, compound_id,
        stint_start_lap, stint_end_lap, total_laps,
        first_lap_time_seconds, last_lap_time_seconds,
        avg_lap_time_seconds, median_lap_time_seconds,
        fastest_lap_time_seconds, degradation_rate,
        total_time_loss, avg_track_temp, avg_air_temp
    )
    SELECT 
        p_race_id,
        p_driver_id,
        p_stint_number,
        MAX(lt.compound_id),
        MIN(lt.lap_number),
        MAX(lt.lap_number),
        COUNT(*),
        (SELECT lap_time_seconds FROM lap_times 
         WHERE race_id = p_race_id AND driver_id = p_driver_id 
         AND stint_number = p_stint_number ORDER BY lap_number LIMIT 1),
        (SELECT lap_time_seconds FROM lap_times 
         WHERE race_id = p_race_id AND driver_id = p_driver_id 
         AND stint_number = p_stint_number ORDER BY lap_number DESC LIMIT 1),
        AVG(lt.lap_time_seconds),
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lt.lap_time_seconds),
        MIN(lt.lap_time_seconds),
        -- Simple degradation calculation
        (MAX(lt.lap_time_seconds) - MIN(lt.lap_time_seconds)) / NULLIF(COUNT(*) - 1, 0),
        MAX(lt.lap_time_seconds) - MIN(lt.lap_time_seconds),
        AVG(wc.track_temp_celsius),
        AVG(wc.air_temp_celsius)
    FROM lap_times lt
    LEFT JOIN weather_conditions wc ON lt.race_id = wc.race_id AND lt.lap_number = wc.lap_number
    WHERE lt.race_id = p_race_id 
      AND lt.driver_id = p_driver_id 
      AND lt.stint_number = p_stint_number
      AND lt.is_accurate = TRUE
      AND lt.track_status = '1' -- Only normal track conditions
    GROUP BY p_race_id, p_driver_id, p_stint_number
    ON CONFLICT (race_id, driver_id, stint_number) 
    DO UPDATE SET
        total_laps = EXCLUDED.total_laps,
        avg_lap_time_seconds = EXCLUDED.avg_lap_time_seconds,
        degradation_rate = EXCLUDED.degradation_rate,
        total_time_loss = EXCLUDED.total_time_loss;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SAMPLE QUERIES
-- ============================================

-- Query 1: Average degradation rate by compound and circuit
-- 
-- SELECT 
--     c.circuit_name,
--     tc.compound_name,
--     AVG(sm.degradation_rate) as avg_degradation,
--     COUNT(*) as stint_count
-- FROM stint_metrics sm
-- JOIN races r ON sm.race_id = r.race_id
-- JOIN circuits c ON r.circuit_id = c.circuit_id
-- JOIN tire_compounds tc ON sm.compound_id = tc.compound_id
-- WHERE r.year = 2023
-- GROUP BY c.circuit_name, tc.compound_name
-- ORDER BY avg_degradation DESC;

-- Query 2: Find optimal tire strategy for a circuit
--
-- SELECT 
--     tc.compound_name,
--     AVG(sm.total_laps) as avg_stint_length,
--     AVG(sm.degradation_rate) as avg_degradation,
--     AVG(sm.total_time_loss) as avg_time_loss
-- FROM stint_metrics sm
-- JOIN races r ON sm.race_id = r.race_id
-- JOIN circuits c ON r.circuit_id = c.circuit_id
-- JOIN tire_compounds tc ON sm.compound_id = tc.compound_id
-- WHERE c.circuit_name = 'Monaco Grand Prix'
-- GROUP BY tc.compound_name;

-- Query 3: Driver performance on specific compound
--
-- SELECT 
--     d.driver_code,
--     COUNT(*) as laps_on_compound,
--     AVG(lt.lap_time_seconds) as avg_lap_time,
--     MIN(lt.lap_time_seconds) as best_lap_time
-- FROM lap_times lt
-- JOIN drivers d ON lt.driver_id = d.driver_id
-- JOIN tire_compounds tc ON lt.compound_id = tc.compound_id
-- WHERE tc.compound_name = 'SOFT'
--   AND lt.race_id IN (SELECT race_id FROM races WHERE year = 2023)
-- GROUP BY d.driver_code
-- ORDER BY avg_lap_time;