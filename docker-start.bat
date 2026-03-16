@echo off
REM OOCAA Docker Startup Script for Windows
REM This script simplifies common Docker operations for OOCAA

setlocal enabledelayedexpansion

REM Colors are not easily available in Windows batch, so we'll just use text
echo.
echo ========================================
echo OOCAA Docker Control - Windows
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    echo Visit: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Setup environment if needed
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo [+] .env file created from .env.example
        echo [!] Please edit .env with your configuration
        pause
    )
)

REM Show menu
:menu
echo.
echo OOCAA Docker Control
echo ========================================
echo 1. Start containers (build if needed)
echo 2. Stop containers
echo 3. View logs
echo 4. Create superuser
echo 5. Run migrations
echo 6. Access web shell
echo 7. Access database shell
echo 8. Restart containers
echo 9. Clean everything (WARNING: deletes data)
echo 10. Exit
echo.

set /p choice="Choose an option (1-10): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto logs
if "%choice%"=="4" goto superuser
if "%choice%"=="5" goto migrate
if "%choice%"=="6" goto webshell
if "%choice%"=="7" goto dbshell
if "%choice%"=="8" goto restart
if "%choice%"=="9" goto clean
if "%choice%"=="10" goto end

echo Invalid option. Please try again.
goto menu

:start
echo.
echo Starting Docker containers...
docker compose up -d
if errorlevel 1 (
    echo Error starting containers
    pause
    goto menu
)
echo [+] Containers started
echo [+] Access application at http://localhost:8000
timeout /t 3
goto menu

:stop
echo.
docker compose stop
echo [+] Containers stopped
timeout /t 2
goto menu

:logs
echo.
echo Showing logs (Press Ctrl+C to exit)...
docker compose logs -f
goto menu

:superuser
echo.
echo Creating superuser...
docker compose exec web python manage.py createsuperuser
goto menu

:migrate
echo.
echo Running migrations...
docker compose exec web python manage.py migrate
echo [+] Migrations completed
timeout /t 2
goto menu

:webshell
echo.
echo Entering Django shell (type 'exit()' to exit)...
docker compose exec web python manage.py shell
goto menu

:dbshell
echo.
echo Entering PostgreSQL shell (type 'exit' to exit)...
docker compose exec db psql -U postgres oocaa_db
goto menu

:restart
echo.
docker compose restart
echo [+] Containers restarted
timeout /t 2
goto menu

:clean
echo.
set /p confirm="This will delete all data. Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    docker compose down -v
    echo [+] Cleaned up all containers and data
) else (
    echo [!] Cancelled
)
timeout /t 2
goto menu

:end
echo.
echo Goodbye!
exit /b 0
