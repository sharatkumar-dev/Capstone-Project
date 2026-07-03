# Structured Data Schemas

This folder contains Python Pydantic models for enforcing strict, typed boundaries on the data passed between agents and validated by the Streamlit application.

## Contents
- **`schemas/models.py`**: Declares Pydantic V2 models for:
  - `TaxpayerProfile`: Customer onboarding metadata, target track, and GST parameters.
  - `ExtractedInvoiceItem`: Structured receipt details, payment modes, and GST tracking.
