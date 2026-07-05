import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

from PIL import Image
import streamlit as st

# Configure enterprise-grade logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TaxAssistantApp")

# Import Agent Functions
from agents.router_agent import run_router_agent
from agents.vision_agent import analyze_document
from agents.calculator_agent import run_calculation
from schemas.models import TaxpayerProfile

# Page configuration
st.set_page_config(
    page_title="Indian Presumptive Tax Assistant",
    page_icon="💼",
    layout="wide"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global font overwrite - strictly text elements to avoid breaking icon webfonts */
    .stMarkdown, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sleek gradient background for title area */
    .title-gradient {
        background: linear-gradient(90deg, #38bdf8 0%, #06b6d4 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
    }
    
    /* Stage Status Card */
    .stage-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .stage-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stage-badge-router { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .stage-badge-vision { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .stage-badge-calculator { background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    
    /* Taxpayer Profile Card */
    .profile-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.7));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .profile-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 13px;
    }
    .profile-item:last-child {
        border-bottom: none;
    }
    .profile-label {
        color: #94a3b8;
        font-weight: 500;
    }
    .profile-value {
        color: #f1f5f9;
        font-weight: 600;
    }
    
    /* Elegant metric card containers */
    .metric-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #10b981;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .metric-value.itc {
        color: #3b82f6;
    }
    
    /* Global styles for main chat and right columns */
    .stChatInputContainer {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(15, 23, 42, 0.6) !important;
    }
    
    .stDownloadButton button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #1d4ed8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: white !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Premium Tab Customizations */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        white-space: nowrap !important;
        background-color: transparent !important;
        border-radius: 4px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #38bdf8 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Namaste! I am your Indian presumptive tax assistant. Let's get you onboarded first. What is your name or the name of your business entity?"
        }
    ]

if "profile" not in st.session_state:
    st.session_state.profile = None  # Will hold TaxpayerProfile dict once completed

if "temp_profile" not in st.session_state:
    st.session_state.temp_profile = {}  # Holds partially extracted fields

if "transactions" not in st.session_state:
    st.session_state.transactions = []  # Will hold List[ExtractedInvoiceItem]

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()  # Set of filenames already parsed

if "current_agent" not in st.session_state:
    st.session_state.current_agent = "Router"

if "calculation_result" not in st.session_state:
    st.session_state.calculation_result = None  # Holds generated Markdown report

if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = b""  # Holds pre-compiled PDF bytes for stable download

# App Title
st.markdown("<h1 class='title-gradient'>Independent Contractor & Small Business Tax Guide</h1>", unsafe_allow_html=True)
st.markdown("##### *Your 3-Agent Presumptive Tax Compliance Assistant (Sec 44ADA & 44AD)*")
st.write("---")

# Main Page Layout (Full-width tabs are used below for maximum space and professional layout)

# Sidebar - Local state representation and config
with st.sidebar:
    st.markdown("### 🛠️ Controller & Profile")
    
    # Active Agent Indicator
    current_agent = st.session_state.current_agent
    badge_class = f"stage-badge stage-badge-{current_agent.lower()}"
    agent_names = {
        "Router": "Onboarding (Router)",
        "Vision": "Ingestion (Vision/Parser)",
        "Calculator": "Calculation (Calculator)"
    }
    stage_html = f"""
    <div class="stage-card">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.8px;">Active Stage</div>
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
            <span style="font-size: 14px; font-weight: 700; color: #f1f5f9;">{agent_names.get(current_agent, current_agent)}</span>
            <span class="{badge_class}">Active</span>
        </div>
    </div>
    """
    st.markdown(stage_html, unsafe_allow_html=True)
    
    # Debugging profile fields
    if not st.session_state.profile and st.session_state.temp_profile:
        st.markdown("#### ⏳ Partial Progress")
        for k, v in st.session_state.temp_profile.items():
            if v is not None:
                st.markdown(f"- **{k.replace('_', ' ').title()}:** `{v}`")
    
    st.markdown("---")
    st.markdown("### 👤 Taxpayer Profile")
    if st.session_state.profile:
        prof = st.session_state.profile
        gst_status = 'Registered' if prof.get('gst_registered') else 'Not Registered'
        gstin_html = f'<div class="profile-item"><span class="profile-label">GSTIN</span><span class="profile-value">{prof.get("gstin", "N/A")}</span></div>' if prof.get('gst_registered') else ''
        
        profile_html = f"""
        <div class="profile-card">
            <div class="profile-item"><span class="profile-label">Name</span><span class="profile-value">{prof.get('taxpayer_name', 'N/A')}</span></div>
            <div class="profile-item"><span class="profile-label">Track</span><span class="profile-value">{prof.get('track', 'N/A')}</span></div>
            <div class="profile-item"><span class="profile-label">AY</span><span class="profile-value">{prof.get('assessment_year', 'N/A')}</span></div>
            <div class="profile-item"><span class="profile-label">Gross Revenue</span><span class="profile-value" style="color: #10b981;">₹{prof.get('gross_revenue_inr', 0):,.2f}</span></div>
            <div class="profile-item"><span class="profile-label">GST Status</span><span class="profile-value">{gst_status}</span></div>
            {gstin_html}
            <div class="profile-item"><span class="profile-label">Regime</span><span class="profile-value" style="font-size:11px;">{prof.get('preferred_regime', 'N/A')}</span></div>
        </div>
        """
        st.markdown(profile_html, unsafe_allow_html=True)
        
        # Turnover limit progress bar & threshold alerts
        track = prof.get("track")
        revenue = prof.get("gross_revenue_inr", 0.0)
        if track == "Professional":
            limit = 7500000.0
            limit_label = "₹75 Lakhs (Sec 44ADA)"
        else:
            digital = prof.get("digital_revenue_inr") or 0.0
            cash = prof.get("cash_revenue_inr") or 0.0
            total = digital + cash if (digital + cash) > 0 else revenue
            cash_pct = (cash / total) if total > 0 else 0.0
            if cash_pct > 0.05:
                limit = 20000000.0
                limit_label = "₹2 Crores (Sec 44AD - Cash > 5%)"
                st.warning(f"⚠️ Cash receipts are {cash_pct*100:.1f}% (>5%). Sec 44AD limit reduced to ₹2 Crores.")
            else:
                limit = 30000000.0
                limit_label = "₹3 Crores (Sec 44AD)"
        
        progress_val = min(revenue / limit, 1.0)
        st.markdown(f"**Turnover Headroom Used** ({revenue*100/limit:.1f}%)")
        st.progress(progress_val)
        st.caption(f"₹{revenue:,.2f} of {limit_label}")
    else:
        st.markdown("""
        <div class="profile-card" style="border-left: 4px solid #eab308; background-color: rgba(234, 179, 8, 0.05);">
            <div style="font-size: 13px; color: #fbbf24; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                <span>⚠️ Profile Incomplete</span>
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
                Please complete the onboarding conversation to establish your tax profile and track.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("### 📂 Document Ingest")
    uploaded_files = st.file_uploader(
        "Upload receipts/invoices (PDF, PNG, JPG, JPEG)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        disabled=(st.session_state.profile is None) # Disable until onboarding is done
    )
    
    if st.session_state.profile is None and uploaded_files:
        st.error("Please complete onboarding first so we know your tax track before digesting documents.")
    
    # Process uploaded files
    if st.session_state.profile and uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                with st.spinner(f"Ingesting & parsing `{uploaded_file.name}`..."):
                    try:
                        file_bytes = uploaded_file.read()
                        mime_type = uploaded_file.type
                        
                        # Call Vision Agent
                        item = analyze_document(uploaded_file.name, file_bytes, mime_type)
                        
                        # Add to list
                        st.session_state.transactions.append(item.model_dump())
                        st.session_state.processed_files.add(uploaded_file.name)
                        st.success(f"Parsed `{uploaded_file.name}` successfully!")
                        st.rerun()
                    except Exception as parse_err:
                        logger.exception("Failed to parse document %s: %s", uploaded_file.name, str(parse_err))
                        st.error(f"Error parsing `{uploaded_file.name}`: {str(parse_err)}")
                
    st.markdown("---")
    st.markdown("### 📊 Live Summary")
    # Only count Pure Business and Mixed (or Unresolved) items that are not Personal
    eligible_expenses = [
        t for t in st.session_state.transactions 
        if t.get('usage_type') in ["Pure Business", "Mixed", "Unresolved"]
    ]
    total_expenses = sum(t.get('amount_total_inr', 0.0) for t in eligible_expenses)
    
    # GST ITC is only eligible if taxpayer is registered and it is business related
    if st.session_state.profile and st.session_state.profile.get("gst_registered"):
        total_gst_paid = sum(t.get('gst_paid_inr', 0.0) for t in eligible_expenses)
    else:
        total_gst_paid = 0.0
        
    summary_html = f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-title">Total Eligible Expenses</div>
            <div class="metric-value">₹{total_expenses:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Eligible GST ITC</div>
            <div class="metric-value itc">₹{total_gst_paid:,.2f}</div>
        </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

# Main Page Layout (Full-width Tabs)
tab_chat, tab_ledger, tab_report = st.tabs([
    "💬 Onboarding Chat & CA Assistant", 
    "📋 Bookkeeping Ledger", 
    "📄 Tax Compliance Report"
])

with tab_chat:
    st.markdown("### 💬 Tax Agent Chat")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input
    if prompt := st.chat_input("Type your response here..."):
        # Append User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Call Router Agent if profile not completed
        if st.session_state.profile is None:
            with st.spinner("CA Alok is reviewing your profile..."):
                try:
                    response = run_router_agent(st.session_state.messages)
                    
                    # Merge any extracted fields into temp_profile
                    if response.extracted_profile:
                        extracted_dict = response.extracted_profile.model_dump(exclude_none=True)
                        for field, val in extracted_dict.items():
                            st.session_state.temp_profile[field] = val
                    
                    # Append assistant reply to messages
                    st.session_state.messages.append({"role": "assistant", "content": response.assistant_response})
                    
                    # Check if onboarding profile is complete and valid
                    required_fields = ["taxpayer_name", "assessment_year", "track", "gross_revenue_inr", "gst_registered"]
                    is_complete = all(st.session_state.temp_profile.get(f) is not None for f in required_fields)
                    if is_complete and st.session_state.temp_profile.get("gst_registered") is True:
                        if st.session_state.temp_profile.get("gstin") is None:
                            is_complete = False
                    if is_complete and st.session_state.temp_profile.get("track") == "Small Business":
                        if st.session_state.temp_profile.get("digital_revenue_inr") is None or st.session_state.temp_profile.get("cash_revenue_inr") is None:
                            is_complete = False
                            
                    if is_complete:
                        try:
                            # Validate using Pydantic TaxpayerProfile schema
                            profile_instance = TaxpayerProfile(**st.session_state.temp_profile)
                            
                            # Update session state profile
                            st.session_state.profile = st.session_state.temp_profile
                            st.session_state.current_agent = "Vision"
                            
                            track = st.session_state.profile.get("track")
                            revenue = st.session_state.profile.get("gross_revenue_inr", 0)
                            
                            audit_warning = ""
                            if track == "Professional" and revenue > 7500000:
                                audit_warning = "\n\n⚠️ **CRITICAL WARNING:** Your estimated revenue exceeds the statutory limit of ₹75 Lakhs for Section 44ADA. **AUDIT IS COMPULSORY UNDER SECTION 44AB.**"
                            elif track == "Small Business" and revenue > 30000000:
                                audit_warning = "\n\n⚠️ **CRITICAL WARNING:** Your estimated revenue exceeds the statutory limit of ₹3 Crores for Section 44AD. **AUDIT IS COMPULSORY UNDER SECTION 44AB.**"
                            
                            congrats_message = f"🎉 **Onboarding Complete!**\n\nI have verified your taxpayer profile as a **{track}** under the **{st.session_state.profile.get('preferred_regime', 'New Regime')}**.{audit_warning}\n\nYou can now upload your business invoices/receipts in the sidebar to begin ingestion."
                            st.session_state.messages.append({"role": "assistant", "content": congrats_message})
                        except Exception as val_err:
                            logger.warning("Profile parsed but schema validation failed: %s", str(val_err))
                            
                    st.rerun()
                except Exception as e:
                    logger.exception("Failed to run Router Agent: %s", str(e))
                    st.error(f"Failed to communicate with onboarding agent. Error: {str(e)}")
        else:
            with st.chat_message("assistant"):
                response_text = f"Your onboarding profile is active. Track is **{st.session_state.profile.get('track')}**. Upload invoices in the sidebar to parse them and view them in the ledger."
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

with tab_ledger:
    st.markdown("### 📋 Bookkeeping Ledger")
    if not st.session_state.transactions:
        st.info("No transactions extracted yet. Upload files in the sidebar to begin parsing.")
    else:
        # Interactive filters to organize transaction review
        filter_option = st.radio(
            "Filter Transactions by Scope",
            options=["Show All", "💼 Business", "❌ Personal", "⚠️ Mixed", "❓ Unresolved"],
            horizontal=True,
            key="ledger_filter_scope"
        )
        
        filter_map = {
            "💼 Business": "Pure Business",
            "❌ Personal": "Pure Personal",
            "⚠️ Mixed": "Mixed",
            "❓ Unresolved": "Unresolved"
        }
        
        # Loop over transactions with edit widgets
        for idx, txn in enumerate(st.session_state.transactions):
            usage = txn.get('usage_type', 'Unresolved')
            
            # Apply filter
            if filter_option != "Show All" and usage != filter_map[filter_option]:
                continue
                
            badge = "💼 Business"
            if usage == "Pure Personal":
                badge = "❌ Personal"
            elif usage == "Mixed":
                badge = "⚠️ Mixed"
            elif usage == "Unresolved":
                badge = "❓ Unresolved"
                
            expander_title = f"{badge} | {txn.get('vendor', 'Unknown')} — ₹{txn.get('amount_total_inr', 0):,.2f}"
                
            with st.expander(expander_title):
                # 3 columns for general and financial data to clean up layout
                col1, col2, col3 = st.columns(3)
                with col1:
                    edit_vendor = st.text_input("Vendor", value=txn.get('vendor'), key=f"vendor_{idx}")
                    edit_date = st.date_input("Date", value=txn.get('date'), key=f"date_{idx}")
                with col2:
                    edit_amount = st.number_input("Amount Total (INR)", value=float(txn.get('amount_total_inr', 0.0)), min_value=0.0, key=f"amount_{idx}")
                    edit_gst = st.number_input("GST Paid (INR)", value=float(txn.get('gst_paid_inr', 0.0)), min_value=0.0, key=f"gst_{idx}")
                with col3:
                    rates = [0, 5, 12, 18, 28]
                    current_rate = txn.get('gst_rate_percent', 0)
                    default_rate_idx = rates.index(current_rate) if current_rate in rates else 0
                    edit_rate = st.selectbox("GST Rate %", options=rates, index=default_rate_idx, key=f"rate_{idx}")
                    
                    pms = ["Digital (UPI/Card/NetBanking)", "Cash", "Cheque"]
                    current_pm = txn.get('payment_mode', 'Digital (UPI/Card/NetBanking)')
                    default_pm_idx = pms.index(current_pm) if current_pm in pms else 0
                    edit_pm = st.selectbox("Payment Mode", options=pms, index=default_pm_idx, key=f"payment_{idx}")
                
                # Bottom columns for categorization & description
                col_left, col_right = st.columns(2)
                with col_left:
                    edit_desc = st.text_area("Description", value=txn.get('description', ''), key=f"desc_{idx}", height=68)
                with col_right:
                    edit_cat = st.text_input("Category", value=txn.get('category', ''), key=f"category_{idx}")
                    usages = ["Pure Business", "Pure Personal", "Mixed", "Unresolved"]
                    current_usage = txn.get('usage_type', 'Unresolved')
                    default_usage_idx = usages.index(current_usage) if current_usage in usages else 3
                    edit_usage = st.selectbox("Usage Scope", options=usages, index=default_usage_idx, key=f"usage_{idx}")
                
                # Directly update state
                st.session_state.transactions[idx] = {
                    "document_id": txn.get('document_id'),
                    "date": edit_date,
                    "vendor": edit_vendor,
                    "amount_total_inr": edit_amount,
                    "gst_paid_inr": edit_gst,
                    "gst_rate_percent": edit_rate,
                    "description": edit_desc,
                    "category": edit_cat,
                    "usage_type": edit_usage,
                    "payment_mode": edit_pm
                }

with tab_report:
    st.markdown("### 📄 Tax Compliance Advisory Report")
    
    # Report generation button (at the top of the report tab)
    report_btn = st.button(
        "Run Presumptive Tax Calculation & Generate Report",
        disabled=(st.session_state.profile is None or not st.session_state.transactions),
        use_container_width=True
    )
    if report_btn:
        st.session_state.current_agent = "Calculator"
        with st.spinner("Calculator Agent is executing presumptive logic..."):
            try:
                report = run_calculation(st.session_state.profile, st.session_state.transactions)
                st.session_state.calculation_result = report
                # Cache PDF bytes immediately after generation so download is stable
                try:
                    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Tax_Compliance_Report_FY2026.pdf")
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pf:
                            st.session_state.pdf_report_bytes = pf.read()
                    else:
                        from agents.utils import convert_markdown_to_pdf
                        st.session_state.pdf_report_bytes = convert_markdown_to_pdf(report)
                except Exception as pdf_err:
                    logger.warning("Could not pre-cache PDF bytes: %s", str(pdf_err))
                    st.session_state.pdf_report_bytes = b""
                st.success("Calculations complete!")
                st.rerun()
            except Exception as calc_err:
                logger.exception("Calculator Agent execution failed: %s", str(calc_err))
                st.error(f"Calculation failed: {str(calc_err)}")
                
    st.markdown("---")
    
    if st.session_state.calculation_result:
        st.success("Analysis report generated successfully!")
        
        # Serve PDF from session_state cache (pre-compiled at generation time)
        pdf_bytes = st.session_state.get("pdf_report_bytes", b"")

        # If not yet cached (e.g. page reload after restart), reload from disk
        if not pdf_bytes:
            try:
                pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Tax_Compliance_Report_FY2026.pdf")
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pf:
                        pdf_bytes = pf.read()
                    st.session_state.pdf_report_bytes = pdf_bytes
            except Exception as e:
                logger.exception("Failed to load PDF from disk: %s", str(e))

        if pdf_bytes:
            st.download_button(
                label="📥 Download Official Tax Compliance Report (PDF)",
                data=pdf_bytes,
                file_name="Tax_Compliance_Report_FY2026.pdf",
                mime="application/pdf",
                key="pdf_download_btn",
                use_container_width=True
            )
        else:
            st.download_button(
                label="📥 Download Official Tax Compliance Report (.md)",
                data=st.session_state.calculation_result,
                file_name="Tax_Compliance_Report_FY2026.md",
                mime="text/markdown",
                key="md_download_btn",
                use_container_width=True
            )
        # Visual comparison metrics and chart
        try:
            import pandas as pd
            prof = st.session_state.profile
            revenue = prof.get("gross_revenue_inr", 0.0)
            track = prof.get("track")
            
            # 1. Option A: Presumptive Deemed Income
            if track == "Professional":
                presumptive_income = revenue * 0.5
            else:
                digital = prof.get("digital_revenue_inr") or 0.0
                cash = prof.get("cash_revenue_inr") or 0.0
                presumptive_income = (digital * 0.06) + (cash * 0.08)
                
            # 2. Option B: Actual Net Income (Revenue - Expenses)
            eligible_exps = [
                t for t in st.session_state.transactions 
                if t.get('usage_type') in ["Pure Business", "Mixed", "Unresolved"]
            ]
            local_total_expenses = sum(t.get('amount_total_inr', 0.0) for t in eligible_exps)
            actual_net_income = max(revenue - local_total_expenses, 0.0)
            
            # Two column layout for visual impact
            chart_col, metrics_col = st.columns([2, 1])
            with chart_col:
                st.markdown("#### 📊 Comparative Analysis: Taxable Income")
                comparison_df = pd.DataFrame({
                    "Filing Option": ["Option A: Presumptive", "Option B: Regular (Net Income)"],
                    "Amount (INR)": [presumptive_income, actual_net_income]
                })
                st.bar_chart(data=comparison_df, x="Filing Option", y="Amount (INR)", use_container_width=True)
            with metrics_col:
                st.markdown("#### 💡 Quick Comparison")
                st.metric(label="Option A (Deemed Income)", value=f"₹{presumptive_income:,.2f}")
                st.metric(label="Option B (Actual Net Income)", value=f"₹{actual_net_income:,.2f}", delta=f"₹{actual_net_income - presumptive_income:,.2f}" if actual_net_income > presumptive_income else None, delta_color="inverse")
                
                # Dynamic advice
                if actual_net_income < presumptive_income:
                    st.info("💡 **Recommendation**: Option B (Regular Filing) has lower taxable income. You might consider standard bookkeeping and audit.")
                else:
                    st.info("💡 **Recommendation**: Option A (Presumptive) has lower taxable income. Highly recommended for compliance savings!")
            st.markdown("---")
        except Exception as chart_err:
            logger.warning("Failed to render comparison chart: %s", str(chart_err))

        st.markdown(st.session_state.calculation_result)
    else:
        st.info("The final report will appear here once calculations are run.")
