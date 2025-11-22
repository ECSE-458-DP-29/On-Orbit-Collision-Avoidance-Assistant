# On-Orbit Collision Avoidance Assistant (OOCAA)

## Setup

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

### 6. Run the Development Server
Start the Django development server:
```bash
python manage.py runserver
```

## Additional Notes
- Ensure you have Python 3.8+ installed on your system.
- If `pip` is outdated, upgrade it using:
  ```bash
  python -m pip install --upgrade pip
  ```
