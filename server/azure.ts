import { log } from './vite';

// Azure Configuration
export const AZURE_CONFIG = {
  // Database configuration
  SQL_CONNECTION_STRING: process.env.AZURE_SQL_CONNECTION_STRING || '',
  
  // Azure Blob Storage configuration
  STORAGE_ACCOUNT_NAME: process.env.AZURE_STORAGE_ACCOUNT_NAME || '',
  STORAGE_ACCOUNT_KEY: process.env.AZURE_STORAGE_ACCOUNT_KEY || '',
  STORAGE_CONNECTION_STRING: process.env.AZURE_STORAGE_CONNECTION_STRING || '',
  
  // Container names for different types of blob storage
  CLAIM_DOCUMENTS_CONTAINER: 'claim-documents',
  PROFILE_IMAGES_CONTAINER: 'profile-images',
  
  // Azure Key Vault (for production secrets)
  KEY_VAULT_NAME: process.env.AZURE_KEY_VAULT_NAME || '',
};

// Validate required Azure configuration in production
export function validateAzureConfig() {
  const isProduction = process.env.NODE_ENV === 'production';
  
  if (isProduction) {
    if (!AZURE_CONFIG.SQL_CONNECTION_STRING) {
      throw new Error('AZURE_SQL_CONNECTION_STRING environment variable is required in production');
    }
    
    if (!AZURE_CONFIG.STORAGE_CONNECTION_STRING) {
      throw new Error('AZURE_STORAGE_CONNECTION_STRING environment variable is required in production');
    }
    
    log('Azure configuration validated successfully', 'azure');
  } else {
    log('Running in development mode - Azure configuration is optional', 'azure');
  }
}

// Initialize Azure services based on environment
export function initializeAzureServices() {
  const isProduction = process.env.NODE_ENV === 'production';
  
  if (isProduction) {
    log('Initializing Azure services for production environment', 'azure');
    // Initialize connection to Azure SQL, Blob Storage, etc.
    // This would be implemented when ready for Azure deployment
  }
}