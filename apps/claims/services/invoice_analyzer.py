"""
Invoice Document Analysis Service using Azure AI Document Intelligence.

Processes invoice documents with custom models defined by the user.
"""

from typing import Dict, Optional, List
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from decouple import config

logger = logging.getLogger(__name__)


class InvoiceAnalyzerService:
    """Service for analyzing invoice documents using Azure Document Intelligence with custom models."""
    
    def __init__(self, model_name: str = "prebuilt-invoice"):
        """Initialize the Document Intelligence client with custom model support."""
        self.endpoint = config('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        self.key = config('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        self.model_name = model_name  # Custom model name
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY "
                "environment variables must be set"
            )
        
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def analyze_invoice(self, document_url: str, custom_fields: Optional[List[str]] = None) -> Dict:
        """
        Analyze an invoice document using custom model and extract custom fields.
        
        Args:
            document_url: Azure Blob Storage URL to the invoice document
            custom_fields: List of custom field names to extract (required for custom models)
            
        Returns:
            Dictionary containing extracted invoice information with confidence scores
        """
        try:
            logger.info(f"Analyzing invoice document with custom model '{self.model_name}': {document_url}")
            
            # Use custom model for analysis
            poller = self.client.begin_analyze_document(
                self.model_name,
                AnalyzeDocumentRequest(url_source=document_url)
            )
            invoice_result = poller.result()
            
            if not invoice_result.documents:
                logger.warning(f"No documents found in analysis result for: {document_url}")
                return {
                    'success': False,
                    'error': 'No document detected',
                    'raw_result': None
                }
            
            # Extract data from the first document
            invoice_document = invoice_result.documents[0]
            extracted_data = self._extract_custom_fields(invoice_document, custom_fields)
            
            logger.info(f"Successfully extracted invoice data from: {document_url}")
            return {
                'success': True,
                'error': None,
                'data': extracted_data,
                'raw_result': invoice_result
            }
        
        except Exception as e:
            logger.error(f"Error analyzing invoice document {document_url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'raw_result': None
            }
    
    def _extract_custom_fields(self, invoice_document, custom_fields: Optional[List[str]] = None) -> Dict:
        """
        Extract custom fields from an analyzed invoice document using custom model.
        
        Args:
            invoice_document: Document object from Azure API response
            custom_fields: List of custom field names to extract
            
        Returns:
            Dictionary of extracted custom fields with values and confidence scores
        """
        extracted = {}
        
        # Extract all fields from the custom model response
        if hasattr(invoice_document, 'fields'):
            for field_name, field in invoice_document.fields.items():
                value = self._get_field_value(field)
                extracted[field_name] = {
                    'value': value,
                    'confidence': field.confidence if hasattr(field, 'confidence') else None
                }
        
        # If custom_fields are specified, filter to only those fields
        if custom_fields:
            filtered_extracted = {}
            for field_name in custom_fields:
                if field_name in extracted:
                    filtered_extracted[field_name] = extracted[field_name]
                else:
                    # Add placeholder for requested but not found fields
                    filtered_extracted[field_name] = {
                        'value': None,
                        'confidence': None,
                        'note': 'Field not found in custom model response'
                    }
            extracted = filtered_extracted
        
        # Calculate overall confidence score
        confidence_scores = []
        for field_data in extracted.values():
            if isinstance(field_data, dict) and 'confidence' in field_data:
                conf = field_data['confidence']
                if conf is not None:
                    confidence_scores.append(conf)
        
        if confidence_scores:
            extracted['confidence_score'] = sum(confidence_scores) / len(confidence_scores)
        
        return extracted
    
    def _get_field_value(self, field) -> Optional[str]:
        """
        Extract value from a field object.
        
        Args:
            field: Field object from Azure API response
            
        Returns:
            Extracted value or None
        """
        if not field:
            return None
        
        if hasattr(field, 'value_string'):
            return field.value_string
        elif hasattr(field, 'value_date'):
            return field.value_date
        elif hasattr(field, 'value_address'):
            return field.value_address
        elif hasattr(field, 'value_currency'):
            return field.value_currency
        elif hasattr(field, 'value_number'):
            return field.value_number
        elif hasattr(field, 'content'):
            return field.content
        else:
            return str(field.value) if hasattr(field, 'value') else None
    
    def format_extraction_summary(self, extracted_data: Dict) -> str:
        """
        Format extracted data into a readable summary string.
        
        Args:
            extracted_data: Extracted field data
            
        Returns:
            Formatted string summary
        """
        summary_lines = []
        
        # Add custom fields to summary
        for field_name, field_data in extracted_data.items():
            if field_name == 'confidence_score':
                continue
                
            value = field_data.get('value')
            confidence = field_data.get('confidence')
            
            if value is not None:
                field_display = field_name.replace('_', ' ').title()
                confidence_text = f" (confidence: {confidence:.2f})" if confidence is not None else ""
                summary_lines.append(f"{field_display}: {value}{confidence_text}")
        
        # Add confidence score
        if 'confidence_score' in extracted_data:
            summary_lines.append(f"\nOverall Confidence: {extracted_data['confidence_score']:.2f}")
        
        return '\n'.join(summary_lines)