import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
from functools import wraps
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

st.set_page_config(page_title="NYZTrade DCF Pro", page_icon="📊", layout="wide")

# ============================================
# AUTHENTICATION
# ============================================
def check_password():
    def password_entered():
        username = st.session_state["username"].strip().lower()
        password = st.session_state["password"]
        users = {"demo": "demo123", "premium": "niyas123", "niyas": "nyztrade123"}
        if username in users and password == users[username]:
            st.session_state["password_correct"] = True
            st.session_state["authenticated_user"] = username
            del st.session_state["password"]
            return
        st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
            .login-container {
                max-width: 450px;
                margin: 0 auto;
                padding: 40px;
            }
            .login-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 60px 40px;
                border-radius: 24px;
                text-align: center;
                margin-bottom: 40px;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
            }
            .login-header h1 {
                color: white;
                font-size: 2.8rem;
                margin: 0;
                font-weight: 700;
            }
            .login-header p {
                color: rgba(255,255,255,0.85);
                font-size: 1.1rem;
                margin-top: 10px;
            }
        </style>
        <div class="login-header">
            <h1>📊 NYZTrade DCF Pro</h1>
            <p>Professional Discounted Cash Flow Valuation</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.text_input("👤 Username", key="username", placeholder="Enter username")
                st.text_input("🔒 Password", type="password", key="password", placeholder="Enter password")
                st.button("🚀 Login", on_click=password_entered, use_container_width=True, type="primary")
                st.caption("Demo: `demo/demo123` | Premium: `premium/niyas123`")
        return False
    elif not st.session_state["password_correct"]:
        st.error("❌ Incorrect credentials. Please try again.")
        return False
    return True

if not check_password():
    st.stop()

# ============================================
# ENHANCED CUSTOM STYLES - Modern Dark Theme
# ============================================
st.markdown("""
<style>
/* Global Styles */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(180deg, #0a0a0f 0%, #13131a 100%);
}

/* Main Header */
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 40px 50px;
    border-radius: 24px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.05);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #667eea);
    background-size: 300% 100%;
    animation: gradient-flow 4s ease infinite;
}
@keyframes gradient-flow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.main-header h1 {
    color: #fff;
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header .subtitle {
    color: rgba(255,255,255,0.7);
    font-size: 1.1rem;
    margin-top: 8px;
}

/* Glass Card Style */
.glass-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 24px;
    margin: 12px 0;
    transition: all 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(255,255,255,0.15);
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

/* DCF Value Box - Hero Style */
.dcf-hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px;
    border-radius: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}
.dcf-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}
.dcf-hero h3 {
    color: rgba(255,255,255,0.9);
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 0 0 10px 0;
    position: relative;
}
.dcf-hero .value {
    color: #fff;
    font-size: 3.5rem;
    font-weight: 700;
    margin: 0;
    position: relative;
}
.dcf-hero .current {
    color: rgba(255,255,255,0.75);
    font-size: 1.1rem;
    margin-top: 12px;
    position: relative;
}

/* Upside/Downside Cards */
.upside-card {
    padding: 35px;
    border-radius: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.upside-positive {
    background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
    box-shadow: 0 15px 40px rgba(0, 184, 148, 0.4);
}
.upside-negative {
    background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
    box-shadow: 0 15px 40px rgba(214, 48, 49, 0.4);
}
.upside-card h3 {
    color: rgba(255,255,255,0.9);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 0 0 10px 0;
}
.upside-card .value {
    color: #fff;
    font-size: 3rem;
    font-weight: 700;
}
.upside-card .label {
    color: rgba(255,255,255,0.8);
    font-size: 1rem;
    margin-top: 8px;
}

/* Metric Cards Grid */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
    margin: 20px 0;
}
.metric-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}
.metric-item:hover {
    background: rgba(255,255,255,0.06);
    border-color: rgba(102, 126, 234, 0.5);
}
.metric-item .label {
    color: rgba(255,255,255,0.5);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.metric-item .value {
    color: #fff;
    font-size: 1.4rem;
    font-weight: 600;
}

/* Recommendation Badges */
.rec-badge {
    padding: 30px;
    border-radius: 20px;
    text-align: center;
    font-weight: 700;
    position: relative;
    overflow: hidden;
}
.rec-strong-buy {
    background: linear-gradient(135deg, #00b894 0%, #55efc4 100%);
    box-shadow: 0 15px 40px rgba(0, 184, 148, 0.4);
}
.rec-buy {
    background: linear-gradient(135deg, #00cec9 0%, #81ecec 100%);
    box-shadow: 0 15px 40px rgba(0, 206, 201, 0.4);
}
.rec-hold {
    background: linear-gradient(135deg, #fdcb6e 0%, #ffeaa7 100%);
    color: #2d3436 !important;
    box-shadow: 0 15px 40px rgba(253, 203, 110, 0.4);
}
.rec-avoid {
    background: linear-gradient(135deg, #e17055 0%, #fab1a0 100%);
    box-shadow: 0 15px 40px rgba(225, 112, 85, 0.4);
}
.rec-badge .title {
    font-size: 1.8rem;
    color: #fff;
    margin-bottom: 8px;
}
.rec-badge .subtitle {
    font-size: 1.1rem;
    color: rgba(255,255,255,0.85);
}

/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 30px 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.section-header h2 {
    color: #fff;
    font-size: 1.4rem;
    font-weight: 600;
    margin: 0;
}
.section-header .icon {
    font-size: 1.5rem;
}

/* Data Tables */
.styled-table {
    background: rgba(255,255,255,0.02);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Info Cards */
.info-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 16px 0;
}
.info-card h4 {
    color: #667eea;
    margin: 0 0 10px 0;
    font-size: 1rem;
}
.info-card p {
    color: rgba(255,255,255,0.7);
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Feature Cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin: 30px 0;
}
.feature-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    transition: all 0.3s ease;
}
.feature-card:hover {
    transform: translateY(-5px);
    border-color: rgba(102, 126, 234, 0.5);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}
.feature-card .icon {
    font-size: 2.5rem;
    margin-bottom: 15px;
}
.feature-card h3 {
    color: #fff;
    font-size: 1.1rem;
    margin: 0 0 10px 0;
}
.feature-card p {
    color: rgba(255,255,255,0.6);
    font-size: 0.9rem;
    margin: 0;
    line-height: 1.5;
}

/* WACC Component Cards */
.wacc-component {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin: 8px 0;
}
.wacc-component .label {
    color: rgba(255,255,255,0.6);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.wacc-component .value {
    color: #667eea;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 8px 0;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 40px 0;
}

/* Footer */
.footer {
    text-align: center;
    padding: 40px;
    color: rgba(255,255,255,0.4);
    font-size: 0.9rem;
}
.footer a {
    color: #667eea;
    text-decoration: none;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# STOCK UNIVERSE
# ============================================
POPULAR_STOCKS = {
    "🔵 Large Cap - Nifty 50": {
        "RELIANCE.NS": "Reliance Industries", "TCS.NS": "TCS", "HDFCBANK.NS": "HDFC Bank",
        "INFY.NS": "Infosys", "ICICIBANK.NS": "ICICI Bank", "HINDUNILVR.NS": "Hindustan Unilever",
        "ITC.NS": "ITC", "SBIN.NS": "State Bank of India", "BHARTIARTL.NS": "Bharti Airtel",
        "KOTAKBANK.NS": "Kotak Mahindra Bank", "LT.NS": "Larsen & Toubro", "AXISBANK.NS": "Axis Bank",
        "ASIANPAINT.NS": "Asian Paints", "MARUTI.NS": "Maruti Suzuki", "TITAN.NS": "Titan Company",
        "BAJFINANCE.NS": "Bajaj Finance", "WIPRO.NS": "Wipro", "SUNPHARMA.NS": "Sun Pharma",
        "ULTRACEMCO.NS": "UltraTech Cement", "NESTLEIND.NS": "Nestle India", "HCLTECH.NS": "HCL Technologies",
        "TATAMOTORS.NS": "Tata Motors", "POWERGRID.NS": "Power Grid", "NTPC.NS": "NTPC",
        "ONGC.NS": "ONGC", "M&M.NS": "Mahindra & Mahindra", "JSWSTEEL.NS": "JSW Steel",
        "TATASTEEL.NS": "Tata Steel", "ADANIENT.NS": "Adani Enterprises", "ADANIPORTS.NS": "Adani Ports"
    },
    "🟢 Mid Cap - Growth": {
        "JINDALSTEL.NS": "Jindal Steel", "TRENT.NS": "Trent", "PERSISTENT.NS": "Persistent Systems",
        "PIIND.NS": "PI Industries", "DIXON.NS": "Dixon Technologies", "VOLTAS.NS": "Voltas",
        "MPHASIS.NS": "Mphasis", "COFORGE.NS": "Coforge", "LTIM.NS": "LTIMindtree",
        "AUROPHARMA.NS": "Aurobindo Pharma", "TORNTPHARM.NS": "Torrent Pharma", "ALKEM.NS": "Alkem Lab",
        "POLYCAB.NS": "Polycab India", "HAVELLS.NS": "Havells India", "CROMPTON.NS": "Crompton Greaves",
        "ASTRAL.NS": "Astral Ltd", "SUPREMEIND.NS": "Supreme Industries", "APLAPOLLO.NS": "APL Apollo",
        "SYNGENE.NS": "Syngene International", "LALPATHLAB.NS": "Dr Lal PathLabs"
    },
    "🟡 Small Cap - High Growth": {
        "AMBER.NS": "Amber Enterprises", "AETHER.NS": "Aether Industries", "ANGELONE.NS": "Angel One",
        "CAMPUS.NS": "Campus Activewear", "DATAPATTNS.NS": "Data Patterns", "EASEMYTRIP.NS": "EaseMyTrip",
        "FIVESTAR.NS": "Five Star Business", "GLAND.NS": "Gland Pharma", "HAPPSTMNDS.NS": "Happiest Minds",
        "HOMEFIRST.NS": "Home First Finance", "INDIAMART.NS": "IndiaMART", "JUSTDIAL.NS": "Just Dial",
        "LATENTVIEW.NS": "LatentView Analytics", "NAZARA.NS": "Nazara Technologies", 
        "OLECTRA.NS": "Olectra Greentech", "ROUTE.NS": "Route Mobile", "SOLARINDS.NS": "Solar Industries"
    },
    "🏦 Sectoral - Banking": {
        "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "SBI",
        "KOTAKBANK.NS": "Kotak Bank", "AXISBANK.NS": "Axis Bank", "INDUSINDBK.NS": "IndusInd Bank",
        "BANDHANBNK.NS": "Bandhan Bank", "FEDERALBNK.NS": "Federal Bank", "IDFCFIRSTB.NS": "IDFC First",
        "AUBANK.NS": "AU Small Finance"
    },
    "💻 Sectoral - IT": {
        "TCS.NS": "TCS", "INFY.NS": "Infosys", "WIPRO.NS": "Wipro", "HCLTECH.NS": "HCL Tech",
        "TECHM.NS": "Tech Mahindra", "LTIM.NS": "LTIMindtree", "MPHASIS.NS": "Mphasis",
        "COFORGE.NS": "Coforge", "PERSISTENT.NS": "Persistent", "LTTS.NS": "L&T Technology",
        "CYIENT.NS": "Cyient", "TATAELXSI.NS": "Tata Elxsi", "KPITTECH.NS": "KPIT Tech"
    },
    "💊 Sectoral - Pharma": {
        "SUNPHARMA.NS": "Sun Pharma", "DRREDDY.NS": "Dr Reddy's", "CIPLA.NS": "Cipla",
        "DIVISLAB.NS": "Divi's Labs", "AUROPHARMA.NS": "Aurobindo Pharma", "LUPIN.NS": "Lupin",
        "TORNTPHARM.NS": "Torrent Pharma", "ALKEM.NS": "Alkem Lab", "BIOCON.NS": "Biocon",
        "GLENMARK.NS": "Glenmark", "IPCALAB.NS": "IPCA Labs", "LAURUSLABS.NS": "Laurus Labs"
    }
}

# Industry-specific parameters
INDUSTRY_PARAMS = {
    'Technology': {'beta': 1.15, 'debt_equity': 0.1, 'tax_rate': 0.25, 'terminal_growth': 0.04, 'ev_ebitda': 18},
    'Financial Services': {'beta': 1.0, 'debt_equity': 0.8, 'tax_rate': 0.25, 'terminal_growth': 0.035, 'ev_ebitda': 12},
    'Consumer Cyclical': {'beta': 1.2, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.04, 'ev_ebitda': 15},
    'Consumer Defensive': {'beta': 0.7, 'debt_equity': 0.3, 'tax_rate': 0.25, 'terminal_growth': 0.03, 'ev_ebitda': 20},
    'Healthcare': {'beta': 0.9, 'debt_equity': 0.2, 'tax_rate': 0.25, 'terminal_growth': 0.04, 'ev_ebitda': 16},
    'Industrials': {'beta': 1.1, 'debt_equity': 0.5, 'tax_rate': 0.25, 'terminal_growth': 0.035, 'ev_ebitda': 12},
    'Energy': {'beta': 1.3, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.02, 'ev_ebitda': 8},
    'Basic Materials': {'beta': 1.25, 'debt_equity': 0.35, 'tax_rate': 0.25, 'terminal_growth': 0.025, 'ev_ebitda': 10},
    'Real Estate': {'beta': 0.9, 'debt_equity': 0.7, 'tax_rate': 0.25, 'terminal_growth': 0.03, 'ev_ebitda': 14},
    'Utilities': {'beta': 0.6, 'debt_equity': 0.8, 'tax_rate': 0.25, 'terminal_growth': 0.025, 'ev_ebitda': 10},
    'Communication Services': {'beta': 1.0, 'debt_equity': 0.5, 'tax_rate': 0.25, 'terminal_growth': 0.035, 'ev_ebitda': 12},
    'Default': {'beta': 1.0, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.03, 'ev_ebitda': 12}
}

# ============================================
# UTILITY FUNCTIONS
# ============================================
def retry_with_backoff(retries=5, backoff_in_seconds=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    time.sleep(backoff_in_seconds * 2 ** x)
                    x += 1
        return wrapper
    return decorator

@st.cache_data(ttl=10800)
@retry_with_backoff(retries=5, backoff_in_seconds=3)
def fetch_stock_data(ticker):
    """Fetch comprehensive stock data including financials"""
    try:
        time.sleep(1.5)
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            return None, None, None, "Unable to fetch basic data"
        
        try:
            income_stmt = stock.income_stmt
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cash_flow
        except:
            income_stmt = pd.DataFrame()
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
        
        return info, income_stmt, balance_sheet, cash_flow
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            return None, None, None, "RATE_LIMIT"
        return None, None, None, str(e)[:100]

def calculate_fcf_from_financials(info, income_stmt, cash_flow):
    """Calculate Free Cash Flow from financial statements - Returns in chronological order"""
    fcf_data = {}
    
    try:
        if not cash_flow.empty:
            if 'Free Cash Flow' in cash_flow.index:
                fcf_row = cash_flow.loc['Free Cash Flow']
                for col in fcf_row.index[:4]:
                    year = col.year if hasattr(col, 'year') else str(col)[:4]
                    fcf_data[str(year)] = float(fcf_row[col]) if pd.notna(fcf_row[col]) else 0
            else:
                ocf_row = None
                capex_row = None
                
                for idx in ['Operating Cash Flow', 'Total Cash From Operating Activities', 'Cash Flow From Operating Activities']:
                    if idx in cash_flow.index:
                        ocf_row = cash_flow.loc[idx]
                        break
                
                for idx in ['Capital Expenditure', 'Capital Expenditures', 'Purchase Of PPE']:
                    if idx in cash_flow.index:
                        capex_row = cash_flow.loc[idx]
                        break
                
                if ocf_row is not None and capex_row is not None:
                    for col in ocf_row.index[:4]:
                        year = col.year if hasattr(col, 'year') else str(col)[:4]
                        ocf = float(ocf_row[col]) if pd.notna(ocf_row[col]) else 0
                        capex = float(capex_row[col]) if pd.notna(capex_row[col]) else 0
                        fcf_data[str(year)] = ocf + capex if capex < 0 else ocf - abs(capex)
    except Exception as e:
        pass
    
    if not fcf_data:
        operating_cf = info.get('operatingCashflow', 0) or 0
        capex = abs(info.get('capitalExpenditures', 0) or 0)
        if operating_cf > 0:
            fcf_data['TTM'] = operating_cf - capex
    
    # Sort by year in ASCENDING order (oldest first) - THIS IS THE FIX
    sorted_fcf = dict(sorted(fcf_data.items(), key=lambda x: x[0]))
    
    return sorted_fcf

def calculate_revenue_from_financials(income_stmt):
    """Get revenue data in chronological order"""
    revenue_data = {}
    try:
        if not income_stmt.empty:
            revenue_row = None
            for idx in ['Total Revenue', 'Revenue', 'Operating Revenue']:
                if idx in income_stmt.index:
                    revenue_row = income_stmt.loc[idx]
                    break
            
            if revenue_row is not None:
                for col in revenue_row.index[:4]:
                    year = col.year if hasattr(col, 'year') else str(col)[:4]
                    val = float(revenue_row[col]) if pd.notna(revenue_row[col]) else 0
                    if val > 0:
                        revenue_data[str(year)] = val
    except:
        pass
    
    # Sort ascending
    return dict(sorted(revenue_data.items(), key=lambda x: x[0]))

def calculate_ebitda_from_financials(income_stmt):
    """Get EBITDA data in chronological order"""
    ebitda_data = {}
    try:
        if not income_stmt.empty:
            ebitda_row = None
            for idx in ['EBITDA', 'Normalized EBITDA']:
                if idx in income_stmt.index:
                    ebitda_row = income_stmt.loc[idx]
                    break
            
            if ebitda_row is not None:
                for col in ebitda_row.index[:4]:
                    year = col.year if hasattr(col, 'year') else str(col)[:4]
                    val = float(ebitda_row[col]) if pd.notna(ebitda_row[col]) else 0
                    if val > 0:
                        ebitda_data[str(year)] = val
    except:
        pass
    
    return dict(sorted(ebitda_data.items(), key=lambda x: x[0]))

def calculate_wacc(info, risk_free_rate=0.07, market_premium=0.06):
    """Calculate Weighted Average Cost of Capital using CAPM"""
    sector = info.get('sector', 'Default')
    params = INDUSTRY_PARAMS.get(sector, INDUSTRY_PARAMS['Default'])
    
    # Beta from info or industry default
    beta = info.get('beta', params['beta']) or params['beta']
    beta = max(0.5, min(2.0, beta))
    
    # Cost of Equity using CAPM: Re = Rf + β × (Rm - Rf)
    cost_of_equity = risk_free_rate + beta * market_premium
    
    # Cost of Debt
    total_debt = info.get('totalDebt', 0) or 0
    interest_expense = info.get('interestExpense', 0) or 0
    
    if total_debt > 0 and interest_expense > 0:
        cost_of_debt = abs(interest_expense) / total_debt
    else:
        cost_of_debt = risk_free_rate + 0.02
    
    cost_of_debt = min(cost_of_debt, 0.15)
    
    # Tax rate
    tax_rate = params['tax_rate']
    
    # Capital structure weights
    market_cap = info.get('marketCap', 0) or 0
    
    if market_cap > 0 and total_debt > 0:
        total_value = market_cap + total_debt
        equity_weight = market_cap / total_value
        debt_weight = total_debt / total_value
    else:
        debt_equity = params['debt_equity']
        equity_weight = 1 / (1 + debt_equity)
        debt_weight = debt_equity / (1 + debt_equity)
    
    # WACC = (E/V × Re) + (D/V × Rd × (1-T))
    wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
    
    return {
        'wacc': wacc,
        'cost_of_equity': cost_of_equity,
        'cost_of_debt': cost_of_debt,
        'beta': beta,
        'equity_weight': equity_weight,
        'debt_weight': debt_weight,
        'tax_rate': tax_rate,
        'risk_free_rate': risk_free_rate,
        'market_premium': market_premium
    }

def project_fcf(base_fcf, growth_rates, years=5):
    """Project future Free Cash Flows"""
    projected = []
    current_fcf = base_fcf
    
    for i in range(years):
        if i < len(growth_rates):
            growth = growth_rates[i]
        else:
            growth = growth_rates[-1] if growth_rates else 0.05
        
        current_fcf = current_fcf * (1 + growth)
        projected.append({
            'year': i + 1,
            'fcf': current_fcf,
            'growth_rate': growth
        })
    
    return projected

def calculate_terminal_value_gordon(final_fcf, wacc, terminal_growth):
    """Terminal Value = FCF × (1 + g) / (WACC - g)"""
    if wacc <= terminal_growth:
        terminal_growth = wacc - 0.02
    return final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)

def calculate_terminal_value_exit_multiple(final_ebitda, exit_multiple):
    """Terminal Value = EBITDA × Exit Multiple"""
    return final_ebitda * exit_multiple

def calculate_dcf_value(projected_fcf, terminal_value, wacc, net_debt, shares_outstanding):
    """Calculate DCF-based fair value per share"""
    # Discount projected FCFs
    pv_fcfs = 0
    pv_fcf_breakdown = []
    
    for item in projected_fcf:
        discount_factor = (1 + wacc) ** item['year']
        pv = item['fcf'] / discount_factor
        pv_fcfs += pv
        pv_fcf_breakdown.append({
            'year': item['year'],
            'fcf': item['fcf'],
            'discount_factor': discount_factor,
            'pv': pv
        })
    
    # Discount terminal value
    final_year = len(projected_fcf)
    pv_terminal = terminal_value / ((1 + wacc) ** final_year)
    
    # Enterprise Value = PV of FCFs + PV of Terminal Value
    enterprise_value = pv_fcfs + pv_terminal
    
    # Equity Value = EV - Net Debt
    equity_value = enterprise_value - net_debt
    
    # Fair Value per Share
    if shares_outstanding > 0:
        fair_value = equity_value / shares_outstanding
    else:
        fair_value = 0
    
    return {
        'pv_fcfs': pv_fcfs,
        'pv_terminal': pv_terminal,
        'terminal_value': terminal_value,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'fair_value': max(0, fair_value),
        'pv_breakdown': pv_fcf_breakdown
    }

def run_sensitivity_analysis(base_fcf, growth_rates, wacc_base, terminal_growth_base, 
                             net_debt, shares, years=5):
    """Run sensitivity analysis on WACC vs Terminal Growth"""
    wacc_range = [wacc_base - 0.02, wacc_base - 0.01, wacc_base, wacc_base + 0.01, wacc_base + 0.02]
    growth_range = [terminal_growth_base - 0.01, terminal_growth_base - 0.005, 
                    terminal_growth_base, terminal_growth_base + 0.005, terminal_growth_base + 0.01]
    
    sensitivity_matrix = []
    
    for wacc in wacc_range:
        row = []
        for tg in growth_range:
            if wacc <= tg:
                row.append(0)
                continue
            projected = project_fcf(base_fcf, growth_rates, years)
            tv = calculate_terminal_value_gordon(projected[-1]['fcf'], wacc, tg)
            result = calculate_dcf_value(projected, tv, wacc, net_debt, shares)
            row.append(result['fair_value'])
        sensitivity_matrix.append(row)
    
    return {
        'matrix': sensitivity_matrix,
        'wacc_range': wacc_range,
        'growth_range': growth_range
    }

# ============================================
# ENHANCED VISUALIZATION FUNCTIONS
# ============================================
def create_fcf_projection_chart(historical_fcf, projected_fcf, current_year):
    """Create FCF projection chart - Historical in chronological order"""
    fig = go.Figure()
    
    # Historical FCF - Already sorted chronologically
    if historical_fcf:
        years = list(historical_fcf.keys())
        values = [v / 10000000 for v in historical_fcf.values()]
        
        fig.add_trace(go.Bar(
            x=years, 
            y=values,
            name='Historical FCF',
            marker=dict(
                color='#667eea',
                line=dict(color='#764ba2', width=2)
            ),
            text=[f'₹{v:,.1f} Cr' for v in values],
            textposition='outside',
            textfont=dict(color='white', size=11)
        ))
    
    # Projected FCF
    if projected_fcf:
        proj_years = [f'Year {p["year"]}' for p in projected_fcf]
        proj_values = [p['fcf'] / 10000000 for p in projected_fcf]
        
        fig.add_trace(go.Bar(
            x=proj_years, 
            y=proj_values,
            name='Projected FCF',
            marker=dict(
                color='#00b894',
                line=dict(color='#00cec9', width=2)
            ),
            text=[f'₹{v:,.1f} Cr' for v in proj_values],
            textposition='outside',
            textfont=dict(color='white', size=11)
        ))
    
    fig.update_layout(
        title=dict(
            text='<b>Free Cash Flow: Historical & Projected</b>',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        xaxis=dict(
            title='Period',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.05)',
            showgrid=False
        ),
        yaxis=dict(
            title='FCF (₹ Crores)',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=True,
            zerolinecolor='rgba(255,255,255,0.2)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        margin=dict(t=80, b=50, l=60, r=40),
        bargap=0.3
    )
    
    return fig

def create_valuation_waterfall(pv_fcfs, pv_terminal, net_debt, equity_value):
    """Create valuation waterfall chart"""
    fig = go.Figure(go.Waterfall(
        name="DCF Valuation",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["<b>PV of FCFs</b>", "<b>PV of Terminal Value</b>", "<b>Less: Net Debt</b>", "<b>Equity Value</b>"],
        y=[pv_fcfs / 10000000, pv_terminal / 10000000, -net_debt / 10000000, 0],
        text=[f'₹{pv_fcfs/10000000:,.0f} Cr', f'₹{pv_terminal/10000000:,.0f} Cr', 
              f'-₹{net_debt/10000000:,.0f} Cr', f'₹{equity_value/10000000:,.0f} Cr'],
        textposition="outside",
        textfont=dict(color='white', size=12),
        connector=dict(line=dict(color='rgba(255,255,255,0.3)', width=2)),
        increasing=dict(marker=dict(color='#00b894', line=dict(color='#00cec9', width=2))),
        decreasing=dict(marker=dict(color='#e17055', line=dict(color='#d63031', width=2))),
        totals=dict(marker=dict(color='#667eea', line=dict(color='#764ba2', width=2)))
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>DCF Valuation Waterfall</b>',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        xaxis=dict(tickfont=dict(color='white', size=11)),
        yaxis=dict(
            title='Value (₹ Crores)',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        showlegend=False,
        margin=dict(t=80, b=50, l=60, r=40)
    )
    
    return fig

def create_sensitivity_heatmap(sensitivity_data):
    """Create sensitivity analysis heatmap"""
    matrix = sensitivity_data['matrix']
    wacc_labels = [f'{w*100:.1f}%' for w in sensitivity_data['wacc_range']]
    growth_labels = [f'{g*100:.2f}%' for g in sensitivity_data['growth_range']]
    
    # Custom colorscale
    colorscale = [
        [0, '#d63031'],
        [0.25, '#e17055'],
        [0.5, '#fdcb6e'],
        [0.75, '#00cec9'],
        [1, '#00b894']
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=growth_labels,
        y=wacc_labels,
        colorscale=colorscale,
        text=[[f'₹{val:,.0f}' for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont=dict(size=13, color='white'),
        hoverongaps=False,
        showscale=True,
        colorbar=dict(
            title='Fair Value (₹)',
            titlefont=dict(color='white'),
            tickfont=dict(color='white')
        )
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Sensitivity Analysis: Fair Value</b><br><sup>WACC vs Terminal Growth Rate</sup>',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        xaxis=dict(
            title='Terminal Growth Rate',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            side='bottom'
        ),
        yaxis=dict(
            title='WACC (Discount Rate)',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(t=100, b=60, l=80, r=60)
    )
    
    return fig

def create_value_gauge(current_price, fair_value, upside):
    """Create gauge chart for fair value comparison"""
    # Determine color based on upside
    if upside > 20:
        gauge_color = '#00b894'
    elif upside > 0:
        gauge_color = '#00cec9'
    elif upside > -10:
        gauge_color = '#fdcb6e'
    else:
        gauge_color = '#e17055'
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fair_value,
        number=dict(
            prefix="₹",
            font=dict(size=50, color='white'),
            valueformat=",.2f"
        ),
        delta=dict(
            reference=current_price,
            relative=True,
            valueformat='.1%',
            increasing=dict(color='#00b894'),
            decreasing=dict(color='#e17055'),
            font=dict(size=20)
        ),
        title=dict(
            text="<b>DCF Fair Value</b>",
            font=dict(size=20, color='white')
        ),
        gauge=dict(
            axis=dict(
                range=[0, max(fair_value * 1.5, current_price * 1.5)],
                tickfont=dict(color='rgba(255,255,255,0.7)')
            ),
            bar=dict(color=gauge_color),
            bgcolor='rgba(255,255,255,0.05)',
            bordercolor='rgba(255,255,255,0.1)',
            steps=[
                dict(range=[0, current_price * 0.8], color='rgba(225, 112, 85, 0.3)'),
                dict(range=[current_price * 0.8, current_price], color='rgba(253, 203, 110, 0.3)'),
                dict(range=[current_price, current_price * 1.2], color='rgba(0, 206, 201, 0.3)'),
                dict(range=[current_price * 1.2, max(fair_value * 1.5, current_price * 1.5)], color='rgba(0, 184, 148, 0.3)')
            ],
            threshold=dict(
                line=dict(color='white', width=4),
                thickness=0.8,
                value=current_price
            )
        )
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(t=60, b=30, l=40, r=40),
        annotations=[
            dict(
                x=0.5, y=-0.12,
                xref='paper', yref='paper',
                text=f'<b>Current Price: ₹{current_price:,.2f}</b>',
                showarrow=False,
                font=dict(size=14, color='rgba(255,255,255,0.8)')
            )
        ]
    )
    
    return fig

def create_value_composition_donut(pv_fcfs, pv_terminal):
    """Create donut chart showing value composition"""
    total_ev = pv_fcfs + pv_terminal
    
    fig = go.Figure(data=[go.Pie(
        labels=['PV of FCFs<br>(Explicit Period)', 'PV of Terminal Value<br>(Perpetuity)'],
        values=[pv_fcfs, pv_terminal],
        hole=0.65,
        marker=dict(
            colors=['#667eea', '#00b894'],
            line=dict(color='rgba(255,255,255,0.2)', width=2)
        ),
        textinfo='percent',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>₹%{value:,.0f} Cr<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text='<b>Enterprise Value Composition</b>',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(color='white', size=11)
        ),
        annotations=[
            dict(
                text=f'<b>₹{total_ev/10000000:,.0f} Cr</b><br><span style="font-size:12px;color:rgba(255,255,255,0.6)">Enterprise Value</span>',
                x=0.5, y=0.5,
                font=dict(size=18, color='white'),
                showarrow=False
            )
        ],
        margin=dict(t=80, b=80, l=40, r=40)
    )
    
    return fig

def create_fcf_growth_chart(projected_fcf):
    """Create FCF growth rate chart"""
    years = [f'Year {p["year"]}' for p in projected_fcf]
    growth_rates = [p['growth_rate'] * 100 for p in projected_fcf]
    fcf_values = [p['fcf'] / 10000000 for p in projected_fcf]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # FCF bars
    fig.add_trace(
        go.Bar(
            x=years,
            y=fcf_values,
            name='FCF (₹ Cr)',
            marker=dict(color='#667eea', line=dict(color='#764ba2', width=2)),
            opacity=0.8
        ),
        secondary_y=False
    )
    
    # Growth rate line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=growth_rates,
            name='Growth Rate (%)',
            mode='lines+markers',
            line=dict(color='#00b894', width=3),
            marker=dict(size=10, color='#00b894', line=dict(color='white', width=2))
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(
            text='<b>Projected FCF & Growth Rates</b>',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        margin=dict(t=80, b=50, l=60, r=60)
    )
    
    fig.update_xaxes(tickfont=dict(color='white'), gridcolor='rgba(255,255,255,0.05)')
    fig.update_yaxes(
        title_text='FCF (₹ Crores)',
        titlefont=dict(color='rgba(255,255,255,0.7)'),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.1)',
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Growth Rate (%)',
        titlefont=dict(color='rgba(255,255,255,0.7)'),
        tickfont=dict(color='white'),
        gridcolor='rgba(255,255,255,0.05)',
        secondary_y=True
    )
    
    return fig

# ============================================
# PDF REPORT GENERATOR
# ============================================
def create_dcf_pdf_report(company, ticker, sector, dcf_results, wacc_data, assumptions):
    """Generate comprehensive DCF PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                  textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, 
                                     textColor=colors.grey, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, 
                                    textColor=colors.HexColor('#667eea'))
    
    story = []
    
    # Header
    story.append(Paragraph("NYZTrade DCF Valuation Report", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Professional Discounted Cash Flow Analysis", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Company Info
    story.append(Paragraph(f"<b>{company}</b>", styles['Heading2']))
    story.append(Paragraph(f"Ticker: {ticker} | Sector: {sector}", styles['Normal']))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Valuation Summary
    story.append(Paragraph("Valuation Summary", section_style))
    story.append(Spacer(1, 10))
    
    val_data = [
        ['Metric', 'Value'],
        ['DCF Fair Value', f"₹{dcf_results['fair_value']:,.2f}"],
        ['Current Price', f"₹{assumptions['current_price']:,.2f}"],
        ['Upside/Downside', f"{assumptions['upside']:+.1f}%"],
        ['Enterprise Value', f"₹{dcf_results['enterprise_value']/10000000:,.0f} Cr"],
        ['Equity Value', f"₹{dcf_results['equity_value']/10000000:,.0f} Cr"]
    ]
    
    val_table = Table(val_data, colWidths=[3*inch, 2.5*inch])
    val_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa'))
    ]))
    story.append(val_table)
    story.append(Spacer(1, 20))
    
    # Key Assumptions
    story.append(Paragraph("Key Assumptions", section_style))
    story.append(Spacer(1, 10))
    
    assumptions_data = [
        ['Parameter', 'Value'],
        ['WACC (Discount Rate)', f"{wacc_data['wacc']*100:.2f}%"],
        ['Cost of Equity (CAPM)', f"{wacc_data['cost_of_equity']*100:.2f}%"],
        ['Cost of Debt (After Tax)', f"{wacc_data['cost_of_debt']*(1-wacc_data['tax_rate'])*100:.2f}%"],
        ['Beta (β)', f"{wacc_data['beta']:.2f}"],
        ['Risk-Free Rate', f"{wacc_data['risk_free_rate']*100:.1f}%"],
        ['Terminal Growth Rate', f"{assumptions['terminal_growth']*100:.1f}%"],
        ['Projection Period', f"{assumptions['projection_years']} Years"]
    ]
    
    assump_table = Table(assumptions_data, colWidths=[3*inch, 2.5*inch])
    assump_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa'))
    ]))
    story.append(assump_table)
    story.append(Spacer(1, 20))
    
    # Value Breakdown
    story.append(Paragraph("Value Breakdown", section_style))
    story.append(Spacer(1, 10))
    
    total_ev = dcf_results['pv_fcfs'] + dcf_results['pv_terminal']
    breakdown_data = [
        ['Component', 'Value (₹ Cr)', '% of EV'],
        ['PV of FCFs (Explicit Period)', f"{dcf_results['pv_fcfs']/10000000:,.0f}", 
         f"{dcf_results['pv_fcfs']/total_ev*100:.1f}%"],
        ['PV of Terminal Value', f"{dcf_results['pv_terminal']/10000000:,.0f}",
         f"{dcf_results['pv_terminal']/total_ev*100:.1f}%"],
        ['Enterprise Value', f"{dcf_results['enterprise_value']/10000000:,.0f}", '100%'],
        ['Less: Net Debt', f"-{assumptions['net_debt']/10000000:,.0f}", '-'],
        ['Equity Value', f"{dcf_results['equity_value']/10000000:,.0f}", '-']
    ]
    
    breakdown_table = Table(breakdown_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa'))
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 30))
    
    # Disclaimer
    story.append(Paragraph("<b>DISCLAIMER</b>", styles['Heading3']))
    story.append(Paragraph(
        "This DCF valuation is for educational and informational purposes only. "
        "It is not intended as financial advice. The projections are based on assumptions "
        "that may not materialize. Past performance does not guarantee future results. "
        "Investors should conduct their own due diligence before making investment decisions. "
        "The fair value estimates are sensitive to input assumptions, particularly WACC and terminal growth rate.",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================
# MAIN APPLICATION
# ============================================

# Header
st.markdown('''
<div class="main-header">
    <h1>📊 DCF VALUATION MODEL</h1>
    <div class="subtitle">Professional Discounted Cash Flow Analysis | Real-Time Data</div>
</div>
''', unsafe_allow_html=True)

# Feature Cards
st.markdown('''
<div class="feature-grid">
    <div class="feature-card">
        <div class="icon">💰</div>
        <h3>Intrinsic Valuation</h3>
        <p>Calculate fair value using discounted future cash flows</p>
    </div>
    <div class="feature-card">
        <div class="icon">📈</div>
        <h3>Multi-Year Projections</h3>
        <p>5-10 year FCF forecasts with terminal value</p>
    </div>
    <div class="feature-card">
        <div class="icon">🎯</div>
        <h3>Sensitivity Analysis</h3>
        <p>Risk assessment across WACC & growth scenarios</p>
    </div>
</div>
''', unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Stock Selection")

# Stock universe
all_stocks = {}
for cat, stocks in POPULAR_STOCKS.items():
    all_stocks.update(stocks)

category = st.sidebar.selectbox("Category", ["All Stocks"] + list(POPULAR_STOCKS.keys()))
search = st.sidebar.text_input("🔍 Search", placeholder="Company or ticker...")

if search:
    filtered = {t: n for t, n in all_stocks.items() if search.upper() in t.upper() or search.upper() in n.upper()}
elif category == "All Stocks":
    filtered = all_stocks
else:
    filtered = POPULAR_STOCKS[category]

if filtered:
    options = [f"{n} ({t})" for t, n in filtered.items()]
    selected = st.sidebar.selectbox("Select Stock", options)
    ticker = selected.split("(")[1].strip(")")
else:
    ticker = None
    st.sidebar.warning("No stocks found")

custom = st.sidebar.text_input("Custom Ticker", placeholder="e.g., TATAMOTORS.NS")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ DCF Assumptions")

# Growth Assumptions
with st.sidebar.expander("📈 Growth Rates", expanded=True):
    st.caption("Annual FCF Growth Rates")
    growth_y1 = st.slider("Year 1", -20, 50, 15, format="%d%%") / 100
    growth_y2 = st.slider("Year 2", -20, 50, 12, format="%d%%") / 100
    growth_y3 = st.slider("Year 3", -20, 50, 10, format="%d%%") / 100
    growth_y4 = st.slider("Year 4", -20, 50, 8, format="%d%%") / 100
    growth_y5 = st.slider("Year 5", -20, 50, 6, format="%d%%") / 100
    growth_rates = [growth_y1, growth_y2, growth_y3, growth_y4, growth_y5]

# WACC Parameters
with st.sidebar.expander("💵 WACC Parameters"):
    risk_free_rate = st.slider("Risk-Free Rate (10Y Govt Bond)", 4.0, 10.0, 7.0, format="%.1f%%") / 100
    market_premium = st.slider("Equity Risk Premium", 3.0, 10.0, 6.0, format="%.1f%%") / 100
    custom_wacc = st.checkbox("Override with Custom WACC")
    if custom_wacc:
        manual_wacc = st.slider("Custom WACC", 8.0, 20.0, 12.0, format="%.1f%%") / 100

# Terminal Value
with st.sidebar.expander("🔮 Terminal Value"):
    terminal_method = st.radio("Calculation Method", ["Gordon Growth Model", "Exit Multiple"])
    if terminal_method == "Gordon Growth Model":
        terminal_growth = st.slider("Perpetual Growth Rate", 1.0, 5.0, 3.0, format="%.1f%%") / 100
        exit_multiple = None
        st.caption("💡 Should not exceed long-term GDP growth (~4-5%)")
    else:
        exit_multiple = st.slider("Exit EV/EBITDA Multiple", 5.0, 25.0, 12.0, format="%.1fx")
        terminal_growth = 0.03
        st.caption("💡 Based on industry comparable multiples")

# Projection Period
projection_years = st.sidebar.slider("📅 Projection Period", 3, 10, 5, format="%d Years")

# Extended projection for longer periods
if projection_years > 5:
    additional_years = projection_years - 5
    for i in range(additional_years):
        # Gradually decay growth towards terminal rate
        decay_growth = max(terminal_growth, growth_y5 * (0.9 ** (i + 1)))
        growth_rates.append(decay_growth)

st.sidebar.markdown("---")

# Analyze button
if st.sidebar.button("🚀 RUN DCF ANALYSIS", use_container_width=True, type="primary"):
    st.session_state.analyze = custom.upper() if custom else ticker

# ============================================
# MAIN ANALYSIS
# ============================================
if 'analyze' in st.session_state:
    t = st.session_state.analyze
    
    with st.spinner(f"📊 Fetching data for {t}..."):
        info, income_stmt, balance_sheet, cash_flow = fetch_stock_data(t)
    
    if isinstance(cash_flow, str):
        if cash_flow == "RATE_LIMIT":
            st.error("⏱️ **Rate Limit Reached**")
            st.warning("Yahoo Finance API limit hit. Please wait 3-5 minutes and try again.")
        else:
            st.error(f"Error: {cash_flow}")
        st.stop()
    
    if not info:
        st.error("❌ Failed to fetch data. Please try again.")
        st.stop()
    
    # Extract key data
    company = info.get('longName', t)
    sector = info.get('sector', 'Default')
    current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
    market_cap = info.get('marketCap', 0) or 0
    shares_outstanding = info.get('sharesOutstanding', 1)
    total_debt = info.get('totalDebt', 0) or 0
    total_cash = info.get('totalCash', 0) or 0
    net_debt = total_debt - total_cash
    ebitda = info.get('ebitda', 0) or 0
    
    # Get historical data in chronological order
    historical_fcf = calculate_fcf_from_financials(info, income_stmt, cash_flow)
    historical_revenue = calculate_revenue_from_financials(income_stmt)
    historical_ebitda = calculate_ebitda_from_financials(income_stmt)
    
    # Get base FCF (most recent year - last item in sorted dict)
    if historical_fcf:
        base_fcf = list(historical_fcf.values())[-1]  # Last value (most recent)
    else:
        operating_cf = info.get('operatingCashflow', 0) or 0
        capex = abs(info.get('capitalExpenditures', 0) or 0)
        base_fcf = operating_cf - capex
    
    if base_fcf <= 0:
        st.warning("⚠️ Negative or zero FCF detected. Using EBITDA-based estimation.")
        base_fcf = ebitda * 0.5 if ebitda > 0 else market_cap * 0.05
    
    # Calculate WACC
    if custom_wacc:
        wacc = manual_wacc
        wacc_data = {
            'wacc': wacc,
            'cost_of_equity': wacc,
            'cost_of_debt': wacc * 0.7,
            'beta': info.get('beta', 1.0) or 1.0,
            'equity_weight': 0.8,
            'debt_weight': 0.2,
            'tax_rate': 0.25,
            'risk_free_rate': risk_free_rate,
            'market_premium': market_premium
        }
    else:
        wacc_data = calculate_wacc(info, risk_free_rate, market_premium)
        wacc = wacc_data['wacc']
    
    # Project FCFs
    projected_fcf = project_fcf(base_fcf, growth_rates, projection_years)
    
    # Calculate Terminal Value
    if terminal_method == "Gordon Growth Model":
        tv = calculate_terminal_value_gordon(projected_fcf[-1]['fcf'], wacc, terminal_growth)
    else:
        final_year_ebitda = ebitda * np.prod([1 + g for g in growth_rates[:projection_years]])
        tv = calculate_terminal_value_exit_multiple(final_year_ebitda, exit_multiple)
    
    # Calculate DCF Value
    dcf_results = calculate_dcf_value(projected_fcf, tv, wacc, net_debt, shares_outstanding)
    fair_value = dcf_results['fair_value']
    upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
    
    # Sensitivity Analysis
    sensitivity = run_sensitivity_analysis(base_fcf, growth_rates, wacc, terminal_growth, 
                                           net_debt, shares_outstanding, projection_years)
    
    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    
    # Company Title
    st.markdown(f"## {company}")
    st.markdown(f"**{sector}** • `{t}` • Market Cap: ₹{market_cap/10000000:,.0f} Cr")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Main Value Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="dcf-hero">
            <h3>📊 DCF FAIR VALUE</h3>
            <div class="value">₹{fair_value:,.2f}</div>
            <div class="current">Current Market Price: ₹{current_price:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        upside_class = "upside-positive" if upside > 0 else "upside-negative"
        status_text = "UNDERVALUED" if upside > 0 else "OVERVALUED"
        potential_text = "Upside" if upside > 0 else "Downside"
        st.markdown(f'''
        <div class="upside-card {upside_class}">
            <h3>📈 {status_text}</h3>
            <div class="value">{upside:+.1f}%</div>
            <div class="label">Potential {potential_text}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Download PDF
    assumptions_dict = {
        'current_price': current_price,
        'upside': upside,
        'terminal_growth': terminal_growth,
        'projection_years': projection_years,
        'net_debt': net_debt
    }
    
    pdf = create_dcf_pdf_report(company, t, sector, dcf_results, wacc_data, assumptions_dict)
    
    st.download_button(
        "📥 Download DCF Report (PDF)",
        data=pdf,
        file_name=f"NYZTrade_DCF_{t}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Key Metrics Grid
    st.markdown("### 📊 Key Financial Metrics")
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    metrics_data = [
        ("Current Price", f"₹{current_price:,.2f}"),
        ("Market Cap", f"₹{market_cap/10000000:,.0f} Cr"),
        ("EBITDA (TTM)", f"₹{ebitda/10000000:,.0f} Cr" if ebitda else "N/A"),
        ("Net Debt", f"₹{net_debt/10000000:,.0f} Cr"),
        ("Base FCF", f"₹{base_fcf/10000000:,.1f} Cr"),
        ("WACC", f"{wacc*100:.2f}%")
    ]
    
    for col, (label, value) in zip([m1, m2, m3, m4, m5, m6], metrics_data):
        col.metric(label, value)
    
    # Recommendation Badge
    if upside > 40:
        rec_class, rec_title = "rec-strong-buy", "🚀 STRONG BUY"
    elif upside > 20:
        rec_class, rec_title = "rec-buy", "✅ BUY"
    elif upside > 0:
        rec_class, rec_title = "rec-buy", "📈 ACCUMULATE"
    elif upside > -15:
        rec_class, rec_title = "rec-hold", "⏸️ HOLD"
    else:
        rec_class, rec_title = "rec-avoid", "❌ AVOID"
    
    st.markdown(f'''
    <div class="rec-badge {rec_class}">
        <div class="title">{rec_title}</div>
        <div class="subtitle">DCF Implied Return: {upside:+.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ==========================================
    # CHARTS SECTION
    # ==========================================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 FCF Projection", 
        "💧 Valuation Waterfall", 
        "🎯 Sensitivity Analysis", 
        "🍩 Value Composition",
        "📋 Detailed Tables"
    ])
    
    with tab1:
        current_year = datetime.now().year
        fig = create_fcf_projection_chart(historical_fcf, projected_fcf, current_year)
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth chart
        fig2 = create_fcf_growth_chart(projected_fcf)
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        fig = create_valuation_waterfall(dcf_results['pv_fcfs'], dcf_results['pv_terminal'], 
                                         net_debt, dcf_results['equity_value'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Value breakdown info
        st.markdown('''
        <div class="info-card">
            <h4>📌 Understanding the Waterfall</h4>
            <p>
                <b>PV of FCFs:</b> Present value of projected free cash flows during explicit forecast period<br>
                <b>PV of Terminal Value:</b> Present value of cash flows beyond forecast period (perpetuity)<br>
                <b>Net Debt:</b> Total debt minus cash & equivalents, subtracted to get equity value
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    with tab3:
        fig = create_sensitivity_heatmap(sensitivity)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('''
        <div class="info-card">
            <h4>📌 How to Read Sensitivity Analysis</h4>
            <p>
                This matrix shows how fair value changes with different assumptions:<br>
                • <b>Rows:</b> WACC (discount rate) - higher WACC = lower value<br>
                • <b>Columns:</b> Terminal growth rate - higher growth = higher value<br>
                • <span style="color: #00b894;">Green cells</span> indicate higher valuations, 
                  <span style="color: #e17055;">red cells</span> indicate lower valuations
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_value_composition_donut(dcf_results['pv_fcfs'], dcf_results['pv_terminal'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_value_gauge(current_price, fair_value, upside)
            st.plotly_chart(fig, use_container_width=True)
        
        # TV contribution warning
        tv_pct = dcf_results['pv_terminal'] / (dcf_results['pv_fcfs'] + dcf_results['pv_terminal']) * 100
        if tv_pct > 75:
            st.warning(f"⚠️ Terminal Value contributes {tv_pct:.0f}% of Enterprise Value. DCF is highly sensitive to terminal assumptions.")
    
    with tab5:
        # FCF Projection Table
        st.markdown("#### 📋 Projected Free Cash Flows")
        
        fcf_df = pd.DataFrame([
            {
                'Year': f'Year {p["year"]}',
                'FCF (₹ Cr)': f'{p["fcf"]/10000000:,.1f}',
                'Growth Rate': f'{p["growth_rate"]*100:.1f}%',
                'Discount Factor': f'{1/(1+wacc)**p["year"]:.4f}',
                'PV of FCF (₹ Cr)': f'{(p["fcf"] / (1+wacc)**p["year"])/10000000:,.1f}'
            }
            for p in projected_fcf
        ])
        st.dataframe(fcf_df, use_container_width=True, hide_index=True)
        
        # Value Summary Table
        st.markdown("#### 💰 Valuation Summary")
        
        total_ev = dcf_results['pv_fcfs'] + dcf_results['pv_terminal']
        summary_df = pd.DataFrame({
            'Component': [
                'PV of FCFs (Explicit Period)',
                'PV of Terminal Value',
                'Enterprise Value',
                'Less: Net Debt',
                'Equity Value',
                'Shares Outstanding',
                'Fair Value per Share',
                'Current Market Price',
                'Upside/Downside'
            ],
            'Value': [
                f'₹{dcf_results["pv_fcfs"]/10000000:,.0f} Cr',
                f'₹{dcf_results["pv_terminal"]/10000000:,.0f} Cr',
                f'₹{total_ev/10000000:,.0f} Cr',
                f'-₹{net_debt/10000000:,.0f} Cr',
                f'₹{dcf_results["equity_value"]/10000000:,.0f} Cr',
                f'{shares_outstanding/10000000:,.2f} Cr',
                f'₹{fair_value:,.2f}',
                f'₹{current_price:,.2f}',
                f'{upside:+.1f}%'
            ],
            '% of EV': [
                f'{dcf_results["pv_fcfs"]/total_ev*100:.1f}%',
                f'{dcf_results["pv_terminal"]/total_ev*100:.1f}%',
                '100%',
                '-',
                '-',
                '-',
                '-',
                '-',
                '-'
            ]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ==========================================
    # WACC BREAKDOWN
    # ==========================================
    st.markdown("### 📐 WACC Calculation Details")
    
    wacc_col1, wacc_col2, wacc_col3, wacc_col4 = st.columns(4)
    
    with wacc_col1:
        st.markdown(f'''
        <div class="wacc-component">
            <div class="label">WACC</div>
            <div class="value">{wacc_data["wacc"]*100:.2f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with wacc_col2:
        st.markdown(f'''
        <div class="wacc-component">
            <div class="label">Cost of Equity</div>
            <div class="value">{wacc_data["cost_of_equity"]*100:.2f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with wacc_col3:
        st.markdown(f'''
        <div class="wacc-component">
            <div class="label">Cost of Debt (After Tax)</div>
            <div class="value">{wacc_data["cost_of_debt"]*(1-wacc_data["tax_rate"])*100:.2f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with wacc_col4:
        st.markdown(f'''
        <div class="wacc-component">
            <div class="label">Beta (β)</div>
            <div class="value">{wacc_data["beta"]:.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with st.expander("📚 WACC Formula & Methodology"):
        st.markdown("""
        **WACC Formula:**
        ```
        WACC = (E/V × Re) + (D/V × Rd × (1-T))
        ```
        
        **Where:**
        - E = Market value of equity
        - D = Market value of debt  
        - V = E + D (Total value)
        - Re = Cost of equity (from CAPM)
        - Rd = Cost of debt
        - T = Corporate tax rate
        
        **Cost of Equity (CAPM):**
        ```
        Re = Rf + β × (Rm - Rf)
        ```
        - Rf = Risk-free rate (10-year government bond yield)
        - β = Beta (measure of systematic risk)
        - (Rm - Rf) = Equity market risk premium
        
        **Terminal Value (Gordon Growth):**
        ```
        TV = FCFn × (1 + g) / (WACC - g)
        ```
        - FCFn = Free Cash Flow in final projected year
        - g = Perpetual growth rate (should not exceed GDP growth)
        """)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Company Fundamentals
    st.markdown("### 🏢 Company Fundamentals")
    
    fund_col1, fund_col2 = st.columns(2)
    
    with fund_col1:
        fundamentals_1 = pd.DataFrame({
            'Metric': ['P/E Ratio (TTM)', 'Forward P/E', 'PEG Ratio', 'Price to Book'],
            'Value': [
                f'{info.get("trailingPE", 0):.2f}x' if info.get("trailingPE") else 'N/A',
                f'{info.get("forwardPE", 0):.2f}x' if info.get("forwardPE") else 'N/A',
                f'{info.get("pegRatio", 0):.2f}' if info.get("pegRatio") else 'N/A',
                f'{info.get("priceToBook", 0):.2f}x' if info.get("priceToBook") else 'N/A'
            ]
        })
        st.dataframe(fundamentals_1, use_container_width=True, hide_index=True)
    
    with fund_col2:
        fundamentals_2 = pd.DataFrame({
            'Metric': ['EV/EBITDA', 'Profit Margin', 'ROE', 'Debt/Equity'],
            'Value': [
                f'{info.get("enterpriseToEbitda", 0):.2f}x' if info.get("enterpriseToEbitda") else 'N/A',
                f'{info.get("profitMargins", 0)*100:.1f}%' if info.get("profitMargins") else 'N/A',
                f'{info.get("returnOnEquity", 0)*100:.1f}%' if info.get("returnOnEquity") else 'N/A',
                f'{info.get("debtToEquity", 0):.2f}' if info.get("debtToEquity") else 'N/A'
            ]
        })
        st.dataframe(fundamentals_2, use_container_width=True, hide_index=True)

else:
    # Welcome screen
    st.markdown('''
    <div class="info-card">
        <h4>👈 Getting Started</h4>
        <p>Select a stock from the sidebar and click <b>RUN DCF ANALYSIS</b> to begin your valuation.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 What is DCF Valuation?
        
        **Discounted Cash Flow (DCF)** is an intrinsic valuation method that estimates a company's value based on its expected future cash flows.
        
        **The DCF Process:**
        1. **Forecast FCF** - Project free cash flows for 5-10 years
        2. **Calculate WACC** - Determine the discount rate
        3. **Estimate Terminal Value** - Value beyond forecast period
        4. **Discount to Present** - Apply time value of money
        5. **Calculate Fair Value** - Divide by shares outstanding
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 Key Features
        
        - ✅ **Real-time data** from Yahoo Finance
        - ✅ **CAPM-based WACC** calculation
        - ✅ **Gordon Growth & Exit Multiple** terminal value methods
        - ✅ **Interactive sensitivity analysis**
        - ✅ **Professional PDF reports**
        - ✅ **100+ Indian stocks** pre-loaded
        - ✅ **Customizable assumptions**
        """)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 📐 DCF Formula Reference
    
    ```
    Enterprise Value = Σ [FCFt / (1 + WACC)^t] + [Terminal Value / (1 + WACC)^n]
    
    Equity Value = Enterprise Value - Net Debt
    
    Fair Value per Share = Equity Value / Shares Outstanding
    ```
    
    **Terminal Value (Gordon Growth Model):**
    ```
    TV = FCFn × (1 + g) / (WACC - g)
    
    Where: g = perpetual growth rate (typically 2-4%)
    ```
    
    **Terminal Value (Exit Multiple):**
    ```
    TV = EBITDA (Final Year) × Exit Multiple
    ```
    """)

# Footer
st.markdown('''
<div class="footer">
    <p><b>NYZTrade DCF Valuation Platform</b> | Professional Analysis Tool</p>
    <p>⚠️ For educational purposes only. Not financial advice. Always conduct your own research.</p>
</div>
''', unsafe_allow_html=True)
