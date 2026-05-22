"""
Fabric SQL Database Service
Connects to Microsoft Fabric SQL using Service Principal authentication
"""

import os
import logging
import pyodbc
import struct
from typing import Dict, Any, Optional, List
from azure.identity import ClientSecretCredential

logger = logging.getLogger(__name__)


class FabricDatabase:
    """Handle Fabric SQL connections and queries using Service Principal"""
    
    def __init__(self):
        self.server = os.environ.get('FABRIC_SERVER', '')
        self.database = os.environ.get('FABRIC_DATABASE', '')
        self.client_id = os.environ.get('FABRIC_CLIENT_ID', '')
        self.client_secret = os.environ.get('FABRIC_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('FABRIC_TENANT_ID', '')
        
        # Azure SQL resource identifier
        self.sql_resource = "https://database.windows.net/"
        
    def _get_access_token(self):
        """Get access token for Azure SQL using service principal"""
        try:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            token = credential.get_token(f"{self.sql_resource}.default")
            return token.token
            
        except Exception as e:
            logger.error(f"Failed to acquire access token: {str(e)}")
            raise
    
    def _get_connection(self):
        """Create a new database connection using token-based authentication"""
        try:
            # Get access token
            access_token = self._get_access_token()
            
            # Find available ODBC driver - try modern drivers first, fall back to SQL Server
            preferred_drivers = [
                'ODBC Driver 18 for SQL Server',
                'ODBC Driver 17 for SQL Server',
                'ODBC Driver 13 for SQL Server',
                'SQL Server'  # Legacy driver, doesn't support token auth
            ]
            
            # Get all available drivers
            installed_drivers = pyodbc.drivers()
            logger.debug(f"All installed drivers: {installed_drivers}")
            
            # Find the first preferred driver that's installed
            driver = None
            for preferred in preferred_drivers:
                for installed in installed_drivers:
                    if preferred == installed:
                        driver = installed
                        break
                if driver:
                    break
            
            if not driver:
                raise Exception(
                    "No SQL Server ODBC driver found. "
                    "Please install 'ODBC Driver 17 for SQL Server' or newer. "
                    f"Available drivers: {installed_drivers}"
                )
            
            logger.info(f"Selected ODBC driver: {driver}")
            
            # Build connection string for token authentication
            connection_string = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
            
            # Convert token to the format expected by pyodbc
            token_bytes = access_token.encode('utf-16-le')
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
            
            # SQL_COPT_SS_ACCESS_TOKEN = 1256
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            
            connection = pyodbc.connect(
                connection_string,
                attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
            )
            
            logger.debug(f"Connected to Fabric SQL: {self.server}/{self.database}")
            return connection
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
    
    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get all records from APP_ADMINS table"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ID,
                    ADMIN_EMAIL,
                    ADMIN_TYPE,
                    APP_ID,
                    APP_NAME,
                    DATE_CREATED
                FROM APP_ADMINS
                ORDER BY ID ASC
            """
            
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching admins: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_admin_by_id(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """Get a single admin record by ID"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ID,
                    ADMIN_EMAIL,
                    ADMIN_TYPE,
                    APP_ID,
                    APP_NAME,
                    DATE_CREATED
                FROM APP_ADMINS
                WHERE ID = ?
            """
            
            cursor.execute(query, (admin_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching admin by ID: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_admin(self, admin_email: str, admin_type: str, app_id: int, app_name: str) -> int:
        """Create a new admin record"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO APP_ADMINS (ADMIN_EMAIL, ADMIN_TYPE, APP_ID, APP_NAME, DATE_CREATED)
                VALUES (?, ?, ?, ?, GETDATE())
            """
            
            cursor.execute(query, (admin_email, admin_type, app_id, app_name))
            conn.commit()
            
            # Get the inserted ID
            cursor.execute("SELECT @@IDENTITY AS ID")
            new_id = cursor.fetchone()[0]
            
            logger.info(f"Created admin record with ID: {new_id}")
            return new_id
            
        except Exception as e:
            logger.error(f"Error creating admin: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def update_admin(self, admin_id: int, admin_email: str, admin_type: str, app_id: int, app_name: str) -> bool:
        """Update an existing admin record"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE APP_ADMINS
                SET ADMIN_EMAIL = ?,
                    ADMIN_TYPE = ?,
                    APP_ID = ?,
                    APP_NAME = ?
                WHERE ID = ?
            """
            
            cursor.execute(query, (admin_email, admin_type, app_id, app_name, admin_id))
            conn.commit()
            
            rows_affected = cursor.rowcount
            logger.info(f"Updated admin record ID {admin_id}: {rows_affected} rows affected")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating admin: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def delete_admin(self, admin_id: int) -> bool:
        """Delete an admin record"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "DELETE FROM APP_ADMINS WHERE ID = ?"
            
            cursor.execute(query, (admin_id,))
            conn.commit()
            
            rows_affected = cursor.rowcount
            logger.info(f"Deleted admin record ID {admin_id}: {rows_affected} rows affected")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error deleting admin: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test the database connection"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
