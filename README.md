# Fabric SQL Admin Manager

[![Build and deploy Python app to Azure Web App - SQLAdminMgmt](https://github.com/PeakMade/SQLAdminMgmt/actions/workflows/main_sqladminmgmt.yml/badge.svg)](https://github.com/PeakMade/SQLAdminMgmt/actions/workflows/main_sqladminmgmt.yml)

Flask web application for managing the APP_ADMINS table in Microsoft Fabric SQL. Provides both a web UI for manual administration and a REST API for programmatic access from other applications.

## Features

- **Hybrid Access**: Web UI for manual management + REST API for programmatic access
- **Dual Authentication**: Azure AD for web users, API keys for app-to-app communication
- **Azure AD Authentication**: Secure login with Microsoft identity platform
- **Fabric SQL Connection**: Service principal authentication to Fabric SQL
- **CRUD Operations**: Create, Read, Update, Delete admin records
- **Modern UI**: Clean, responsive interface matching your existing apps
- **CORS Support**: Cross-origin API access for distributed applications
- **Client Library**: Ready-to-use Python client for easy integration

## Documentation Structure

This repository includes comprehensive documentation for different use cases:

- **[README.md](README.md)** (this file) - Overview, installation, and basic usage
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide with architecture overview
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete REST API reference
- **[AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)** - Detailed Azure deployment guide
- **[INTEGRATION_EXAMPLE.py](INTEGRATION_EXAMPLE.py)** - Code examples for integrating this API into your Flask apps
- **[fabric_admin_client.py](fabric_admin_client.py)** - Python client library for easy API access

## Prerequisites

- Python 3.8+
- ODBC Driver 17 or 18 for SQL Server
- Azure AD app registration for user authentication
- Service Principal with access to Fabric SQL

## Installation

1. **Clone or navigate to the repository**:
   ```powershell
   cd "c:\Users\ffree\OneDrive - PeakMade Real Estate\Documents\git\Test SQL"
   ```

2. **Create a virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`:
     ```powershell
     Copy-Item .env.example .env
     ```
   - Update the values in `.env` with your Azure AD and Fabric SQL details (see Configuration section below)

## Configuration

The application requires several environment variables to be configured in a `.env` file. Use `.env.example` as a template.

### Azure AD App Registration (User Authentication)

Create an app registration in Azure AD for user login:

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Create a new registration
3. Add redirect URI: `http://localhost:5000/auth/callback` (local) or your deployed URL
4. Create a client secret
5. Update `.env` with:
   - `AZURE_AD_CLIENT_ID`
   - `AZURE_AD_CLIENT_SECRET`
   - `AZURE_AD_TENANT_ID`
   - `AZURE_AD_REDIRECT_URI`

### Service Principal (Fabric SQL Connection)

Configure a service principal with access to your Fabric SQL database:

1. Create a service principal in Azure AD (or use an existing one)
2. Grant it access to your Fabric workspace and SQL database
3. Update `.env` with:
   - `FABRIC_CLIENT_ID`
   - `FABRIC_CLIENT_SECRET`
   - `FABRIC_TENANT_ID`
   - `FABRIC_SERVER`
   - `FABRIC_DATABASE`

### API Keys (For Programmatic Access)

Configure API keys to allow other applications to access the REST API:

1. Generate secure API keys for each application that needs access
2. Update `.env` with:
   - `API_KEYS=APP1:key1,APP2:key2,APP3:key3`
   
**Example:**
```
API_KEYS=CashForecast:abc123xyz,OtherApp:def456uvw
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

## Usage

1. **Start the application**:
   ```powershell
   python app.py
   ```

2. **Access the application**:
   - Open browser to `http://localhost:5000`
   - You'll be redirected to Azure AD login
   - After authentication, you'll see the admin management interface

3. **CRUD Operations**:
   - **Create**: Click "Add New Admin" button
   - **Read**: View all admins in the table
   - **Update**: Click "Edit" button on any row
   - **Delete**: Click "Delete" button (with confirmation)

## Database Schema

**APP_ADMINS Table**:
- `ID` (int, primary key) - Auto-generated
- `ADMIN_EMAIL` (varchar(256)) - Email address
- `ADMIN_TYPE` (varchar(256)) - Type of admin (e.g., Owner, Admin, ReadOnly)
- `APP_ID` (int) - Application identifier
- `APP_NAME` (varchar(256)) - Application name
- `DATE_CREATED` (datetime) - Auto-generated timestamp

## Deployment to Azure

This application is designed to run on Azure App Service. For detailed deployment instructions, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

**Quick Deploy:**

1. **Create App Service**:
   ```powershell
   az webapp create --resource-group <your-rg> --plan <your-plan> --name <your-app-name> --runtime "PYTHON:3.11"
   ```

2. **Configure environment variables** in Azure Portal:
   - Go to App Service > Configuration > Application settings
   - Add all variables from `.env` file

3. **Deploy code**:
   ```powershell
   az webapp up --name <your-app-name> --resource-group <your-rg>
   ```

4. **Update redirect URI**:
   - In Azure AD app registration, add: `https://<your-app-name>.azurewebsites.net/auth/callback`
   - Update `AZURE_AD_REDIRECT_URI` in App Service configuration

For advanced deployment options, monitoring setup, and troubleshooting, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

## Using the API in Your Applications

### Option 1: Use the Client Library

Copy [fabric_admin_client.py](fabric_admin_client.py) to your project and use it:

```python
from fabric_admin_client import FabricAdminClient

# Initialize client
client = FabricAdminClient(
    api_url="http://localhost:5000",  # or your Azure URL
    api_key="your-api-key-here"
)

# Check if user is admin
if client.is_admin("user@example.com"):
    # Grant access
    pass

# Get all admins
admins = client.get_all_admins()

# Create a new admin
new_id = client.create_admin(
    admin_email="newadmin@example.com",
    admin_type="admin",
    app_id=1,
    app_name="My App"
)
```

### Option 2: Direct API Calls

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Integration Patterns

For complete integration examples including decorators, caching, and best practices, see [INTEGRATION_EXAMPLE.py](INTEGRATION_EXAMPLE.py).

## Security Notes

- Never commit `.env` file to source control
- Rotate secrets regularly
- Use Azure Key Vault for production secrets
- Implement proper authorization (group-based access control) as needed

## Troubleshooting

### ODBC Driver Not Found
Install Microsoft ODBC Driver for SQL Server:
- Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Install ODBC Driver 17 or 18 for SQL Server

### Authentication Issues
- Verify Azure AD app registration configuration
- Check redirect URI matches exactly (including http/https)
- Ensure client secret hasn't expired
- Confirm tenant ID is correct

### Database Connection Issues
- Verify service principal has access to Fabric workspace
- Check Fabric SQL endpoint is correct
- Ensure Fabric SQL allows external connections
- Test connection using the `/test-connection` endpoint (requires login)

### API Access Issues
- Verify API key is included in `X-API-Key` header
- Check API key is correctly configured in `API_KEYS` environment variable
- Ensure CORS is properly configured for your origin

For more troubleshooting tips, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

## Next Steps

1. **Get Started**: Follow [QUICK_START.md](QUICK_START.md) for architecture overview and setup
2. **Integrate with Your Apps**: Check [INTEGRATION_EXAMPLE.py](INTEGRATION_EXAMPLE.py) for code patterns
3. **Deploy to Azure**: Use [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for production deployment
4. **API Reference**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for all API endpoints

## License

Internal use only - PeakMade Real Estate
