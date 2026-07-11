"""
KYC Document Analysis Service using Azure AI Document Intelligence.

Processes ID documents (national IDs, passports) to extract and verify user information.
"""

from typing import Dict, Optional
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from decouple import config

logger = logging.getLogger(__name__)


class KYCAnalyzerService:
    """Service for analyzing KYC documents using Azure Document Intelligence."""
    
    def __init__(self):
        """Initialize the Document Intelligence client."""
        self.endpoint = config('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        self.key = config('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY "
                "environment variables must be set"
            )
        
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def analyze_id_document(self, document_url: str) -> Dict:
        """
        Analyze an ID document (national ID, passport, etc.) and extract information.
        
        Args:
            document_url: Azure Blob Storage URL to the ID document
            
        Returns:
            Dictionary containing extracted ID information with confidence scores
        """
        try:
            logger.info(f"Analyzing ID document: {document_url}")
            
            poller = self.client.begin_analyze_document(
                "prebuilt-idDocument",
                AnalyzeDocumentRequest(url_source=document_url)
            )
            id_documents = poller.result()
            
            if not id_documents.documents:
                logger.warning(f"No documents found in analysis result for: {document_url}")
                return {
                    'success': False,
                    'error': 'No document detected',
                    'raw_result': None
                }
            
            # Extract data from the first document
            id_document = id_documents.documents[0]
            extracted_data = self._extract_id_fields(id_document)
            
            logger.info(f"Successfully extracted ID data from: {document_url}")
            return {
                'success': True,
                'error': None,
                'data': extracted_data,
                'raw_result': id_documents
            }
        
        except Exception as e:
            logger.error(f"Error analyzing ID document {document_url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'raw_result': None
            }
    
    def _extract_id_fields(self, id_document) -> Dict:
        """
        Extract relevant fields from an analyzed ID document.
        
        Args:
            id_document: Document object from Azure API response
            
        Returns:
            Dictionary of extracted fields with values and confidence scores
        """
        extracted = {}
        
        # Map of field names to extract
        field_mapping = {
            'first_name': 'FirstName',
            'last_name': 'LastName',
            'document_number': 'DocumentNumber',
            'date_of_birth': 'DateOfBirth',
            'date_of_expiration': 'DateOfExpiration',
            'sex': 'Sex',
            'address': 'Address',
            'country_region': 'CountryRegion',
            'region': 'Region',
            'mrz': 'MachineReadableZone',
            'nationality': 'Nationality',
        }
        
        for field_key, field_name in field_mapping.items():
            field = id_document.fields.get(field_name)
            
            if field:
                value = None
                if hasattr(field, 'value_string'):
                    value = field.value_string
                elif hasattr(field, 'value_date'):
                    value = field.value_date
                elif hasattr(field, 'value_address'):
                    value = field.value_address
                elif hasattr(field, 'value_country_region'):
                    value = field.value_country_region
                elif hasattr(field, 'content'):
                    value = field.content
                else:
                    value = str(field.value) if hasattr(field, 'value') else None
                
                extracted[field_key] = {
                    'value': value,
                    'confidence': field.confidence if hasattr(field, 'confidence') else None
                }
        
        return extracted
    
    def verify_kyc_data(self, extracted_data: Dict, user_data: Dict) -> Dict:
        """
        Verify extracted ID data against user registration data.
        
        Args:
            extracted_data: Data extracted from ID document
            user_data: User's registered data (full_name, national_id, etc.)
            
        Returns:
            Dictionary with verification results and flags
        """
        verification_result = {
            'verified': True,
            'flags': [],
            'mismatches': [],
            'confidence_score': 1.0
        }
        
        # Check first name
        first_name = extracted_data.get('first_name', {}).get('value', '').lower()
        last_name = extracted_data.get('last_name', {}).get('value', '').lower()
        
        if first_name or last_name:
            extracted_full_name = f"{first_name} {last_name}".strip().lower()
            registered_full_name = user_data.get('full_name', '').lower()
            
            if extracted_full_name != registered_full_name:
                verification_result['verified'] = False
                verification_result['mismatches'].append({
                    'field': 'full_name',
                    'extracted': extracted_full_name,
                    'registered': registered_full_name
                })
        
        # Check document number (national ID)
        doc_number = extracted_data.get('document_number', {}).get('value', '')
        if doc_number:
            if doc_number != user_data.get('national_id', ''):
                verification_result['verified'] = False
                verification_result['mismatches'].append({
                    'field': 'national_id',
                    'extracted': doc_number,
                    'registered': user_data.get('national_id', '')
                })
        
        # Check expiration
        doe = extracted_data.get('date_of_expiration', {}).get('value')
        if doe:
            from datetime import datetime
            try:
                exp_date = datetime.fromisoformat(str(doe))
                if exp_date < datetime.now():
                    verification_result['flags'].append('ID_EXPIRED')
                    verification_result['verified'] = False
            except (ValueError, TypeError):
                logger.warning(f"Could not parse expiration date: {doe}")
        
        # Calculate average confidence score
        confidence_scores = []
        for field_key, field_data in extracted_data.items():
            if isinstance(field_data, dict) and 'confidence' in field_data:
                conf = field_data['confidence']
                if conf is not None:
                    confidence_scores.append(conf)
        
        if confidence_scores:
            verification_result['confidence_score'] = sum(confidence_scores) / len(confidence_scores)
            
            # Flag low confidence
            if verification_result['confidence_score'] < 0.8:
                verification_result['flags'].append('LOW_CONFIDENCE')
        
        return verification_result
    
    def format_extraction_summary(self, extracted_data: Dict) -> str:
        """
        Format extracted data into a readable summary string.
        
        Args:
            extracted_data: Extracted field data
            
        Returns:
            Formatted string summary
        """
        summary_lines = []
        
        first_name = extracted_data.get('first_name', {}).get('value')
        last_name = extracted_data.get('last_name', {}).get('value')
        if first_name or last_name:
            summary_lines.append(f"Name: {first_name or ''} {last_name or ''}".strip())
        
        doc_number = extracted_data.get('document_number', {}).get('value')
        if doc_number:
            summary_lines.append(f"Document Number: {doc_number}")
        
        dob = extracted_data.get('date_of_birth', {}).get('value')
        if dob:
            summary_lines.append(f"Date of Birth: {dob}")
        
        doe = extracted_data.get('date_of_expiration', {}).get('value')
        if doe:
            summary_lines.append(f"Expiration Date: {doe}")
        
        sex = extracted_data.get('sex', {}).get('value')
        if sex:
            summary_lines.append(f"Sex: {sex}")
        
        address = extracted_data.get('address', {}).get('value')
        if address:
            summary_lines.append(f"Address: {address}")
        
        country = extracted_data.get('country_region', {}).get('value')
        if country:
            summary_lines.append(f"Country: {country}")
        
        region = extracted_data.get('region', {}).get('value')
        if region:
            summary_lines.append(f"Region: {region}")
        
        return '\n'.join(summary_lines)
