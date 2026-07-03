import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger("TaxAssistantApp.CalculatorAgent")

def run_calculation(profile: dict, transactions: list) -> str:
    """
    Performs presumptive tax math, enforces caps, invokes the Gemini 2.0 model
    to write a clean audit-ready markdown report, and saves it to the reports folder.
    """
    # 1. Read profile metadata
    taxpayer_name = profile.get("taxpayer_name", "Valued Taxpayer")
    track = profile.get("track", "Professional")
    gross_revenue = float(profile.get("gross_revenue_inr", 0.0))
    gst_registered = bool(profile.get("gst_registered", False))
    gstin = profile.get("gstin", "")
    preferred_regime = profile.get("preferred_regime", "New Regime (Default Sec 115BAC)")
    assessment_year = profile.get("assessment_year", "2026-27")

    # 2. Enforce statutory caps & refuse calculations if exceeded
    # Cap 44ADA = ₹75 Lakhs (7,500,000)
    # Cap 44AD = ₹3 Crores (30,000,000)
    refusal_reason = ""
    is_refused = False
    
    if track == "Professional" and gross_revenue > 7500000:
        is_refused = True
        refusal_reason = (
            "STATUTORY CAP EXCEEDED: Section 44AB tax audit compulsory. "
            "Estimated revenue of ₹{:,} exceeds the statutory cap of ₹75 Lakhs for Section 44ADA."
        ).format(int(gross_revenue))
        logger.warning(refusal_reason)
    elif track == "Small Business" and gross_revenue > 30000000:
        is_refused = True
        refusal_reason = (
            "STATUTORY CAP EXCEEDED: Section 44AB tax audit compulsory. "
            "Estimated turnover of ₹{:,} exceeds the statutory cap of ₹3 Crores for Section 44AD."
        ).format(int(gross_revenue))
        logger.warning(refusal_reason)

    # 3. Perform calculations (if not refused)
    presumptive_income = 0.0
    digital_turnover = 0.0
    cash_turnover = 0.0
    digital_sum = 0.0
    cash_sum = 0.0
    
    # Separate expenses & categorize transactions
    business_txns = []
    personal_txns = []
    flagged_txns = []
    
    for t in transactions:
        usage = t.get("usage_type", "Unresolved")
        if usage == "Pure Personal":
            personal_txns.append(t)
        elif usage in ["Mixed", "Unresolved"]:
            flagged_txns.append(t)
            business_txns.append(t)  # Include for visibility but note flags
        else:
            business_txns.append(t)

    # Sum total expenses and GST ITC from business-related transactions
    total_business_expenses = sum(t.get("amount_total_inr", 0.0) for t in business_txns)
    eligible_gst_itc = sum(t.get("gst_paid_inr", 0.0) for t in business_txns) if gst_registered else 0.0

    if not is_refused:
        if track == "Professional":
            presumptive_income = gross_revenue * 0.50
        else:
            # Section 44AD Small Business digital/cash ratio
            # Digital = UPI, Card, NetBanking, Cheque. Cash = Cash.
            digital_txns = [t for t in transactions if t.get("payment_mode") in ["Digital (UPI/Card/NetBanking)", "Cheque"]]
            cash_txns = [t for t in transactions if t.get("payment_mode") == "Cash"]
            
            digital_sum = sum(t.get("amount_total_inr", 0.0) for t in digital_txns)
            cash_sum = sum(t.get("amount_total_inr", 0.0) for t in cash_txns)
            total_sum = digital_sum + cash_sum
            
            if total_sum > 0:
                digital_ratio = digital_sum / total_sum
                cash_ratio = cash_sum / total_sum
            else:
                digital_ratio = 1.0  # Default to digital if no transactions
                cash_ratio = 0.0
                
            digital_turnover = gross_revenue * digital_ratio
            cash_turnover = gross_revenue * cash_ratio
            
            presumptive_income = (digital_turnover * 0.06) + (cash_turnover * 0.08)

    # 4. Generate structured text to feed into the Gemini report writer
    prompt_data = f"""
    Taxpayer Name: {taxpayer_name}
    Track: {track} (Section {"44ADA" if track == "Professional" else "44AD"})
    Estimated Revenue: INR {gross_revenue:,.2f}
    GST Registered: {gst_registered}
    GSTIN: {gstin if gst_registered else "N/A"}
    Assessment Year: {assessment_year}
    Preferred Regime: {preferred_regime}
    
    Refusal Flag: {is_refused}
    Refusal Reason: {refusal_reason}
    
    Calculations (if applicable):
    - Presumptive Income: INR {presumptive_income:,.2f}
    - Digital Turnover Portion: INR {digital_turnover:,.2f} (Turnover received via banking channels/UPI)
    - Cash Turnover Portion: INR {cash_turnover:,.2f} (Turnover received in cash)
    
    Ledger Expenses:
    - Total Business-Related Expenses Incurred: INR {total_business_expenses:,.2f}
    - Total Eligible GST Input Tax Credit (ITC): INR {eligible_gst_itc:,.2f}
    - Number of Flagged/Mixed-Use Transactions: {len(flagged_txns)}
    - Number of Pure Personal Transactions: {len(personal_txns)}
    
    Confirmed Business Transaction items:
    {[{'date': str(t.get('date')), 'vendor': t.get('vendor'), 'amount': t.get('amount_total_inr'), 'mode': t.get('payment_mode'), 'usage': t.get('usage_type')} for t in business_txns]}
    
    Flagged Transaction items (Mixed/Unresolved):
    {[{'date': str(t.get('date')), 'vendor': t.get('vendor'), 'amount': t.get('amount_total_inr'), 'description': t.get('description'), 'usage': t.get('usage_type')} for t in flagged_txns]}
    """

    # 5. Load system instruction
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "calculator_agent.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    except Exception as e:
        logger.exception("Failed to load calculator agent system instruction: %s", str(e))
        system_instruction = "You are the Calculator Agent. Summarize tax presumptive calculations and flags into a clean compliance report."

    # 6. Call Gemini 2.0 to draft the Markdown report
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    try:
        logger.info("Calling Gemini 2.0 model for Calculator Agent report writer...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Write a professional tax compliance advisory report in Markdown format using the following details.",
                prompt_data
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        report_content = response.text
        
        # 7. Write to local directory
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "Tax_Compliance_Report_FY2026.md")
        
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(report_content)
            
        logger.info("Successfully generated and saved compliance report to: %s", report_path)
        return report_content

    except Exception as api_err:
        logger.exception("Failed to call Gemini model for Calculator Agent report writer: %s", str(api_err))
        raise
