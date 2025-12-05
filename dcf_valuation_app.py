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
            .login-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 60px 40px;
                border-radius: 24px;
                text-align: center;
                margin-bottom: 40px;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
            }
            .login-header h1 { color: white; font-size: 2.8rem; margin: 0; font-weight: 700; }
            .login-header p { color: rgba(255,255,255,0.85); font-size: 1.1rem; margin-top: 10px; }
        </style>
        <div class="login-header">
            <h1>📊 NYZTrade DCF Pro</h1>
            <p>Professional Discounted Cash Flow Valuation</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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
# CUSTOM STYLES
# ============================================
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #0a0a0f 0%, #13131a 100%); }

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
.main-header h1 { color: #fff; font-size: 2.5rem; font-weight: 700; margin: 0; }
.main-header .subtitle { color: rgba(255,255,255,0.7); font-size: 1.1rem; margin-top: 8px; }

.dcf-hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px;
    border-radius: 24px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}
.dcf-hero h3 { color: rgba(255,255,255,0.9); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 10px 0; }
.dcf-hero .value { color: #fff; font-size: 3.5rem; font-weight: 700; margin: 0; }
.dcf-hero .current { color: rgba(255,255,255,0.75); font-size: 1.1rem; margin-top: 12px; }

.upside-card { padding: 35px; border-radius: 20px; text-align: center; }
.upside-positive { background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); box-shadow: 0 15px 40px rgba(0, 184, 148, 0.4); }
.upside-negative { background: linear-gradient(135deg, #e17055 0%, #d63031 100%); box-shadow: 0 15px 40px rgba(214, 48, 49, 0.4); }
.upside-card h3 { color: rgba(255,255,255,0.9); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 10px 0; }
.upside-card .value { color: #fff; font-size: 3rem; font-weight: 700; }
.upside-card .label { color: rgba(255,255,255,0.8); font-size: 1rem; margin-top: 8px; }

.rec-badge { padding: 30px; border-radius: 20px; text-align: center; font-weight: 700; }
.rec-strong-buy { background: linear-gradient(135deg, #00b894 0%, #55efc4 100%); box-shadow: 0 15px 40px rgba(0, 184, 148, 0.4); }
.rec-buy { background: linear-gradient(135deg, #00cec9 0%, #81ecec 100%); box-shadow: 0 15px 40px rgba(0, 206, 201, 0.4); }
.rec-hold { background: linear-gradient(135deg, #fdcb6e 0%, #ffeaa7 100%); color: #2d3436 !important; box-shadow: 0 15px 40px rgba(253, 203, 110, 0.4); }
.rec-avoid { background: linear-gradient(135deg, #e17055 0%, #fab1a0 100%); box-shadow: 0 15px 40px rgba(225, 112, 85, 0.4); }
.rec-badge .title { font-size: 1.8rem; color: #fff; margin-bottom: 8px; }
.rec-badge .subtitle { font-size: 1.1rem; color: rgba(255,255,255,0.85); }

.wacc-component {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin: 8px 0;
}
.wacc-component .label { color: rgba(255,255,255,0.6); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
.wacc-component .value { color: #667eea; font-size: 1.8rem; font-weight: 700; margin: 8px 0; }

.info-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 16px 0;
}
.info-card h4 { color: #667eea; margin: 0 0 10px 0; font-size: 1rem; }
.info-card p { color: rgba(255,255,255,0.7); margin: 0; font-size: 0.95rem; line-height: 1.6; }

.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); margin: 40px 0; }

.footer { text-align: center; padding: 40px; color: rgba(255,255,255,0.4); font-size: 0.9rem; }

.feature-grid { display: flex; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
.feature-card {
    flex: 1;
    min-width: 200px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 30px;
    text-align: center;
}
.feature-card .icon { font-size: 2.5rem; margin-bottom: 15px; }
.feature-card h3 { color: #fff; font-size: 1.1rem; margin: 0 0 10px 0; }
.feature-card p { color: rgba(255,255,255,0.6); font-size: 0.9rem; margin: 0; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# STOCK UNIVERSE - Investing.com Pro Style
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
        "ASTRAL.NS": "Astral Ltd", "SUPREMEIND.NS": "Supreme Industries", "APLAPOLLO.NS": "APL Apollo"
    },
    "🟡 Small Cap - High Growth": {
        "AMBER.NS": "Amber Enterprises", "AETHER.NS": "Aether Industries", "ANGELONE.NS": "Angel One",
        "CAMPUS.NS": "Campus Activewear", "DATAPATTNS.NS": "Data Patterns", "EASEMYTRIP.NS": "EaseMyTrip",
        "FIVESTAR.NS": "Five Star Business", "GLAND.NS": "Gland Pharma", "HAPPSTMNDS.NS": "Happiest Minds",
        "HOMEFIRST.NS": "Home First Finance", "INDIAMART.NS": "IndiaMART", "JUSTDIAL.NS": "Just Dial",
        "LATENTVIEW.NS": "LatentView Analytics", "NAZARA.NS": "Nazara Technologies"
    },
    "🏦 Banking & Finance": {
        "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "SBI",
        "KOTAKBANK.NS": "Kotak Bank", "AXISBANK.NS": "Axis Bank", "INDUSINDBK.NS": "IndusInd Bank",
        "BANDHANBNK.NS": "Bandhan Bank", "FEDERALBNK.NS": "Federal Bank", "AUBANK.NS": "AU Small Finance"
    },
    "💻 IT & Technology": {
        "TCS.NS": "TCS", "INFY.NS": "Infosys", "WIPRO.NS": "Wipro", "HCLTECH.NS": "HCL Tech",
        "TECHM.NS": "Tech Mahindra", "LTIM.NS": "LTIMindtree", "MPHASIS.NS": "Mphasis",
        "COFORGE.NS": "Coforge", "PERSISTENT.NS": "Persistent", "TATAELXSI.NS": "Tata Elxsi"
    },
    "💊 Pharma & Healthcare": {
        "SUNPHARMA.NS": "Sun Pharma", "DRREDDY.NS": "Dr Reddy's", "CIPLA.NS": "Cipla",
        "DIVISLAB.NS": "Divi's Labs", "AUROPHARMA.NS": "Aurobindo Pharma", "LUPIN.NS": "Lupin",
        "TORNTPHARM.NS": "Torrent Pharma", "ALKEM.NS": "Alkem Lab", "BIOCON.NS": "Biocon"
    }
}

# Industry parameters for WACC calculation (Investing.com Pro style)
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
    """Fetch comprehensive stock data"""
    try:
        time.sleep(1.5)
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            return None, None, None, "Unable to fetch data"
        
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
    """Calculate FCF - Returns in CHRONOLOGICAL order (oldest to newest)"""
    fcf_data = {}
    
    try:
        if cash_flow is not None and not cash_flow.empty:
            if 'Free Cash Flow' in cash_flow.index:
                fcf_row = cash_flow.loc['Free Cash Flow']
                for col in fcf_row.index[:4]:
                    year = col.year if hasattr(col, 'year') else str(col)[:4]
                    val = fcf_row[col]
                    if pd.notna(val):
                        fcf_data[str(year)] = float(val)
            else:
                ocf_row = None
                capex_row = None
                
                for idx in ['Operating Cash Flow', 'Total Cash From Operating Activities']:
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
    
    # Sort chronologically (oldest first)
    return dict(sorted(fcf_data.items(), key=lambda x: x[0]))

def calculate_wacc(info, risk_free_rate=0.07, market_premium=0.06):
    """WACC using CAPM (Investing.com Pro methodology)"""
    sector = info.get('sector', 'Default')
    params = INDUSTRY_PARAMS.get(sector, INDUSTRY_PARAMS['Default'])
    
    beta = info.get('beta', params['beta']) or params['beta']
    beta = max(0.5, min(2.0, beta))
    
    # Cost of Equity: Re = Rf + β × (Rm - Rf)
    cost_of_equity = risk_free_rate + beta * market_premium
    
    # Cost of Debt
    total_debt = info.get('totalDebt', 0) or 0
    interest_expense = info.get('interestExpense', 0) or 0
    
    if total_debt > 0 and interest_expense > 0:
        cost_of_debt = abs(interest_expense) / total_debt
    else:
        cost_of_debt = risk_free_rate + 0.02
    cost_of_debt = min(cost_of_debt, 0.15)
    
    tax_rate = params['tax_rate']
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
    """Project FCF for N years"""
    projected = []
    current_fcf = base_fcf
    
    for i in range(years):
        growth = growth_rates[i] if i < len(growth_rates) else growth_rates[-1]
        current_fcf = current_fcf * (1 + growth)
        projected.append({'year': i + 1, 'fcf': current_fcf, 'growth_rate': growth})
    
    return projected

def calculate_terminal_value_gordon(final_fcf, wacc, terminal_growth):
    """Gordon Growth: TV = FCF × (1+g) / (WACC - g)"""
    if wacc <= terminal_growth:
        terminal_growth = wacc - 0.02
    return final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)

def calculate_terminal_value_exit_multiple(final_ebitda, exit_multiple):
    """Exit Multiple: TV = EBITDA × Multiple"""
    return final_ebitda * exit_multiple

def calculate_dcf_value(projected_fcf, terminal_value, wacc, net_debt, shares_outstanding):
    """Calculate DCF fair value per share"""
    pv_fcfs = 0
    for item in projected_fcf:
        discount_factor = (1 + wacc) ** item['year']
        pv_fcfs += item['fcf'] / discount_factor
    
    final_year = len(projected_fcf)
    pv_terminal = terminal_value / ((1 + wacc) ** final_year)
    
    enterprise_value = pv_fcfs + pv_terminal
    equity_value = enterprise_value - net_debt
    
    fair_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
    
    return {
        'pv_fcfs': pv_fcfs,
        'pv_terminal': pv_terminal,
        'terminal_value': terminal_value,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'fair_value': max(0, fair_value)
    }

def run_sensitivity_analysis(base_fcf, growth_rates, wacc_base, terminal_growth_base, net_debt, shares, years=5):
    """Sensitivity matrix for WACC vs Terminal Growth"""
    wacc_range = [wacc_base - 0.02, wacc_base - 0.01, wacc_base, wacc_base + 0.01, wacc_base + 0.02]
    growth_range = [terminal_growth_base - 0.01, terminal_growth_base - 0.005, 
                    terminal_growth_base, terminal_growth_base + 0.005, terminal_growth_base + 0.01]
    
    matrix = []
    for w in wacc_range:
        row = []
        for g in growth_range:
            if w <= g:
                row.append(0)
            else:
                proj = project_fcf(base_fcf, growth_rates, years)
                tv = calculate_terminal_value_gordon(proj[-1]['fcf'], w, g)
                result = calculate_dcf_value(proj, tv, w, net_debt, shares)
                row.append(result['fair_value'])
        matrix.append(row)
    
    return {'matrix': matrix, 'wacc_range': wacc_range, 'growth_range': growth_range}

# ============================================
# CHART FUNCTIONS (FIXED)
# ============================================
def create_fcf_projection_chart(historical_fcf, projected_fcf):
    """FCF Bar Chart - Historical (chronological) + Projected"""
    fig = go.Figure()
    
    # Historical FCF (already sorted chronologically)
    if historical_fcf:
        years = list(historical_fcf.keys())
        values = [v / 10000000 for v in historical_fcf.values()]
        
        fig.add_trace(go.Bar(
            x=years, 
            y=values,
            name='Historical FCF',
            marker_color='#667eea',
            text=[f'₹{v:,.1f} Cr' for v in values],
            textposition='outside',
            textfont=dict(size=11, color='white')
        ))
    
    # Projected FCF
    if projected_fcf:
        proj_years = [f'Year {p["year"]}' for p in projected_fcf]
        proj_values = [p['fcf'] / 10000000 for p in projected_fcf]
        
        fig.add_trace(go.Bar(
            x=proj_years, 
            y=proj_values,
            name='Projected FCF',
            marker_color='#00b894',
            text=[f'₹{v:,.1f} Cr' for v in proj_values],
            textposition='outside',
            textfont=dict(size=11, color='white')
        ))
    
    fig.update_layout(
        title='Free Cash Flow: Historical & Projected',
        title_font=dict(size=18, color='white'),
        title_x=0.5,
        xaxis=dict(
            title='Period',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            showgrid=False
        ),
        yaxis=dict(
            title='FCF (₹ Crores)',
            titlefont=dict(color='rgba(255,255,255,0.7)'),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(color='white')),
        margin=dict(t=80, b=50, l=60, r=40),
        bargap=0.3
    )
    
    return fig

def create_valuation_waterfall(pv_fcfs, pv_terminal, net_debt, equity_value):
    """Valuation Waterfall Chart"""
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["PV of FCFs", "PV of Terminal Value", "Less: Net Debt", "Equity Value"],
        y=[pv_fcfs / 10000000, pv_terminal / 10000000, -net_debt / 10000000, 0],
        text=[f'₹{pv_fcfs/10000000:,.0f} Cr', f'₹{pv_terminal/10000000:,.0f} Cr', 
              f'-₹{net_debt/10000000:,.0f} Cr', f'₹{equity_value/10000000:,.0f} Cr'],
        textposition="outside",
        textfont=dict(color='white', size=12),
        connector=dict(line=dict(color='rgba(255,255,255,0.3)', width=2)),
        increasing=dict(marker=dict(color='#00b894')),
        decreasing=dict(marker=dict(color='#e17055')),
        totals=dict(marker=dict(color='#667eea'))
    ))
    
    fig.update_layout(
        title='DCF Valuation Waterfall',
        title_font=dict(size=18, color='white'),
        title_x=0.5,
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
    """Sensitivity Analysis Heatmap"""
    matrix = sensitivity_data['matrix']
    wacc_labels = [f'{w*100:.1f}%' for w in sensitivity_data['wacc_range']]
    growth_labels = [f'{g*100:.2f}%' for g in sensitivity_data['growth_range']]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=growth_labels,
        y=wacc_labels,
        colorscale=[[0, '#d63031'], [0.25, '#e17055'], [0.5, '#fdcb6e'], [0.75, '#00cec9'], [1, '#00b894']],
        text=[[f'₹{val:,.0f}' for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont=dict(size=12, color='white'),
        hoverongaps=False,
        colorbar=dict(title='Fair Value', titlefont=dict(color='white'), tickfont=dict(color='white'))
    ))
    
    fig.update_layout(
        title='Sensitivity Analysis: Fair Value (WACC vs Terminal Growth)',
        title_font=dict(size=18, color='white'),
        title_x=0.5,
        xaxis=dict(title='Terminal Growth Rate', titlefont=dict(color='rgba(255,255,255,0.7)'), tickfont=dict(color='white')),
        yaxis=dict(title='WACC', titlefont=dict(color='rgba(255,255,255,0.7)'), tickfont=dict(color='white')),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(t=80, b=60, l=80, r=60)
    )
    
    return fig

def create_value_gauge(current_price, fair_value, upside):
    """Fair Value Gauge Chart"""
    gauge_color = '#00b894' if upside > 0 else '#e17055'
    max_val = max(fair_value * 1.5, current_price * 1.5, 100)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fair_value,
        number=dict(prefix="₹", font=dict(size=40, color='white'), valueformat=",.2f"),
        delta=dict(reference=current_price, relative=True, valueformat='.1%',
                   increasing=dict(color='#00b894'), decreasing=dict(color='#e17055'), font=dict(size=18)),
        title=dict(text="DCF Fair Value", font=dict(size=18, color='white')),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(color='rgba(255,255,255,0.7)')),
            bar=dict(color=gauge_color),
            bgcolor='rgba(255,255,255,0.05)',
            steps=[
                dict(range=[0, current_price * 0.8], color='rgba(225, 112, 85, 0.3)'),
                dict(range=[current_price * 0.8, current_price], color='rgba(253, 203, 110, 0.3)'),
                dict(range=[current_price, current_price * 1.2], color='rgba(0, 206, 201, 0.3)'),
                dict(range=[current_price * 1.2, max_val], color='rgba(0, 184, 148, 0.3)')
            ],
            threshold=dict(line=dict(color='white', width=4), thickness=0.8, value=current_price)
        )
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(t=60, b=60, l=40, r=40)
    )
    
    fig.add_annotation(x=0.5, y=-0.15, xref='paper', yref='paper',
                       text=f'Current Price: ₹{current_price:,.2f}', showarrow=False,
                       font=dict(size=14, color='rgba(255,255,255,0.8)'))
    
    return fig

def create_value_composition_donut(pv_fcfs, pv_terminal):
    """Value Composition Donut Chart"""
    total_ev = pv_fcfs + pv_terminal
    
    fig = go.Figure(data=[go.Pie(
        labels=['PV of FCFs', 'PV of Terminal Value'],
        values=[pv_fcfs, pv_terminal],
        hole=0.65,
        marker=dict(colors=['#667eea', '#00b894']),
        textinfo='percent',
        textfont=dict(size=14, color='white')
    )])
    
    fig.update_layout(
        title='Enterprise Value Composition',
        title_font=dict(size=18, color='white'),
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        showlegend=True,
        legend=dict(orientation='h', y=-0.1, x=0.5, xanchor='center', font=dict(color='white', size=11)),
        margin=dict(t=80, b=80, l=40, r=40)
    )
    
    fig.add_annotation(text=f'₹{total_ev/10000000:,.0f} Cr', x=0.5, y=0.5,
                       font=dict(size=16, color='white'), showarrow=False)
    
    return fig

# ============================================
# PDF REPORT
# ============================================
def create_dcf_pdf_report(company, ticker, sector, dcf_results, wacc_data, assumptions):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                  textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, 
                                    textColor=colors.HexColor('#667eea'))
    
    story = []
    story.append(Paragraph("NYZTrade DCF Valuation Report", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>{company}</b>", styles['Heading2']))
    story.append(Paragraph(f"Ticker: {ticker} | Sector: {sector} | Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
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
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa'))
    ]))
    story.append(val_table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Key Assumptions", section_style))
    story.append(Spacer(1, 10))
    
    assump_data = [
        ['Parameter', 'Value'],
        ['WACC', f"{wacc_data['wacc']*100:.2f}%"],
        ['Cost of Equity', f"{wacc_data['cost_of_equity']*100:.2f}%"],
        ['Beta', f"{wacc_data['beta']:.2f}"],
        ['Terminal Growth', f"{assumptions['terminal_growth']*100:.1f}%"],
        ['Projection Years', f"{assumptions['projection_years']} Years"]
    ]
    
    assump_table = Table(assump_data, colWidths=[3*inch, 2.5*inch])
    assump_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa'))
    ]))
    story.append(assump_table)
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("<b>DISCLAIMER:</b> Educational purposes only. Not financial advice.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================
# MAIN APPLICATION
# ============================================

st.markdown('''
<div class="main-header">
    <h1>📊 DCF VALUATION MODEL</h1>
    <div class="subtitle">5-Year Growth + Exit Multiple | Investing.com Pro Methodology</div>
</div>
''', unsafe_allow_html=True)

st.markdown('''
<div class="feature-grid">
    <div class="feature-card">
        <div class="icon">💰</div>
        <h3>Intrinsic Valuation</h3>
        <p>DCF with CAPM-based WACC</p>
    </div>
    <div class="feature-card">
        <div class="icon">📈</div>
        <h3>5-Year Projections</h3>
        <p>FCF forecasts + Terminal Value</p>
    </div>
    <div class="feature-card">
        <div class="icon">🎯</div>
        <h3>Sensitivity Analysis</h3>
        <p>WACC vs Growth scenarios</p>
    </div>
</div>
''', unsafe_allow_html=True)

# Sidebar
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Stock Selection")

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

# Growth Rates (Investing.com Pro style - 5 years)
with st.sidebar.expander("📈 5-Year Growth Rates", expanded=True):
    st.caption("Annual FCF Growth (%)")
    g1 = st.slider("Year 1", -20, 50, 15, format="%d%%") / 100
    g2 = st.slider("Year 2", -20, 50, 12, format="%d%%") / 100
    g3 = st.slider("Year 3", -20, 50, 10, format="%d%%") / 100
    g4 = st.slider("Year 4", -20, 50, 8, format="%d%%") / 100
    g5 = st.slider("Year 5", -20, 50, 6, format="%d%%") / 100
    growth_rates = [g1, g2, g3, g4, g5]

# WACC
with st.sidebar.expander("💵 WACC Parameters"):
    risk_free_rate = st.slider("Risk-Free Rate", 4.0, 10.0, 7.0, format="%.1f%%") / 100
    market_premium = st.slider("Equity Risk Premium", 3.0, 10.0, 6.0, format="%.1f%%") / 100
    use_custom_wacc = st.checkbox("Override WACC")
    manual_wacc = st.slider("Custom WACC", 8.0, 20.0, 12.0, format="%.1f%%") / 100 if use_custom_wacc else None

# Terminal Value (Investing.com Pro: Gordon Growth OR Exit Multiple)
with st.sidebar.expander("🔮 Terminal Value"):
    tv_method = st.radio("Method", ["Gordon Growth Model", "Exit Multiple (EV/EBITDA)"])
    if tv_method == "Gordon Growth Model":
        terminal_growth = st.slider("Perpetual Growth", 1.0, 5.0, 3.0, format="%.1f%%") / 100
        exit_multiple = None
    else:
        exit_multiple = st.slider("Exit EV/EBITDA Multiple", 5.0, 25.0, 10.0, format="%.1fx")
        terminal_growth = 0.03

projection_years = 5  # Fixed 5-year projection like Investing.com Pro

st.sidebar.markdown("---")

if st.sidebar.button("🚀 RUN DCF ANALYSIS", use_container_width=True, type="primary"):
    st.session_state.analyze = custom.upper() if custom else ticker

# ============================================
# MAIN ANALYSIS
# ============================================
if 'analyze' in st.session_state:
    t = st.session_state.analyze
    
    with st.spinner(f"📊 Analyzing {t}..."):
        info, income_stmt, balance_sheet, cash_flow = fetch_stock_data(t)
    
    if isinstance(cash_flow, str):
        if cash_flow == "RATE_LIMIT":
            st.error("⏱️ Rate limit reached. Wait 3-5 minutes.")
        else:
            st.error(f"Error: {cash_flow}")
        st.stop()
    
    if not info:
        st.error("❌ Failed to fetch data")
        st.stop()
    
    # Extract data
    company = info.get('longName', t)
    sector = info.get('sector', 'Default')
    current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
    market_cap = info.get('marketCap', 0) or 0
    shares = info.get('sharesOutstanding', 1)
    total_debt = info.get('totalDebt', 0) or 0
    total_cash = info.get('totalCash', 0) or 0
    net_debt = total_debt - total_cash
    ebitda = info.get('ebitda', 0) or 0
    
    # Historical FCF (chronological)
    historical_fcf = calculate_fcf_from_financials(info, income_stmt, cash_flow)
    
    # Base FCF (most recent)
    if historical_fcf:
        base_fcf = list(historical_fcf.values())[-1]
    else:
        base_fcf = (info.get('operatingCashflow', 0) or 0) - abs(info.get('capitalExpenditures', 0) or 0)
    
    if base_fcf <= 0:
        st.warning("⚠️ Negative FCF. Using EBITDA estimate.")
        base_fcf = ebitda * 0.5 if ebitda > 0 else market_cap * 0.05
    
    # WACC
    if use_custom_wacc and manual_wacc:
        wacc = manual_wacc
        wacc_data = {'wacc': wacc, 'cost_of_equity': wacc, 'cost_of_debt': wacc*0.7, 
                     'beta': info.get('beta', 1.0) or 1.0, 'equity_weight': 0.8, 'debt_weight': 0.2,
                     'tax_rate': 0.25, 'risk_free_rate': risk_free_rate, 'market_premium': market_premium}
    else:
        wacc_data = calculate_wacc(info, risk_free_rate, market_premium)
        wacc = wacc_data['wacc']
    
    # Project FCF
    projected_fcf = project_fcf(base_fcf, growth_rates, projection_years)
    
    # Terminal Value
    if tv_method == "Gordon Growth Model":
        tv = calculate_terminal_value_gordon(projected_fcf[-1]['fcf'], wacc, terminal_growth)
    else:
        final_ebitda = ebitda * np.prod([1 + g for g in growth_rates])
        tv = calculate_terminal_value_exit_multiple(final_ebitda, exit_multiple)
    
    # DCF Value
    dcf_results = calculate_dcf_value(projected_fcf, tv, wacc, net_debt, shares)
    fair_value = dcf_results['fair_value']
    upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
    
    # Sensitivity
    sensitivity = run_sensitivity_analysis(base_fcf, growth_rates, wacc, terminal_growth, net_debt, shares)
    
    # ==================== DISPLAY ====================
    st.markdown(f"## {company}")
    st.markdown(f"**{sector}** • `{t}` • Market Cap: ₹{market_cap/10000000:,.0f} Cr")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="dcf-hero">
            <h3>📊 DCF FAIR VALUE</h3>
            <div class="value">₹{fair_value:,.2f}</div>
            <div class="current">Current Price: ₹{current_price:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        cls = "upside-positive" if upside > 0 else "upside-negative"
        status = "UNDERVALUED" if upside > 0 else "OVERVALUED"
        st.markdown(f'''
        <div class="upside-card {cls}">
            <h3>📈 {status}</h3>
            <div class="value">{upside:+.1f}%</div>
            <div class="label">Potential {"Upside" if upside > 0 else "Downside"}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # PDF Download
    assumptions_dict = {'current_price': current_price, 'upside': upside, 'terminal_growth': terminal_growth,
                        'projection_years': projection_years, 'net_debt': net_debt}
    pdf = create_dcf_pdf_report(company, t, sector, dcf_results, wacc_data, assumptions_dict)
    st.download_button("📥 Download PDF Report", data=pdf, 
                       file_name=f"DCF_{t}_{datetime.now().strftime('%Y%m%d')}.pdf",
                       mime="application/pdf", use_container_width=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Metrics
    st.markdown("### 📊 Key Metrics")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Price", f"₹{current_price:,.2f}")
    m2.metric("Market Cap", f"₹{market_cap/10000000:,.0f} Cr")
    m3.metric("EBITDA", f"₹{ebitda/10000000:,.0f} Cr" if ebitda else "N/A")
    m4.metric("Net Debt", f"₹{net_debt/10000000:,.0f} Cr")
    m5.metric("Base FCF", f"₹{base_fcf/10000000:,.1f} Cr")
    m6.metric("WACC", f"{wacc*100:.2f}%")
    
    # Recommendation
    if upside > 40:
        rec_cls, rec_txt = "rec-strong-buy", "🚀 STRONG BUY"
    elif upside > 20:
        rec_cls, rec_txt = "rec-buy", "✅ BUY"
    elif upside > 0:
        rec_cls, rec_txt = "rec-buy", "📈 ACCUMULATE"
    elif upside > -15:
        rec_cls, rec_txt = "rec-hold", "⏸️ HOLD"
    else:
        rec_cls, rec_txt = "rec-avoid", "❌ AVOID"
    
    st.markdown(f'''
    <div class="rec-badge {rec_cls}">
        <div class="title">{rec_txt}</div>
        <div class="subtitle">DCF Implied Return: {upside:+.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Charts
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 FCF Projection", "💧 Waterfall", "🎯 Sensitivity", "🍩 Composition", "📋 Tables"])
    
    with tab1:
        fig = create_fcf_projection_chart(historical_fcf, projected_fcf)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_valuation_waterfall(dcf_results['pv_fcfs'], dcf_results['pv_terminal'], net_debt, dcf_results['equity_value'])
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = create_sensitivity_heatmap(sensitivity)
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Green = Higher value, Red = Lower value. Rows: WACC, Columns: Terminal Growth")
    
    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            fig = create_value_composition_donut(dcf_results['pv_fcfs'], dcf_results['pv_terminal'])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = create_value_gauge(current_price, fair_value, upside)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        st.markdown("#### Projected FCF")
        fcf_df = pd.DataFrame([{
            'Year': f'Year {p["year"]}',
            'FCF (₹ Cr)': f'{p["fcf"]/10000000:,.1f}',
            'Growth': f'{p["growth_rate"]*100:.1f}%',
            'PV (₹ Cr)': f'{(p["fcf"]/(1+wacc)**p["year"])/10000000:,.1f}'
        } for p in projected_fcf])
        st.dataframe(fcf_df, use_container_width=True, hide_index=True)
        
        st.markdown("#### Valuation Summary")
        total_ev = dcf_results['pv_fcfs'] + dcf_results['pv_terminal']
        summary = pd.DataFrame({
            'Component': ['PV of FCFs', 'PV of Terminal Value', 'Enterprise Value', 'Net Debt', 'Equity Value', 'Fair Value/Share'],
            'Value': [f"₹{dcf_results['pv_fcfs']/10000000:,.0f} Cr", f"₹{dcf_results['pv_terminal']/10000000:,.0f} Cr",
                      f"₹{total_ev/10000000:,.0f} Cr", f"₹{net_debt/10000000:,.0f} Cr",
                      f"₹{dcf_results['equity_value']/10000000:,.0f} Cr", f"₹{fair_value:,.2f}"]
        })
        st.dataframe(summary, use_container_width=True, hide_index=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # WACC Details
    st.markdown("### 📐 WACC Breakdown")
    w1, w2, w3, w4 = st.columns(4)
    
    for col, (label, val) in zip([w1, w2, w3, w4], [
        ("WACC", f"{wacc_data['wacc']*100:.2f}%"),
        ("Cost of Equity", f"{wacc_data['cost_of_equity']*100:.2f}%"),
        ("Cost of Debt", f"{wacc_data['cost_of_debt']*(1-wacc_data['tax_rate'])*100:.2f}%"),
        ("Beta (β)", f"{wacc_data['beta']:.2f}")
    ]):
        col.markdown(f'''
        <div class="wacc-component">
            <div class="label">{label}</div>
            <div class="value">{val}</div>
        </div>
        ''', unsafe_allow_html=True)

else:
    st.markdown('''
    <div class="info-card">
        <h4>👈 Getting Started</h4>
        <p>Select a stock and click <b>RUN DCF ANALYSIS</b> to calculate intrinsic value using the Investing.com Pro methodology.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📐 Investing.com Pro DCF Methodology
    
    This model follows the **5-Year Growth + Exit Multiple** approach:
    
    1. **Forecast FCF** for 5 years using custom growth rates
    2. **Calculate WACC** using CAPM (Cost of Equity) + Cost of Debt
    3. **Terminal Value** via Gordon Growth or Exit Multiple (EV/EBITDA)
    4. **Discount** all cash flows to present value
    5. **Subtract Net Debt** to get Equity Value
    
    **Formulas:**
    ```
    WACC = (E/V × Re) + (D/V × Rd × (1-T))
    Cost of Equity (CAPM) = Rf + β × (Rm - Rf)
    Terminal Value (Gordon) = FCF₅ × (1+g) / (WACC - g)
    Terminal Value (Exit) = EBITDA₅ × Exit Multiple
    ```
    """)

st.markdown('''
<div class="footer">
    <p><b>NYZTrade DCF Pro</b> | Investing.com Pro Methodology</p>
    <p>⚠️ Educational purposes only. Not financial advice.</p>
</div>
''', unsafe_allow_html=True)
