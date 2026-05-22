# Azure App Service Deployment Guide

## Quick Deploy to Azure App Service

### Prerequisites
- Azure subscription
- Azure CLI installed (or use Azure Portal)
- Your Azure AD app registration for user authentication

### Option 1: Deploy via Azure CLI

```powershell
# Login to Azure
az login

# Create resource group (if needed)
az group create --name rg-fabric-admin --location eastus

# Create App Service Plan (if needed)
az appservice plan create `
  --name plan-fabric-admin `
  --resource-group rg-fabric-admin `
  --sku B1 `
  --is-linux false

# Create Web App
az webapp create `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --plan plan-fabric-admin `
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --settings `
    SECRET_KEY="your-production-secret-key" `
    AZURE_AD_CLIENT_ID="your-webapp-client-id" `
    AZURE_AD_CLIENT_SECRET="your-webapp-client-secret" `
    AZURE_AD_TENANT_ID="your-tenant-id" `
    AZURE_AD_REDIRECT_URI="https://your-app-name-here.azurewebsites.net/auth/callback" `
    FABRIC_CLIENT_ID="your-service-principal-client-id" `
    FABRIC_TENANT_ID="your-tenant-id" `
    FABRIC_CLIENT_SECRET="your-service-principal-client-secret" `
    FABRIC_SERVER="your-fabric-server.database.fabric.microsoft.com" `
    FABRIC_DATABASE="your-database-name" `
    API_KEYS="APP1:your-api-key-here,APP2:another-api-key-here" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Deploy code
az webapp up `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --runtime "PYTHON:3.11"
```

### Option 2: Deploy via VS Code

1. Install Azure App Service extension
2. Right-click on project folder
3. Select "Deploy to Web App..."
4. Follow prompts
5. Configure environment variables in Azure Portal

### Option 3: Deploy via GitHub Actions

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'your-app-name-here'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## Post-Deployment Configuration

### 1. Update Azure AD Redirect URI

In Azure AD app registration, add:
```
https://your-app-name-here.azurewebsites.net/auth/callback
```

### 2. Configure CORS (if needed)

```powershell
az webapp cors add `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --allowed-origins "https://your-domain.com"
```

### 3. Enable HTTPS Only (Recommended)

```powershell
az webapp update `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --https-only true
```

### 4. Configure Custom Domain (Optional)

```powershell
az webapp config hostname add `
  --webapp-name your-app-name-here `
  --resource-group rg-fabric-admin `
  --hostname your-custom-domain.com
```

## ODBC Driver on Azure App Service

**No action required!** Azure App Service on Windows includes:
- ODBC Driver 17 for SQL Server ✓
- ODBC Driver 18 for SQL Server ✓

The application automatically detects and uses the available driver.

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Flask session encryption | Generate random string |
| `AZURE_AD_CLIENT_ID` | User authentication | From Azure AD app registration |
| `AZURE_AD_CLIENT_SECRET` | User authentication | From Azure AD app registration |
| `AZURE_AD_TENANT_ID` | Your tenant ID | your-tenant-id-here |
| `AZURE_AD_REDIRECT_URI` | Auth callback URL | https://yourapp.azurewebsites.net/auth/callback |
| `FABRIC_CLIENT_ID` | Service principal for DB | Already configured |
| `FABRIC_TENANT_ID` | Service principal tenant | Already configured |
| `FABRIC_CLIENT_SECRET` | Service principal secret | Already configured |
| `FABRIC_SERVER` | Fabric SQL endpoint | Already configured |
| `FABRIC_DATABASE` | Database name | Already configured |

## Security Best Practices

### Use Azure Key Vault (Production)

Instead of storing secrets in App Settings:

```powershell
# Create Key Vault
az keyvault create `
  --name kv-fabric-admin `
  --resource-group rg-fabric-admin `
  --location eastus

# Store secrets
az keyvault secret set --vault-name kv-fabric-admin --name "FabricClientSecret" --value "your-secret"

# Enable managed identity for Web App
az webapp identity assign `
  --name your-app-name-here `
  --resource-group rg-fabric-admin

# Grant Key Vault access
az keyvault set-policy `
  --name kv-fabric-admin `
  --object-id <managed-identity-object-id> `
  --secret-permissions get list

# Reference in App Settings
az webapp config appsettings set `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --settings FABRIC_CLIENT_SECRET="@Microsoft.KeyVault(VaultName=kv-fabric-admin;SecretName=FabricClientSecret)"
```

## Monitoring & Logging

### Enable Application Insights

```powershell
az monitor app-insights component create `
  --app your-app-name-insights `
  --location eastus `
  --resource-group rg-fabric-admin `
  --application-type web

az webapp config appsettings set `
  --name your-app-name-here `
  --resource-group rg-fabric-admin `
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

### View Logs

```powershell
# Stream logs in real-time
az webapp log tail --name your-app-name-here --resource-group rg-fabric-admin

# Download logs
az webapp log download --name your-app-name-here --resource-group rg-fabric-admin
```

## Scaling

### Manual Scale

```powershell
az appservice plan update `
  --name plan-fabric-admin `
  --resource-group rg-fabric-admin `
  --sku P1V2
```

### Auto-scale (Optional)

```powershell
az monitor autoscale create `
  --resource-group rg-fabric-admin `
  --resource your-app-name-here `
  --resource-type Microsoft.Web/sites `
  --min-count 1 `
  --max-count 3 `
  --count 1
```

## Troubleshooting

### View Kudu Console
Visit: `https://your-app-name-here.scm.azurewebsites.net`

### Check Python Version
```
https://your-app-name-here.scm.azurewebsites.net/api/command
POST: python --version
```

### Check ODBC Drivers
In Kudu console:
```python
import pyodbc
print(pyodbc.drivers())
```

### Common Issues

1. **Authentication fails**: Verify redirect URI matches exactly
2. **Database connection fails**: Check service principal permissions in Fabric
3. **502 Bad Gateway**: Check application logs for startup errors

## Next Steps

After deployment:
1. Test authentication flow
2. Test database connectivity via `/test-connection` endpoint
3. Perform CRUD operations
4. Set up monitoring alerts
5. Configure backup strategy
