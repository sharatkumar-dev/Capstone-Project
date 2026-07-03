# Python Agents

This folder contains the core logic for the three Python agents in our presumptive tax compliance assistant:

1. **Router Agent (`router_agent.py`)**:
   - Parses the initial user request and profile information.
   - Classifies the user into either the Professional Track (Section 44ADA) or Small Business Track (Section 44AD).
   - Manages orchestration and directs control flow.

2. **Vision Agent (`vision_agent.py`)**:
   - Ingests user-uploaded documents (receipts, invoices, bank statements) in PDF or image format.
   - Leverages `google-genai` multimodal vision capabilities to extract structured line items, dates, values, and GST details.

3. **Calculator Agent (`calculator_agent.py`)**:
   - Applies deterministic presumptive tax rules.
   - Enforces statutory caps (₹75 Lakhs for 44ADA / ₹3 Crores for 44AD).
   - Generates the final audit-ready report and flags ambiguous transactions.
