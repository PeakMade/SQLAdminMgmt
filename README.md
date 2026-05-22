# Fabric SQL Admin Manager

Flask web application for managing the APP_ADMINS table in Microsoft Fabric SQL.

## Features

- **Azure AD Authentication**: Secure login with Microsoft identity platform
- **Fabric SQL Connection**: Service principal authentication to Fabric SQL
- **CRUD Operations**: Create, Read, Update, Delete admin records
- **Modern UI**: Clean, responsive interface matching your existing apps
- **Single Sign-On**: Leverages existing browser sessions

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
   - Copy `.env.example` to `.env` (already done)
   - Update the `AZURE_AD_*` variables with your web app registration details

## Configuration

### Azure AD App Registration (User Authentication)

Create an app registration in Azure AD for user login:

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Create a new registration
3. Add redirect URI: `http://localhost:5000/auth/callback` (local) or your deployed URL
4. Create a client secret
5. Update `.env` with:
   - `AZURE_AD_CLIENT_ID`
   - `AZURE_AD_CLIENT_SECRET`
   - `AZURE_AD_REDIRECT_URI`

### Service Principal (Already Configured)

The Fabric SQL connection is already configured with your service principal in `.env`.

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

Deploy as an Azure App Service (Web App):

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

## Security Notes

- Never commit `.env` file to source control
- Rotate secrets regularly
- Use Azure Key Vault for production secrets
- Implement proper authorization (group-based access control) as needed

## Troubleshooting

### ODBC Driver Not Found
Install from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Authentication Issues
- Verify Azure AD app registration configuration
- Check redirect URI matches exactly
- Ensure client secret hasn't expired

### Database Connection Issues
- Verify service principal has access to Fabric workspace
- Check Fabric SQL endpoint is correct
- Ensure Fabric SQL allows external connections

## License

Internal use only - PeakMade Real Estate
