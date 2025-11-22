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
- **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 5. Apply Migrations
Set up the database by applying migrations:
```bash
python manage.py migrate
```

### 6. Run the Development Server
Start the Django development server:
```bash
python manage.py runserver
```

### 7. Deactivate the Virtual Environment (Optional)
When you're done working, deactivate the virtual environment:
```bash
deactivate
```

## Additional Notes
- Ensure you have Python 3.8+ installed on your system.
- If `pip` is outdated, upgrade it using:
  ```bash
  python -m pip install --upgrade pip
  ```

## Project Overview
- This project is a Django-based application for managing Conjunction Data Messages (CDMs) and related space object data.
- For more details, refer to the documentation in the `docs/` folder.
