import json
import os
from io import BytesIO

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from apps.claims.models import Claim
from apps.users.models import KYCDocument
from apps.users.services.mongo_storage import MongoAtlasStorageService


class Command(BaseCommand):
    help = "Migrate existing Azure Blob URLs into Mongo Atlas GridFS and replace stored URLs."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report what would change without writing anything.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        storage = MongoAtlasStorageService()

        self.stdout.write(self.style.WARNING('Starting document migration to Mongo Atlas...'))

        migrated_kyc, skipped_kyc = self._migrate_kyc_documents(storage, dry_run)
        migrated_claims, skipped_claims = self._migrate_claim_documents(storage, dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                f'Migration complete. KYC docs migrated: {migrated_kyc}; claim docs migrated: {migrated_claims}; '
                f'skipped invalid Azure URLs: {skipped_kyc + skipped_claims}.'
            )
        )

    def _migrate_kyc_documents(self, storage, dry_run):
        count = 0
        skipped = 0
        for record in KYCDocument.objects.exclude(document_url='').exclude(document_url__isnull=True):
            if self._is_mongo_reference(record.document_url):
                continue

            try:
                content = self._download_bytes(record.document_url)
                filename = record.document_url.rstrip('/').split('/')[-1] or f"kyc-{record.id}.bin"
                uploaded = SimpleUploadedFile(
                    name=filename,
                    content=content,
                    content_type='application/octet-stream',
                )
                new_url = storage.upload_kyc_document(
                    file_obj=uploaded,
                    document_type='migrated-kyc-document',
                    user_id=record.user_id,
                    filename=filename,
                )
                if not dry_run:
                    record.document_url = new_url
                    record.save(update_fields=['document_url'])
                count += 1
                self.stdout.write(f'KYC migrated: {record.id} -> {new_url}')
            except requests.HTTPError as exc:
                if getattr(exc.response, 'status_code', None) == 404:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f'Skipping missing Azure KYC document {record.id}: {record.document_url}'))
                    continue
                self.stdout.write(self.style.ERROR(f'Failed KYC migration for {record.id}: {exc}'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'Failed KYC migration for {record.id}: {exc}'))
        return count, skipped

    def _migrate_claim_documents(self, storage, dry_run):
        count = 0
        skipped = 0
        for claim in Claim.objects.exclude(documents=[]):
            docs = claim.documents or []
            if not isinstance(docs, list):
                continue

            changed = False
            for item in docs:
                url = item.get('url') if isinstance(item, dict) else None
                if not url:
                    continue

                # Handle Mongo references (skip)
                if self._is_mongo_reference(url):
                    continue

                # Handle Azure Blob URLs
                if url.startswith('https://') and 'blob.core.windows.net' in url:
                    try:
                        content = self._download_bytes(url)
                        filename = url.rstrip('/').split('/')[-1] or f"claim-{claim.claim_id}.bin"
                        uploaded = SimpleUploadedFile(
                            name=filename,
                            content=content,
                            content_type='application/octet-stream',
                        )
                        new_url = storage.upload_kyc_document(
                            file_obj=uploaded,
                            document_type='claim-supporting-document',
                            user_id=claim.user_id_id,
                            filename=filename,
                        )
                        if not dry_run:
                            item['url'] = new_url
                        count += 1
                        changed = True
                        self.stdout.write(f'Claim document migrated: {claim.claim_id} -> {new_url}')
                    except requests.HTTPError as exc:
                        if getattr(exc.response, 'status_code', None) == 404:
                            # Clean up missing Azure URL by removing it from the list
                            if not dry_run:
                                docs.remove(item)
                                changed = True
                            skipped += 1
                            self.stdout.write(self.style.WARNING(f'Removed missing Azure claim document {claim.claim_id}: {url}'))
                            continue
                        self.stdout.write(self.style.ERROR(f'Failed claim migration for {claim.claim_id}: {exc}'))
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f'Failed claim migration for {claim.claim_id}: {exc}'))

                # Handle local /media/ files
                elif url.startswith('/media/'):
                    try:
                        # Read from local filesystem
                        local_path = os.path.join(os.getcwd(), url.lstrip('/'))
                        if os.path.exists(local_path):
                            with open(local_path, 'rb') as f:
                                content = f.read()
                            filename = os.path.basename(local_path)
                            uploaded = SimpleUploadedFile(
                                name=filename,
                                content=content,
                                content_type='application/octet-stream',
                            )
                            new_url = storage.upload_kyc_document(
                                file_obj=uploaded,
                                document_type='claim-supporting-document',
                                user_id=claim.user_id_id,
                                filename=filename,
                            )
                            if not dry_run:
                                item['url'] = new_url
                            count += 1
                            changed = True
                            self.stdout.write(f'Claim document migrated from local: {claim.claim_id} -> {new_url}')
                        else:
                            skipped += 1
                            self.stdout.write(self.style.WARNING(f'Skipping missing local file: {url}'))
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f'Failed local file migration for {claim.claim_id}: {exc}'))

            if changed and not dry_run:
                claim.documents = docs
                claim.save(update_fields=['documents'])
        return count, skipped

    def _download_bytes(self, url):
        response = requests.get(url, timeout=60, allow_redirects=True)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            raise
        return response.content

    def _is_mongo_reference(self, url):
        prefix = storage_prefix = __import__('decouple').config(
            'MONGO_FILE_URL_PREFIX', default='https://mongo-atlas.local/file'
        ).rstrip('/')
        return bool(url) and str(url).startswith(f'{prefix}/')
