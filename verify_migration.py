#!/usr/bin/env python
"""
Verify that the MongoDB migration cleaned up Azure references.
"""
import os
import sys

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from apps.claims.models import Claim
from apps.users.models import KYCDocument

def verify_migration():
    """Verify that Azure references have been cleaned up."""
    print("Verifying MongoDB migration cleanup...")
    
    # Check KYC documents
    kyc_docs = KYCDocument.objects.all()
    print(f'\nKYCDocument records: {kyc_docs.count()}')
    
    azure_kyc_count = 0
    mongo_kyc_count = 0
    for doc in kyc_docs:
        if doc.document_url:
            if 'bima.blob.core.windows.net' in doc.document_url:
                azure_kyc_count += 1
                print(f'  ❌ Azure URL: {doc.document_url}')
            elif 'mongo-atlas.local/file' in doc.document_url:
                mongo_kyc_count += 1
                print(f'  ✅ Mongo URL: {doc.document_url}')
            else:
                print(f'  ⚠️  Other URL: {doc.document_url}')
    
    # Check claim documents  
    claims = Claim.objects.all()
    print(f'\nClaim records: {claims.count()}')
    
    azure_claim_count = 0
    mongo_claim_count = 0
    local_file_count = 0
    
    for claim in claims:
        docs = claim.documents or []
        print(f'  Claim ID: {claim.claim_id}')
        
        for item in docs:
            if isinstance(item, dict) and 'url' in item:
                url = item['url']
                if 'bima.blob.core.windows.net' in url:
                    azure_claim_count += 1
                    print(f'    ❌ Azure URL: {url}')
                elif 'mongo-atlas.local/file' in url:
                    mongo_claim_count += 1
                    print(f'    ✅ Mongo URL: {url}')
                elif url.startswith('/media/'):
                    local_file_count += 1
                    print(f'    📁 Local file: {url}')
                else:
                    print(f'    ⚠️  Other URL: {url}')
    
    # Summary
    print(f'\n📊 Migration Summary:')
    print(f'  KYC Documents:')
    print(f'    - Azure URLs remaining: {azure_kyc_count}')
    print(f'    - Mongo URLs: {mongo_kyc_count}')
    print(f'  Claim Documents:')
    print(f'    - Azure URLs remaining: {azure_claim_count}')
    print(f'    - Mongo URLs: {mongo_claim_count}')
    print(f'    - Local files: {local_file_count}')
    
    # Success criteria
    success = (azure_kyc_count == 0 and azure_claim_count == 0)
    
    if success:
        print(f'\n🎉 Migration verification PASSED!')
        print(f'   All Azure references have been cleaned up.')
    else:
        print(f'\n⚠️  Migration verification FAILED!')
        print(f'   {azure_kyc_count + azure_claim_count} Azure references still remain.')
    
    return success

if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)