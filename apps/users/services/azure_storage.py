# For beginners: This file (apps/users/services/azure_storage.py) contains part of the application logic.
# For beginners: Read this file from top to bottom to see what data it handles
# and which functions/classes other files can call.

"""
Azure Blob Storage service for uploading KYC documents.
"""

import logging
from typing import Optional
from uuid import uuid4
from django.conf import settings
from azure.storage.blob import BlobServiceClient
from decouple import config

logger = logging.getLogger(__name__)


# For beginners: This class 'AzureBlobStorageService' groups related data and behavior
# so other parts of the app can use one structured object.
# For beginners: This class 'AzureBlobStorageService' groups related data and behavior
# so other parts of the app can use one structured object.
class AzureBlobStorageService:
    """Service for uploading files to Azure Blob Storage."""
    
    # For beginners: This function '__init__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '__init__' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def __init__(self):
        """Initialize Azure Blob Storage client."""
        self.account_name = config('AZURE_ACCOUNT_NAME', default='')
        self.account_key = config('AZURE_ACCOUNT_KEY', default='')
        self.container_name = config('AZURE_CONTAINER', default='bima-afya-documents')
        
        if not self.account_name or not self.account_key:
            raise ValueError(
                "AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY environment variables must be set"
            )
        
        # Initialize Azure Blob client
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            credential=self.account_key
        )
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
    
    # For beginners: This function 'upload_kyc_document' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'upload_kyc_document' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def upload_kyc_document(
        self,
        file_obj,
        document_type: str,
        user_id,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload a KYC document to Azure Blob Storage.
        
        Args:
            file_obj: File object to upload (from request.FILES)
            document_type: Type of document (national_id, passport, drivers_license)
            user_id: ID of the user uploading the document
            filename: Optional filename (defaults to UUID)
            
        Returns:
            Full Azure Blob URL of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Generate blob name
            if not filename:
                # Generate unique filename
                file_ext = self._get_file_extension(file_obj.name)
                filename = f"kyc-{document_type}-{uuid4()}.{file_ext}"
            
            # Create blob path structure: kyc-documents/user_id/document_type/filename
            blob_name = f"kyc-documents/{user_id}/{document_type}/{filename}"
            
            logger.info(f"Uploading KYC document to Azure: {blob_name}")
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload file
            blob_client.upload_blob(file_obj, overwrite=True)
            
            # Build and return URL
            blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            
            logger.info(f"Successfully uploaded KYC document: {blob_url}")
            return blob_url
        
        except Exception as e:
            logger.error(f"Error uploading KYC document for user {user_id}: {str(e)}")
            raise
    
    # For beginners: This function 'delete_kyc_document' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function 'delete_kyc_document' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def delete_kyc_document(self, document_url: str) -> bool:
        """
        Delete a KYC document from Azure Blob Storage.
        
        Args:
            document_url: Full Azure Blob URL of the document
            
        Returns:
            True if deletion was successful
        """
        try:
            # Extract blob name from URL
            blob_name = self._extract_blob_name(document_url)
            
            logger.info(f"Deleting KYC document from Azure: {blob_name}")
            
            # Get blob client and delete
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            
            logger.info(f"Successfully deleted KYC document: {blob_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting KYC document {document_url}: {str(e)}")
            return False
    
    # For beginners: This function '_get_file_extension' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '_get_file_extension' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return filename.split('.')[-1].lower() if '.' in filename else 'bin'
    
    # For beginners: This function '_extract_blob_name' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    # For beginners: This function '_extract_blob_name' performs one reusable task.
    # Other parts of the app call it to avoid duplicating logic.
    def _extract_blob_name(self, blob_url: str) -> str:
        """Extract blob name from full Azure Blob URL."""
        # URL format: https://{account}.blob.core.windows.net/{container}/{blob_name}
        parts = blob_url.split(f"{self.container_name}/", 1)
        if len(parts) > 1:
            return parts[1]
        return blob_url
