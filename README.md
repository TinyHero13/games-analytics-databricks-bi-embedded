# Games Analytics - Databricks BI Embedded

A web application for embedding Databricks dashboard. This project provides a dashboard for analyzing gaming data with embedded Databricks Business Intelligence capabilities.

## Technologies used

- **Backend**: Python with built-in HTTP server
- **Frontend**: Vanilla JavaScript, HTML5, CSS
- **Dashboard**: Databricks embedded dashboards
- **Authentication**: Databricks Service Principal (OAuth 2.0)
- **Environment**: Environment variables for configuration

## Prerequisites

- Python 3.11 or higher
- Databricks workspace with dashboard access
- Service Principal with appropriate permissions
- Databricks dashboard ID

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/TinyHero13/games-analytics-databricks-bi-embedded.git
cd games-analytics-databricks-bi-embedded
```

### 2. Set up virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Configure environment variables

Create a `.env` file in the project root with the following configuration:

```env
# Databricks instance configuration
INSTANCE_URL=https://your-databricks-workspace.cloud.databricks.com
WORKSPACE_ID=your_workspace_id

# Dashboard configuration
DASHBOARD_ID=your_dashboard_id

# Service principal authentication
SERVICE_PRINCIPAL_ID=your_service_principal_id
SERVICE_PRINCIPAL_SECRET=your_service_principal_secret

# External viewer configuration
EXTERNAL_VIEWER_ID=your_external_viewer_id
EXTERNAL_VALUE=your_external_value

# Server configuration (optional)
PORT=3000
```

### 5. Run the application

```bash
python main.py
```

The application will be available at `http://localhost:3000`


## Databricks configuration

### Creating a service principal

1. **Access Databricks Admin Console**
   - Go to your Databricks workspace
   - Navigate to Admin Settings → Service Principals

2. **Create service principal**
   - Click "Add Service Principal"
   - Set a name for your service principal
   - Copy the `Application ID` (this is your `SERVICE_PRINCIPAL_ID`)

3. **Generate secret**
   - In the service principal details, go to "OAuth secrets"
   - Generate a new secret
   - Copy the secret value (this is your `SERVICE_PRINCIPAL_SECRET`)

4. **Grant permissions**
   - Assign workspace access to the service principal
   - Grant permissions to access the specific dashboard
   - Ensure the service principal has `CAN_USE` permission on the dashboard

## Project Structure

```
├── main.py                # Main server application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables 
├── static/
│   ├── style.css          # Application styles
│   └── dashboard.js       # Dashboard management logic
└── templates/
    └── index.html         # Main HTML template
```