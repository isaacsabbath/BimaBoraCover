#!/usr/bin/env python
"""
Quick test to verify Mongo GridFS upload is working.
"""
import os
import sys
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from decouple import config

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from apps.users.services.mongo_storage import MongoAtlasStorageService

def test_mongo_upload():
    """Test uploading a file to Mongo GridFS."""
    print("Testing Mongo GridFS upload...")
    
    try:
        # Initialize the storage service
        storage = MongoAtlasStorageService()
        print(f"✓ Mongo storage service initialized")
        print(f"  - Database: {config('MONGO_ATLAS_DB', default='bimabora')}")
        print(f"  - Bucket: {config('MONGO_ATLAS_BUCKET', default='documents')}")
        
        # Create a test file
        test_content = b"Test file content for Mongo GridFS upload"
        test_file = SimpleUploadedFile(
            name="test_document.txt",
            content=test_content,
            content_type="text/plain"
        )
        
        # Upload the file
        document_url = storage.upload_kyc_document(
            file_obj=test_file,
            document_type="test-document",
            user_id=12345,  # Test user ID
            filename="test_document.txt"
        )
        
        print(f"✓ File uploaded successfully")
        print(f"  - URL: {document_url}")
        
        # Verify the URL format
        prefix = config('MONGO_FILE_URL_PREFIX', default='https://mongo-atlas.local/file').rstrip('/')
        if document_url.startswith(f"{prefix}/"):
            print(f"✓ URL format is correct (Mongo reference)")
        else:
            print(f"✗ URL format is incorrect: {document_url}")
            return False
        
        # Try to retrieve the file bytes
        try:
            file_bytes = storage.get_file_bytes(document_url)
            if file_bytes == test_content:
                print(f"✓ File content matches")
            else:
                print(f"✗ File content mismatch")
                return False
        except Exception as e:
            print(f"✗ Failed to retrieve file: {e}")
            return False
        
        # Test deletion
        try:
            delete_result = storage.delete_kyc_document(document_url)
            if delete_result:
                print(f"✓ File deletion successful")
            else:
                print(f"✗ File deletion failed")
                return False
        except Exception as e:
            print(f"✗ Failed to delete file: {e}")
            return False
        
        print("\n🎉 All Mongo GridFS tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_mongo_upload()
    sys.exit(0 if success else 1)