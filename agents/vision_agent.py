import os
import io
import logging
from typing import Optional, Literal
import datetime
from pydantic import BaseModel, Field
from PIL import Image
import fitz
from google import genai
from google.genai import types
from schemas.models import ExtractedInvoiceItem

logger = logging.getLogger("TaxAssistantApp.VisionAgent")

class ExtractedInvoiceFields(BaseModel):
    date: datetime.date = Field(..., description="Date of the transaction (YYYY-MM-DD).")
    vendor: str = Field(..., description="Vendor/Merchant name.")
    amount_total_inr: float = Field(..., ge=0.0, description="Total invoice amount in INR including taxes.")
    gst_paid_inr: float = Field(0.0, ge=0.0, description="GST component paid (CGST+SGST or IGST) if present.")
    gst_rate_percent: Literal[0, 5, 12, 18, 28] = Field(0, description="GST percentage rate.")
    description: str = Field(..., description="Description of the goods or services purchased.")
    category: str = Field(..., description="Expense category classification (e.g. software SaaS, office supplies, rent, personal).")
    usage_type: Literal["Pure Business", "Pure Personal", "Mixed", "Unresolved"] = Field("Unresolved", description="Indicates usage scope based on nature of goods.")
    payment_mode: Literal["Digital (UPI/Card/NetBanking)", "Cash", "Cheque"] = Field(..., description="Mode of transaction payment.")

def analyze_document(file_name: str, file_bytes: bytes, mime_type: str) -> ExtractedInvoiceItem:
    """
    Ingests file bytes, converts PDFs to images if necessary, and uses gemini-2.5-flash vision
    capabilities to extract invoice details matching the ExtractedInvoiceItem schema.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable is not set. Initializing Client without explicit key.")

    client = genai.Client(api_key=api_key)

    # 1. Process document into PIL Image
    try:
        if mime_type.lower() == "application/pdf" or file_name.lower().endswith(".pdf"):
            logger.info("PDF document detected. Converting first page to PIL Image using PyMuPDF...")
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                if len(doc) == 0:
                    raise ValueError("PDF document has no pages.")
                page = doc.load_page(0) # Get first page
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
            except Exception as pdf_err:
                logger.exception("PyMuPDF PDF conversion failed: %s", str(pdf_err))
                raise ValueError(f"Could not render PDF using PyMuPDF: {str(pdf_err)}") from pdf_err
        else:
            logger.info("Image document detected. Loading PIL Image...")
            img = Image.open(io.BytesIO(file_bytes))
    except Exception as img_err:
        logger.exception("Failed to load file %s as image: %s", file_name, str(img_err))
        raise ValueError(f"Could not read uploaded file as a valid image or PDF: {str(img_err)}") from img_err

    # 2. Load system instruction
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "vision_agent.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    except Exception as e:
        logger.exception("Failed to load vision agent system instruction: %s", str(e))
        system_instruction = "You are the Vision Agent. Extract invoice/receipt details into structured fields."

    # 3. Call Gemini Multimodal API
    try:
        logger.info("Calling Gemini Vision model for document: %s", file_name)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Extract the receipt/invoice details from this document.",
                img
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ExtractedInvoiceFields,
                temperature=0.1
            )
        )

        # Parse output
        fields = None
        if response.parsed:
            fields = response.parsed
        else:
            logger.warning("response.parsed is None. Fallback to manual JSON parse.")
            import json
            data = json.loads(response.text)
            fields = ExtractedInvoiceFields.model_validate(data)

        # 4. Map to ExtractedInvoiceItem including document_id
        item = ExtractedInvoiceItem(
            document_id=file_name,
            date=fields.date,
            vendor=fields.vendor,
            amount_total_inr=fields.amount_total_inr,
            gst_paid_inr=fields.gst_paid_inr,
            gst_rate_percent=fields.gst_rate_percent,
            description=fields.description,
            category=fields.category,
            usage_type=fields.usage_type,
            payment_mode=fields.payment_mode
        )
        logger.info("Successfully extracted details for document: %s", file_name)
        return item

    except Exception as api_err:
        logger.exception("Failed to process document vision call for %s: %s", file_name, str(api_err))
        raise
