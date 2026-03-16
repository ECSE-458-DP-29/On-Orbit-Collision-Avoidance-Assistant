# On-Orbit Collision Avoidance Assistant (OOCAA)

## Quick Start Options

### Option 1: Docker
For a containerized setup that works on any environment:

**Windows:**
```bash
docker-start.bat
```

**Linux/Mac:**
```bash
bash docker-start.sh
```

Then open http://localhost:8000

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for more details.

### Option 2: Local Setup (Manual)
Follow the traditional setup process below.

---

## Setup (Local Installation)

Follow these steps to set up the project on your local machine:

### 1. Clone the Repository
```bash
git clone <repository-url>
cd On-Orbit-Collision-Avoidance-Assistant
```

### 2. Create a Virtual Environment
Create a Python virtual environment to isolate dependencies:
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
If you encounter an error about scripts being disabled, follow these steps:

#### a. Check the Current Execution Policy
Run the following command in PowerShell:
```powershell
Get-ExecutionPolicy
```

#### b. Temporarily Allow Script Execution
If the policy is set to `Restricted`, temporarily allow script execution:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### c. Activate the Virtual Environment
- **Windows**:
  ```powershell
  venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install the required Python packages using the `requirements.txt` file located in the `OOCAA` directory:
```bash
pip install -r OOCAA/requirements.txt
```

### 5. Apply Migrations
The `manage.py` file is located in the `OOCAA` directory. Navigate to this directory:
```bash
cd OOCAA
```

If migrations have not been created yet, generate them:
```bash
python manage.py makemigrations
```

Then apply the migrations:
```bash
python manage.py migrate
```

### 6. Create a Superuser
To access the Django admin interface, create a superuser account. Run the following command:
```bash
python manage.py createsuperuser
```
You will be prompted to enter the following details:
- **Username**: Choose a username for the admin account (preferably `admin`)
- **Email**: You can press Enter to skip this field.
- **Password**: Enter a password with at least 8 characters.

### 7. Run the Development Server
Start the Django development server:
```bash
python manage.py runserver
```
Once the superuser is created and the development server is running, you can log in to the admin interface at:
[http://localhost:8000/admin](http://localhost:8000/admin)


## Additional Notes
- Ensure you have Python 3.8+ installed on your system.
- If `pip` is outdated, upgrade it using:
  ```bash
  python -m pip install --upgrade pip
  ```
