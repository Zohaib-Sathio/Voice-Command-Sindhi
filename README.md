# FortVoice UBL - FastAPI Voice Commands API

A FastAPI-based voice command API for banking operations with audio transcription, intent classification, and amount extraction capabilities.

## Features

- 🎤 Audio transcription using OpenAI Whisper
- 🤖 Intent classification with ML models
- 💰 Amount extraction from voice commands
- 🌐 Multilingual support (Urdu and English)
- 📊 Database integration with MySQL
- 🔒 Rate limiting and security features

## Prerequisites

- Docker and Docker Compose installed on your machine
- Required environment variables (see Configuration section)

## Quick Start with Docker

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fastapi-fortvoice-ubl
   ```

2. **Create a `.env` file** in the root directory with your configuration:
   ```env
   # Database Configuration
   DB_HOST=your_db_host
   DB_PORT=3306
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=fortvoice_db
   DB_CHARSET=utf8mb4

   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

   The API will be available at `http://localhost:8000`

### Option 2: Using Docker directly

1. **Build the Docker image:**
   ```bash
   docker build -t fastapi-fortvoice:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name fastapi-fortvoice \
     -p 8000:8000 \
     -e DB_HOST=your_db_host \
     -e DB_PORT=3306 \
     -e DB_USER=your_db_user \
     -e DB_PASSWORD=your_db_password \
     -e DB_NAME=fortvoice_db \
     -e SUPABASE_URL=your_supabase_url \
     -e SUPABASE_KEY=your_supabase_key \
     -e OPENAI_API_KEY=your_openai_api_key \
     -v $(pwd)/src/transcription_audio_files:/app/src/transcription_audio_files \
     fastapi-fortvoice:latest
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - API Endpoints: http://localhost:8000/api/

### Pulling from Docker Hub

If you've pushed your image to Docker Hub:

```bash
docker pull <your-dockerhub-username>/fastapi-fortvoice:latest
docker run -d \
  --name fastapi-fortvoice \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/src/transcription_audio_files:/app/src/transcription_audio_files \
  <your-dockerhub-username>/fastapi-fortvoice:latest
```

## Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | MySQL database host | `localhost` |
| `DB_PORT` | MySQL database port | `3306` |
| `DB_USER` | MySQL database user | `root` |
| `DB_PASSWORD` | MySQL database password | (empty) |
| `DB_NAME` | MySQL database name | `fortvoice_db` |
| `DB_CHARSET` | Database character set | `utf8mb4` |
| `SUPABASE_URL` | Supabase project URL | (required) |
| `SUPABASE_KEY` | Supabase API key | (required) |
| `OPENAI_API_KEY` | OpenAI API key for transcription | (required) |

## Local Development (Without Docker)

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (create a `.env` file)

4. **Run the application:**
   ```bash
   python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once the container is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
fastapi-fortvoice-ubl/
├── src/
│   ├── app.py                 # FastAPI application entry point
│   ├── models/                # ML models and database models
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility functions and configurations
│   └── transcription_audio_files/  # Audio file storage
├── public/                    # Static files
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Troubleshooting

### Container won't start

1. Check if port 8000 is already in use:
   ```bash
   docker ps
   # Stop any conflicting containers or change the port mapping
   ```

2. Verify environment variables are set correctly:
   ```bash
   docker exec fastapi-fortvoice env | grep -E "DB_|OPENAI"
   ```

### Database connection issues

- Ensure your database is accessible from the Docker container
- If using Docker Compose with the MySQL service, the host should be `mysql` instead of `localhost`
- Check database credentials and network connectivity

### Missing models or files

- Ensure all `.pkl` model files are present in `src/models/`
- Check that the volumes are mounted correctly

## Building and Pushing to Docker Hub

To share your image with others:

### Using the build script (recommended)

**On Linux/Mac:**
```bash
chmod +x docker-build.sh
./docker-build.sh latest <your-dockerhub-username>
```

**On Windows:**
```cmd
docker-build.bat latest <your-dockerhub-username>
```

### Manual build and push

1. **Log in to Docker Hub:**
   ```bash
   docker login
   ```

2. **Build the image:**
   ```bash
   docker build -t fastapi-fortvoice:latest .
   ```

3. **Tag your image:**
   ```bash
   docker tag fastapi-fortvoice:latest <your-username>/fastapi-fortvoice:latest
   ```

4. **Push to Docker Hub:**
   ```bash
   docker push <your-username>/fastapi-fortvoice:latest
   ```

## License

[Add your license information here]

## Support

For issues and questions, please open an issue in the repository.

