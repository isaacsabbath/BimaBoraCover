"""
MongoDB Atlas GridFS storage service for KYC and claim documents.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from uuid import uuid4

from decouple import config
from gridfs import GridFSBucket
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class MongoAtlasStorageService:
    """Service for storing and retrieving documents from MongoDB Atlas GridFS."""

    def __init__(self):
        self.mongo_uri = config('MONGO_ATLAS_URI', default='')
        self.database_name = config('MONGO_ATLAS_DB', default='bimabora')
        self.bucket_name = config('MONGO_ATLAS_BUCKET', default='documents')
        self.url_prefix = config(
            'MONGO_FILE_URL_PREFIX',
            default='https://mongo-atlas.local/file'
        ).rstrip('/')

        if not self.mongo_uri:
            raise ValueError('MONGO_ATLAS_URI environment variable must be set')

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.database_name]
        self.bucket = GridFSBucket(self.db, bucket_name=self.bucket_name)

    def upload_kyc_document(
        self,
        file_obj,
        document_type: str,
        user_id,
        filename: Optional[str] = None,
    ) -> str:
        """Upload a file to GridFS and return an app-managed URL reference."""
        if not filename:
            file_ext = self._get_file_extension(getattr(file_obj, 'name', ''))
            filename = f"kyc-{document_type}-{uuid4()}.{file_ext}"

        key = f"kyc-documents/{user_id}/{document_type}/{filename}"

        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        raw_data = file_obj.read()

        content_type = getattr(file_obj, 'content_type', None)
        file_id = self.bucket.upload_from_stream(
            filename=key,
            source=BytesIO(raw_data),
            metadata={
                'key': key,
                'content_type': content_type,
                'original_filename': getattr(file_obj, 'name', filename),
                'document_type': document_type,
                'user_id': str(user_id),
            },
        )

        url = f"{self.url_prefix}/{quote(str(file_id))}"
        logger.info('Uploaded document to Mongo Atlas GridFS: %s', key)
        return url

    def get_file_bytes(self, document_url: str) -> bytes:
        """Read file bytes from GridFS using URL reference."""
        file_id = self._extract_file_id(document_url)
        stream = BytesIO()
        self.bucket.download_to_stream(file_id, stream)
        return stream.getvalue()

    def delete_kyc_document(self, document_url: str) -> bool:
        """Delete a file from GridFS by URL reference."""
        try:
            file_id = self._extract_file_id(document_url)
            self.bucket.delete(file_id)
            return True
        except Exception as exc:
            logger.error('Failed deleting Mongo Atlas file %s: %s', document_url, exc)
            return False

    def _extract_file_id(self, document_url: str):
        from bson import ObjectId

        if not document_url.startswith(f"{self.url_prefix}/"):
            raise ValueError('Invalid Mongo Atlas file URL prefix')

        file_id = document_url.rsplit('/', 1)[-1]
        return ObjectId(file_id)

    def _get_file_extension(self, filename: str) -> str:
        suffix = Path(filename).suffix
        return suffix.replace('.', '').lower() if suffix else 'bin'
