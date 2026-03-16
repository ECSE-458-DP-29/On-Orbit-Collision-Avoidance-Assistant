# Docker Setup Guide - OOCAA

This guide explains how to run the On-Orbit Collision Avoidance Assistant (OOCAA) using Docker and Docker Compose.

## Prerequisites

- **Docker** (version 20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (version 2.0+) - Usually included with Docker Desktop

Verify installation:
```bash
docker --version
docker compose --version
```

## Quick Start (Recommended)

### 1. Setup Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration (especially `DB_PASSWORD`):
```env
DB_NAME=oocaa_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Build and Start Containers

```bash
# Build images and start containers
docker compose up -d

# Check status
docker compose ps
```

This will:
- Build the Django application image
- Start PostgreSQL database
- Run migrations automatically
- Start the Django development server

### 3. Access the Application

Open your browser and go to: **http://localhost:8000**

### 4. Create Admin User (First Time)

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to create your admin account.

## Useful Commands

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web      # Django logs
docker compose logs -f db       # Database logs
```

### Run Django Commands
```bash
# Migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Shell
docker compose exec web python manage.py shell
```

### Database Management
```bash
# Connect to PostgreSQL directly
docker compose exec db psql -U postgres oocaa_db

# Backup database
docker compose exec db pg_dump -U postgres oocaa_db > backup.sql

# Restore database
docker compose exec -T db psql -U postgres oocaa_db < backup.sql
```

### Stop and Clean Up
```bash
# Stop containers (data persists)
docker compose stop

# Start containers again
docker compose start

# Stop and remove containers (data persists in volumes)
docker compose down

# Remove everything including data
docker compose down -v

# Rebuild images
docker compose build --no-cache
```

## MATLAB Engine Support

To enable MATLAB Engine support in the container:

### Option 1: Build with MATLAB Support

Install MATLAB in your base image. Update the `Dockerfile`:

```dockerfile
# Add after system dependencies installation
RUN apt-get install -y --no-install-recommends \
    matlab-runtime  # Or install full MATLAB if available
```

### Option 2: Mount MATLAB Host Installation

If MATLAB is installed on your host machine:

```bash
# Modify docker-compose.yml to mount MATLAB
volumes:
  - /usr/local/MATLAB/R2024a:/matlab:ro  # Adjust path as needed
```

Then in the container, configure the Python MATLAB Engine connection.

## Production Deployment

For production, make these changes:

### 1. Update Settings
```bash
# .env
DEBUG=False
SECRET_KEY=your-secure-key-here  # Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 2. Use Gunicorn Instead of Development Server

Replace the `CMD` in `docker-compose.yml`:
```yaml
web:
  command: >
    sh -c "python manage.py migrate &&
           gunicorn OOCAA.wsgi:application --bind 0.0.0.0:8000"
```

Install gunicorn:
```bash
pip install gunicorn
# Add to requirements.txt
```

### 3. Add Nginx Reverse Proxy (Optional)

Create `nginx.conf`:
```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /app/staticfiles/;
    }
}
```

Add to `docker-compose.yml`:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - static_volume:/app/staticfiles:ro
  depends_on:
    - web
```

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```
Solution:
```bash
# Wait for database to be ready
docker compose logs db
# Restart web service
docker compose restart web
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
  - "5433:5432"  # Use 5433 for database
```

### Static Files Not Loading
```bash
# Collect static files in container
docker compose exec web python manage.py collectstatic --noinput

# Verify volume mount
docker compose exec web ls -la /app/staticfiles/
```

### Permission Denied Errors
```bash
# Fix file permissions
docker compose exec web chown -R 1000:1000 /app
```

## Network Configuration

Both services run on the default `oocaa_network`:
- **Web Service**: `oocaa_web:8000` (internally)
- **Database Service**: `db:5432` (internally)

They can communicate using these hostnames inside containers.

## Performance Tips

1. **Use volumes** for database persistence (already configured)
2. **Limit container resources** in `docker-compose.yml`:
   ```yaml
   web:
     deploy:
       resources:
         limits:
           cpus: '1'
           memory: 1G
   ```

3. **Enable Docker BuildKit** for faster builds:
   ```bash
   DOCKER_BUILDKIT=1 docker compose build
   ```

## Next Steps

- Upload CDM files to populate the database
- Configure 2FA authentication
- Set up backup strategy
- Deploy to your production environment

For more help, see the main [README.md](README.md) or check Django documentation at https://docs.djangoproject.com/
