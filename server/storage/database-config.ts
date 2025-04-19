import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import * as schema from '@shared/schema';
import { log } from '../vite';
import { AZURE_CONFIG } from '../azure';
import ws from 'ws';

// Set up Neon PostgreSQL WebSocket constructor
neonConfig.webSocketConstructor = ws;

// Database connection interface
interface DatabaseConnection {
  connect(): Promise<void>;
  getDb(): any; // Type will depend on implementation (Drizzle)
  close(): Promise<void>;
}

// PostgreSQL connection for development
class PostgresConnection implements DatabaseConnection {
  private pool: Pool;
  private dbInstance: any;

  constructor() {
    if (!process.env.DATABASE_URL) {
      throw new Error('DATABASE_URL environment variable must be set for PostgreSQL connection');
    }

    this.pool = new Pool({ connectionString: process.env.DATABASE_URL });
    this.dbInstance = drizzle({ client: this.pool, schema });
    log('PostgreSQL connection created using Neon serverless', 'database');
  }

  async connect(): Promise<void> {
    try {
      // Test the connection
      const client = await this.pool.connect();
      client.release();
      log('Successfully connected to PostgreSQL database', 'database');
    } catch (error) {
      log(`Error connecting to PostgreSQL: ${error}`, 'database');
      throw error;
    }
  }

  getDb() {
    return this.dbInstance;
  }

  async close(): Promise<void> {
    try {
      await this.pool.end();
      log('PostgreSQL connection closed', 'database');
    } catch (error) {
      log(`Error closing PostgreSQL connection: ${error}`, 'database');
    }
  }
}

// Azure SQL connection for production 
// This is a placeholder and will be implemented with the actual Azure SQL connection logic
class AzureSQLConnection implements DatabaseConnection {
  private dbInstance: any;

  constructor() {
    if (!AZURE_CONFIG.SQL_CONNECTION_STRING) {
      throw new Error('AZURE_SQL_CONNECTION_STRING environment variable must be set for Azure SQL connection');
    }
    
    log('Azure SQL connection created (placeholder)', 'database');
    // This will be implemented with the actual Azure SQL connection code
    // For example using mssql or another appropriate driver for Azure SQL
  }

  async connect(): Promise<void> {
    try {
      log('Would connect to Azure SQL Database here', 'database');
      // Actual implementation would connect to Azure SQL here
    } catch (error) {
      log(`Error connecting to Azure SQL: ${error}`, 'database');
      throw error;
    }
  }

  getDb() {
    return this.dbInstance;
  }

  async close(): Promise<void> {
    try {
      log('Would close Azure SQL connection here', 'database');
      // Actual implementation would close the Azure SQL connection here
    } catch (error) {
      log(`Error closing Azure SQL connection: ${error}`, 'database');
    }
  }
}

// Factory function to create the appropriate database connection
export function createDatabaseConnection(): DatabaseConnection {
  const isProduction = process.env.NODE_ENV === 'production';
  
  if (isProduction && AZURE_CONFIG.SQL_CONNECTION_STRING) {
    return new AzureSQLConnection();
  } else {
    return new PostgresConnection();
  }
}

// Export a singleton connection instance
const dbConnection = createDatabaseConnection();

// Initialize the database connection
export async function initializeDatabase() {
  await dbConnection.connect();
  return dbConnection.getDb();
}

// Export the db instance directly for use in the application
export const db = dbConnection.getDb();