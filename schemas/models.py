from pydantic import BaseModel, Field
from typing import Optional, Literal
import datetime

class TaxpayerProfile(BaseModel):
    """
    Pydantic schema representing the onboarded taxpayer's profile.
    """
    taxpayer_name: str = Field(..., description="Name of the individual, professional, or small business entity.")
    assessment_year: str = Field(..., pattern=r"^[0-9]{4}-[0-9]{2}$", description="Relevant Assessment Year (e.g., 2026-27).")
    track: Literal["Professional", "Small Business"] = Field(..., description="Presumptive tax track: Professional (Sec 44ADA) or Small Business (Sec 44AD).")
    gross_revenue_inr: float = Field(..., ge=0.0, description="Total estimated gross receipts/turnover for the financial year.")
    gst_registered: bool = Field(..., description="GST registration status of the taxpayer.")
    gstin: Optional[str] = Field(None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", description="Indian GSTIN (15 characters), required if registered.")
    preferred_regime: Literal["Old Regime", "New Regime (Default Sec 115BAC)"] = Field("New Regime (Default Sec 115BAC)", description="Tax regime choice.")

class ExtractedInvoiceItem(BaseModel):
    """
    Pydantic schema representing a single transaction item extracted from receipts or invoices.
    """
    document_id: str = Field(..., description="Unique filename or document identifier.")
    date: datetime.date = Field(..., description="Date of the transaction (YYYY-MM-DD).")
    vendor: str = Field(..., description="Vendor/Merchant name.")
    amount_total_inr: float = Field(..., ge=0.0, description="Total invoice amount in INR including taxes.")
    gst_paid_inr: float = Field(0.0, ge=0.0, description="GST component paid (CGST+SGST or IGST) if present.")
    gst_rate_percent: Literal[0, 5, 12, 18, 28] = Field(0, description="GST percentage rate.")
    description: str = Field(..., description="Description of the goods or services purchased.")
    category: str = Field(..., description="Expense category classification (e.g., Rent, Software, Hardware, Dining).")
    usage_type: Literal["Pure Business", "Pure Personal", "Mixed", "Unresolved"] = Field("Unresolved", description="Indicates usage scope.")
    payment_mode: Literal["Digital (UPI/Card/NetBanking)", "Cash", "Cheque"] = Field(..., description="Mode of transaction payment (crucial for Sec 44AD calculations).")
