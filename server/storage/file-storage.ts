import { log } from '../vite';
import { AZURE_CONFIG } from '../azure';
import fs from 'fs';
import path from 'path';

// Interface for file storage operations
export interface IFileStorage {
  saveFile(fileBuffer: Buffer, fileName: string, containerName: string): Promise<string>;
  getFileUrl(fileName: string, containerName: string): Promise<string>;
  deleteFile(fileName: string, containerName: string): Promise<boolean>;
}

// Local file storage implementation for development
export class LocalFileStorage implements IFileStorage {
  private baseDir: string;

  constructor() {
    // Create a local directory to store files during development
    this.baseDir = path.join(process.cwd(), 'local-storage');
    this.ensureDirectoryExists(this.baseDir);
    log('Using local file storage at: ' + this.baseDir, 'storage');
  }

  private ensureDirectoryExists(directory: string): void {
    if (!fs.existsSync(directory)) {
      fs.mkdirSync(directory, { recursive: true });
    }
  }

  private ensureContainerExists(containerName: string): void {
    const containerPath = path.join(this.baseDir, containerName);
    this.ensureDirectoryExists(containerPath);
  }

  async saveFile(fileBuffer: Buffer, fileName: string, containerName: string): Promise<string> {
    try {
      this.ensureContainerExists(containerName);
      const filePath = path.join(this.baseDir, containerName, fileName);
      fs.writeFileSync(filePath, fileBuffer);
      log(`File saved locally: ${filePath}`, 'storage');
      return fileName;
    } catch (error) {
      log(`Error saving file locally: ${error}`, 'storage');
      throw new Error('Failed to save file');
    }
  }

  async getFileUrl(fileName: string, containerName: string): Promise<string> {
    // In local development, we'll just return a path to the local file
    return `/api/files/${containerName}/${fileName}`;
  }

  async deleteFile(fileName: string, containerName: string): Promise<boolean> {
    try {
      const filePath = path.join(this.baseDir, containerName, fileName);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        log(`File deleted locally: ${filePath}`, 'storage');
        return true;
      }
      return false;
    } catch (error) {
      log(`Error deleting file locally: ${error}`, 'storage');
      return false;
    }
  }
}

// Azure Blob Storage implementation for production
// This will be implemented when ready to deploy to Azure
export class AzureBlobStorage implements IFileStorage {
  constructor() {
    if (!AZURE_CONFIG.STORAGE_CONNECTION_STRING) {
      throw new Error('Azure Storage connection string is required');
    }
    log('Using Azure Blob Storage', 'storage');
  }

  async saveFile(fileBuffer: Buffer, fileName: string, containerName: string): Promise<string> {
    // This will be implemented with the Azure Storage SDK
    // For example:
    // const blobServiceClient = BlobServiceClient.fromConnectionString(
    //   AZURE_CONFIG.STORAGE_CONNECTION_STRING
    // );
    // const containerClient = blobServiceClient.getContainerClient(containerName);
    // const blockBlobClient = containerClient.getBlockBlobClient(fileName);
    // await blockBlobClient.upload(fileBuffer, fileBuffer.length);
    // return blockBlobClient.url;
    
    log('Azure Blob Storage: saveFile not implemented yet', 'storage');
    throw new Error('Azure Blob Storage implementation not complete');
  }

  async getFileUrl(fileName: string, containerName: string): Promise<string> {
    // This will create a URL to access the file from Azure Blob Storage
    // For example:
    // const blobServiceClient = BlobServiceClient.fromConnectionString(
    //   AZURE_CONFIG.STORAGE_CONNECTION_STRING
    // );
    // const containerClient = blobServiceClient.getContainerClient(containerName);
    // const blockBlobClient = containerClient.getBlockBlobClient(fileName);
    // return blockBlobClient.url;
    
    log('Azure Blob Storage: getFileUrl not implemented yet', 'storage');
    throw new Error('Azure Blob Storage implementation not complete');
  }

  async deleteFile(fileName: string, containerName: string): Promise<boolean> {
    // This will delete a file from Azure Blob Storage
    // For example:
    // const blobServiceClient = BlobServiceClient.fromConnectionString(
    //   AZURE_CONFIG.STORAGE_CONNECTION_STRING
    // );
    // const containerClient = blobServiceClient.getContainerClient(containerName);
    // const blockBlobClient = containerClient.getBlockBlobClient(fileName);
    // const response = await blockBlobClient.delete();
    // return response.succeeded;
    
    log('Azure Blob Storage: deleteFile not implemented yet', 'storage');
    throw new Error('Azure Blob Storage implementation not complete');
  }
}

// Factory function to create the appropriate file storage implementation
export function createFileStorage(): IFileStorage {
  const isProduction = process.env.NODE_ENV === 'production';
  
  if (isProduction && AZURE_CONFIG.STORAGE_CONNECTION_STRING) {
    return new AzureBlobStorage();
  } else {
    return new LocalFileStorage();
  }
}

// Export a singleton instance
export const fileStorage = createFileStorage();