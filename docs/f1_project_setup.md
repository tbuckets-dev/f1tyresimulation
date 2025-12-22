# F1 Tire Degradation Project - Setup Guide

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- AWS account (or other cloud provider)
- Git

## Project Structure

```
f1-tire-degradation/
├── data/                      # Raw data storage
├── fastf1_cache/             # FastF1 cache directory
├── scripts/
│   ├── collect_data.py       # Data collection script
│   ├── load_data.py          # Database loader script
│   └── predict.py            # Prediction model (to be created)
├── sql/
│   └── schema.sql            # Database schema
├── terraform/                # IaC files
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions pipeline
├── requirements.txt
├── .env.example
└── README.md
```

## Step 1: Local Environment Setup

### 1.1 Clone Repository and Setup Python Environment

```bash
# Create project directory
mkdir f1-tire-degradation
cd f1-tire-degradation

# Initialize git
git init
git remote add origin <your-repo-url>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Requirements.txt

```txt
# Data Collection
fastf1==3.2.0
requests==2.31.0
pandas==2.1.4
numpy==1.26.2

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Machine Learning
scikit-learn==1.3.2
scipy==1.11.4

# Visualization (optional)
matplotlib==3.8.2
seaborn==0.13.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# AWS SDK
boto3==1.34.10

# Configuration
python-dotenv==1.0.0
```

### 1.3 Environment Variables

Create `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=f1_tire_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

# AWS Configuration (for later)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Step 2: Database Setup

### 2.1 Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### 2.2 Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell:
CREATE DATABASE f1_tire_db;
CREATE USER f1_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE f1_tire_db TO f1_user;
\q
```

### 2.3 Initialize Schema

```bash
# Run schema creation
psql -U f1_user -d f1_tire_db -f sql/schema.sql
```

## Step 3: Data Collection

### 3.1 Test Data Collection (Single Race)

```bash
# Edit collect_data.py to collect just one race first
python scripts/collect_data.py --year 2023 --race 1 --max-races 1
```

### 3.2 Full Season Collection

```bash
# Collect full 2023 season
python scripts/collect_data.py --year 2023

# Collect multiple years (will take longer)
python scripts/collect_data.py --years 2021 2022 2023
```

**Expected time:** 
- Single race: ~2-3 minutes
- Full season: ~30-45 minutes
- Three seasons: ~2-3 hours

### 3.3 Load Data into Database

```bash
python scripts/load_data.py
```

## Step 4: Docker Setup

### 4.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "app/main.py"]
```

### 4.2 Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: f1_tire_db
      POSTGRES_USER: f1_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  app:
    build: .
    depends_on:
      - db
    environment:
      DB_HOST: db
      DB_NAME: f1_tire_db
      DB_USER: f1_user
      DB_PASSWORD: ${DB_PASSWORD}
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data

volumes:
  postgres_data:
```

### 4.3 Test Docker Setup

```bash
# Build image
docker-compose build

# Run services
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Step 5: Verify Installation

### 5.1 Check Database

```bash
psql -U f1_user -d f1_tire_db

-- Check tables
\dt

-- Check sample data
SELECT COUNT(*) FROM lap_times;
SELECT COUNT(*) FROM races;
SELECT * FROM vw_lap_details LIMIT 10;

-- Check stint metrics
SELECT * FROM vw_stint_analysis 
WHERE year = 2023 
ORDER BY degradation_rate DESC 
LIMIT 10;
```

### 5.2 Run Tests

```bash
# Install test data (small subset)
pytest tests/ -v

# Check code coverage
pytest --cov=scripts tests/
```

## Step 6: Next Steps

After completing local setup, you'll be ready to:

1. **Week 4**: Set up Terraform for AWS infrastructure
2. **Week 5-6**: Create multi-environment deployments
3. **Week 7-8**: Build CI/CD pipeline
4. **Week 9+**: Add advanced features

## Troubleshooting

### FastF1 Cache Issues

```bash
# Clear cache if you encounter errors
rm -rf fastf1_cache/*
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql -U f1_user -d f1_tire_db -h localhost

# Reset password if needed
ALTER USER f1_user WITH PASSWORD 'new_password';
```

### Memory Issues with Data Collection

If collecting multiple seasons causes memory issues:

```python
# In collect_data.py, process one race at a time
# and clear cache after each race
fastf1.Cache.clear_cache()
```

## Useful Commands

```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # macOS

# View running Docker containers
docker ps

# Access database in Docker
docker-compose exec db psql -U f1_user -d f1_tire_db

# Tail application logs
docker-compose logs -f app

# Remove all Docker volumes (clean slate)
docker-compose down -v
```

## Additional Resources

- **FastF1 Documentation**: https://docs.fastf1.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Docker Documentation**: https://docs.docker.com/
- **Ergast API**: http://ergast.com/mrd/

## Cost Estimates (AWS)

**Month 1 (Local Development)**: $0
**Month 2-3 (Cloud Deployment)**:
- EC2 t3.small (dev): ~$15/month
- RDS db.t3.micro: ~$15/month
- S3 storage (100GB): ~$2/month
- Data transfer: ~$5/month
- **Total**: ~$40-60/month

Use `terraform destroy` when not actively developing to minimize costs!
