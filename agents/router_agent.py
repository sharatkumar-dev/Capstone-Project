import os
import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger("TaxAssistantApp.RouterAgent")

class PartialTaxpayerProfile(BaseModel):
    taxpayer_name: Optional[str] = Field(None, description="Name of the individual, professional, or small business entity.")
    assessment_year: Optional[str] = Field(None, description="Relevant Assessment Year (e.g., 2026-27).")
    track: Optional[Literal["Professional", "Small Business"]] = Field(None, description="Presumptive tax track: Professional (Sec 44ADA) or Small Business (Sec 44AD).")
    gross_revenue_inr: Optional[float] = Field(None, description="Total estimated gross receipts/turnover for the financial year.")
    gst_registered: Optional[bool] = Field(None, description="Whether the taxpayer is registered under GST.")
    gstin: Optional[str] = Field(None, description="Indian GSTIN (15 characters), required if registered.")
    preferred_regime: Optional[Literal["Old Regime", "New Regime (Default Sec 115BAC)"]] = Field("New Regime (Default Sec 115BAC)", description="Tax regime choice.")

class RouterResponse(BaseModel):
    assistant_response: str = Field(..., description="Friendly response to the taxpayer. Keep the conversation engaging and ask for missing details.")
    extracted_profile: Optional[PartialTaxpayerProfile] = Field(None, description="The accumulated profile data extracted from the chat history so far.")

def run_router_agent(messages: list) -> RouterResponse:
    """
    Invokes the Router Agent using gemini-2.0-flash with the conversation history.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable is not set. Initializing Client without explicit key (relying on SDK default resolution).")

    # Initialize client (will automatically check for GEMINI_API_KEY internally if api_key is None)
    client = genai.Client(api_key=api_key)
    
    # Load system instruction
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "router_agent.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    except Exception as e:
        logger.exception("Failed to load router agent system instruction: %s", str(e))
        system_instruction = "You are the Router Agent. Categorize taxpayer to Professional or Small Business."

    # Convert conversation messages to SDK types.Content format
    contents = []
    for msg in messages:
        # Map assistant/user roles appropriately
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )

    # Call Gemini model
    try:
        logger.info("Calling Gemini model for Router Agent...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=RouterResponse,
                temperature=0.1
            )
        )
        
        # Parse Response
        if response.parsed:
            return response.parsed
        else:
            logger.warning("response.parsed is None. Attempting manual parsing.")
            import json
            data = json.loads(response.text)
            return RouterResponse.model_validate(data)
            
    except Exception as e:
        logger.exception("Error in Router Agent execution: %s", str(e))
        raise
