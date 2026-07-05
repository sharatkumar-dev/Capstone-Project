import time
import logging

logger = logging.getLogger("TaxAssistantApp.ModelCall")

def call_gemini_with_fallback(client, method_name: str, model_args: dict, fallback_models=None):
    """
    Executes a Gemini API model call with built-in retry logic (exponential backoff)
    for 429 and 503 errors, and automatic fallback across alternative models.
    """
    if fallback_models is None:
        # Cascade through available flash and flash-lite models
        fallback_models = [
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-3.5-flash"
        ]
        
    last_exception = None
    
    for model in fallback_models:
        # Set the model parameter for this attempt
        model_args['model'] = model
        retries = 3
        backoff = 2.0 # seconds
        
        for attempt in range(retries):
            try:
                logger.info("Attempting Gemini call using model '%s' (attempt %d/%d)...", model, attempt + 1, retries)
                method = getattr(client.models, method_name)
                response = method(**model_args)
                logger.info("Gemini call succeeded with model '%s'", model)
                return response
            except Exception as e:
                last_exception = e
                err_msg = str(e).lower()
                
                # Check if error is retryable (429 or 503)
                is_retryable = (
                    "429" in err_msg or 
                    "503" in err_msg or 
                    "resource_exhausted" in err_msg or 
                    "unavailable" in err_msg
                )
                
                if is_retryable and attempt < retries - 1:
                    logger.warning("Retryable error encountered on model '%s': %s. Retrying in %.1fs...", model, str(e), backoff)
                    time.sleep(backoff)
                    backoff *= 2.0 # Exponential backoff
                else:
                    logger.warning("Model '%s' failed on attempt %d: %s", model, attempt + 1, str(e))
                    break # Break retry loop, proceed to next fallback model
                    
    # If all models and all retry attempts fail
    logger.error("All fallback models and retries were exhausted.")
    raise last_exception


from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        # Set font
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "TAX COMPLIANCE ADVISORY REPORT - AY 2025-26", border=0, align="R")
        self.ln(15)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Set font
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", border=0, align="C")

def convert_markdown_to_pdf(markdown_text: str) -> bytes:
    """
    Converts structured tax Markdown advisory reports into beautifully formatted PDF documents.
    """
    # Pre-process text to replace unicode rupee symbol to avoid encoding issues with Helvetica
    markdown_text = markdown_text.replace("₹", "INR ").replace("\u20b9", "INR ")

    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Text colors
    navy_color = (30, 58, 138)       # #1E3A8A
    dark_gray = (31, 41, 55)        # #1F2937
    light_gray = (229, 231, 235)    # #E5E7EB

    lines = markdown_text.split("\n")
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
            
        # Headers
        if line.startswith("# "):
            in_list = False
            title_text = line[2:]
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(*navy_color)
            pdf.cell(0, 12, title_text, ln=True)
            pdf.ln(4)
        elif line.startswith("## "):
            in_list = False
            header_text = line[3:]
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(*navy_color)
            pdf.cell(0, 10, header_text, ln=True)
            # Add line separator
            pdf.set_draw_color(*light_gray)
            pdf.set_line_width(0.5)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
            pdf.ln(4)
        elif line.startswith("### "):
            in_list = False
            sub_text = line[4:]
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*dark_gray)
            pdf.cell(0, 8, sub_text, ln=True)
            pdf.ln(2)
        # Horizontal rule
        elif line in ("---", "***", "--- "):
            in_list = False
            pdf.set_draw_color(*light_gray)
            pdf.set_line_width(0.8)
            current_y = pdf.get_y()
            pdf.line(20, current_y + 2, 190, current_y + 2)
            pdf.ln(6)
        # Bulleted List
        elif line.startswith("* ") or line.startswith("- "):
            in_list = True
            bullet_text = line[2:]
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*dark_gray)
            pdf.set_x(25)
            pdf.write(5, "- ")
            
            # Write with bold elements
            parts = bullet_text.split("**")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    pdf.set_font("Helvetica", "B", 10)
                else:
                    pdf.set_font("Helvetica", "", 10)
                pdf.write(5, part)
            pdf.ln(6)
            pdf.set_x(20) # Reset margin
        # Normal text / paragraph
        else:
            in_list = False
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*dark_gray)
            
            parts = line.split("**")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    pdf.set_font("Helvetica", "B", 10)
                else:
                    pdf.set_font("Helvetica", "", 10)
                pdf.write(5, part)
            pdf.ln(7)
            
    # Output bytes
    return pdf.output()

