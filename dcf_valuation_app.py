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

st.set_page_config(page_title="NYZTrade DCF Valuation", page_icon="📊", layout="wide")

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
        <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); 
             padding: 3rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;
             box-shadow: 0 20px 60px rgba(0,0,0,0.3);'>
            <h1 style='color: #e94560; font-size: 3rem; margin-bottom: 0.5rem;'>📊 NYZTrade DCF Pro</h1>
            <p style='color: #a0a0a0; font-size: 1.2rem;'>Discounted Cash Flow Valuation Model</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.button("Login", on_click=password_entered, use_container_width=True)
            st.info("Demo: demo/demo123 | Premium: premium/niyas123")
        return False
    elif not st.session_state["password_correct"]:
        st.error("❌ Incorrect credentials")
        return False
    return True

if not check_password():
    st.stop()

# ============================================
# CUSTOM STYLES
# ============================================
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2.5rem;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}
.main-header h1 { color: #e94560; margin-bottom: 0.5rem; }
.main-header p { color: #a0a0a0; }

.dcf-value-box {
    background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%);
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    color: white;
    margin: 1.5rem 0;
    box-shadow: 0 10px 30px rgba(0, 180, 216, 0.3);
}

.upside-positive {
    background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    color: white;
    font-size: 1.5rem;
    font-weight: bold;
}

.upside-negative {
    background: linear-gradient(135deg, #ef476f 0%, #d62828 100%);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    color: white;
    font-size: 1.5rem;
    font-weight: bold;
}

.metric-card {
    background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    color: white;
    margin: 0.5rem 0;
}

.rec-strong-buy {
    background: linear-gradient(135deg, #00C853 0%, #64DD17 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    font-size: 2rem;
    font-weight: bold;
}
.rec-buy {
    background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    font-size: 2rem;
    font-weight: bold;
}
.rec-hold {
    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    font-size: 2rem;
    font-weight: bold;
}
.rec-avoid {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    font-size: 2rem;
    font-weight: bold;
}

.assumption-box {
    background: #1e1e2e;
    border: 1px solid #444;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
}

.fcf-table {
    background: #1a1a2e;
    border-radius: 10px;
    padding: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# STOCK UNIVERSE
# ============================================
POPULAR_STOCKS = {
    "Large Cap - Nifty 50": {
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
    "Mid Cap - Growth": {
        "JINDALSTEL.NS": "Jindal Steel", "TRENT.NS": "Trent", "PERSISTENT.NS": "Persistent Systems",
        "PIIND.NS": "PI Industries", "DIXON.NS": "Dixon Technologies", "VOLTAS.NS": "Voltas",
        "MPHASIS.NS": "Mphasis", "COFORGE.NS": "Coforge", "LTIM.NS": "LTIMindtree",
        "AUROPHARMA.NS": "Aurobindo Pharma", "TORNTPHARM.NS": "Torrent Pharma", "ALKEM.NS": "Alkem Lab",
        "POLYCAB.NS": "Polycab India", "HAVELLS.NS": "Havells India", "CROMPTON.NS": "Crompton Greaves",
        "ASTRAL.NS": "Astral Ltd", "SUPREMEIND.NS": "Supreme Industries", "APLAPOLLO.NS": "APL Apollo",
        "SYNGENE.NS": "Syngene International", "LALPATHLAB.NS": "Dr Lal PathLabs"
    },
    "Small Cap - High Growth": {
        "AMBER.NS": "Amber Enterprises", "AETHER.NS": "Aether Industries", "ANGELONE.NS": "Angel One",
        "CAMPUS.NS": "Campus Activewear", "DATAPATTNS.NS": "Data Patterns", "EASEMYTRIP.NS": "EaseMyTrip",
        "FIVESTAR.NS": "Five Star Business", "GLAND.NS": "Gland Pharma", "HAPPSTMNDS.NS": "Happiest Minds",
        "HOMEFIRST.NS": "Home First Finance", "INDIAMART.NS": "IndiaMART", "JUSTDIAL.NS": "Just Dial",
        "KAYNES.NS": "Kaynes Technology", "LATENTVIEW.NS": "LatentView Analytics", "MEDPLUS.NS": "MedPlus Health",
        "NAZARA.NS": "Nazara Technologies", "OLECTRA.NS": "Olectra Greentech", "PATANJALI.NS": "Patanjali Foods",
        "ROUTE.NS": "Route Mobile", "SOLARINDS.NS": "Solar Industries"
    },
    "Sectoral - Banking": {
        "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "SBI",
        "KOTAKBANK.NS": "Kotak Bank", "AXISBANK.NS": "Axis Bank", "INDUSINDBK.NS": "IndusInd Bank",
        "BANDHANBNK.NS": "Bandhan Bank", "FEDERALBNK.NS": "Federal Bank", "IDFCFIRSTB.NS": "IDFC First",
        "RBLBANK.NS": "RBL Bank", "AUBANK.NS": "AU Small Finance", "EQUITASBNK.NS": "Equitas SFB"
    },
    "Sectoral - IT": {
        "TCS.NS": "TCS", "INFY.NS": "Infosys", "WIPRO.NS": "Wipro", "HCLTECH.NS": "HCL Tech",
        "TECHM.NS": "Tech Mahindra", "LTIM.NS": "LTIMindtree", "MPHASIS.NS": "Mphasis",
        "COFORGE.NS": "Coforge", "PERSISTENT.NS": "Persistent", "LTTS.NS": "L&T Technology",
        "CYIENT.NS": "Cyient", "TATAELXSI.NS": "Tata Elxsi", "KPITTECH.NS": "KPIT Tech"
    },
    "Sectoral - Pharma": {
        "SUNPHARMA.NS": "Sun Pharma", "DRREDDY.NS": "Dr Reddy's", "CIPLA.NS": "Cipla",
        "DIVISLAB.NS": "Divi's Labs", "AUROPHARMA.NS": "Aurobindo Pharma", "LUPIN.NS": "Lupin",
        "TORNTPHARM.NS": "Torrent Pharma", "ALKEM.NS": "Alkem Lab", "BIOCON.NS": "Biocon",
        "GLENMARK.NS": "Glenmark", "IPCALAB.NS": "IPCA Labs", "LAURUSLABS.NS": "Laurus Labs"
    }
}

# Industry-specific parameters for WACC estimation
INDUSTRY_PARAMS = {
    'Technology': {'beta': 1.15, 'debt_equity': 0.1, 'tax_rate': 0.25, 'terminal_growth': 0.04},
    'Financial Services': {'beta': 1.0, 'debt_equity': 0.8, 'tax_rate': 0.25, 'terminal_growth': 0.035},
    'Consumer Cyclical': {'beta': 1.2, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.04},
    'Consumer Defensive': {'beta': 0.7, 'debt_equity': 0.3, 'tax_rate': 0.25, 'terminal_growth': 0.03},
    'Healthcare': {'beta': 0.9, 'debt_equity': 0.2, 'tax_rate': 0.25, 'terminal_growth': 0.04},
    'Industrials': {'beta': 1.1, 'debt_equity': 0.5, 'tax_rate': 0.25, 'terminal_growth': 0.035},
    'Energy': {'beta': 1.3, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.02},
    'Basic Materials': {'beta': 1.25, 'debt_equity': 0.35, 'tax_rate': 0.25, 'terminal_growth': 0.025},
    'Real Estate': {'beta': 0.9, 'debt_equity': 0.7, 'tax_rate': 0.25, 'terminal_growth': 0.03},
    'Utilities': {'beta': 0.6, 'debt_equity': 0.8, 'tax_rate': 0.25, 'terminal_growth': 0.025},
    'Communication Services': {'beta': 1.0, 'debt_equity': 0.5, 'tax_rate': 0.25, 'terminal_growth': 0.035},
    'Default': {'beta': 1.0, 'debt_equity': 0.4, 'tax_rate': 0.25, 'terminal_growth': 0.03}
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
        
        # Fetch financial statements
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
    """Calculate Free Cash Flow from financial statements"""
    fcf_data = {}
    
    try:
        # Try to get FCF directly from cash flow statement
        if not cash_flow.empty:
            if 'Free Cash Flow' in cash_flow.index:
                fcf_row = cash_flow.loc['Free Cash Flow']
                for col in fcf_row.index[:4]:  # Last 4 years
                    year = col.year if hasattr(col, 'year') else str(col)[:4]
                    fcf_data[str(year)] = float(fcf_row[col]) if pd.notna(fcf_row[col]) else 0
            else:
                # Calculate FCF = Operating Cash Flow - CapEx
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
                        # CapEx is usually negative, so we add it
                        fcf_data[str(year)] = ocf + capex if capex < 0 else ocf - abs(capex)
    except Exception as e:
        pass
    
    # Fallback: Use info-based FCF estimation
    if not fcf_data:
        operating_cf = info.get('operatingCashflow', 0) or 0
        capex = abs(info.get('capitalExpenditures', 0) or 0)
        if operating_cf > 0:
            fcf_data['TTM'] = operating_cf - capex
    
    return fcf_data

def calculate_revenue_growth(income_stmt):
    """Calculate historical revenue growth rates"""
    growth_rates = []
    try:
        if not income_stmt.empty:
            revenue_row = None
            for idx in ['Total Revenue', 'Revenue', 'Operating Revenue']:
                if idx in income_stmt.index:
                    revenue_row = income_stmt.loc[idx]
                    break
            
            if revenue_row is not None:
                revenues = [float(v) for v in revenue_row.values[:4] if pd.notna(v) and float(v) > 0]
                if len(revenues) >= 2:
                    for i in range(len(revenues) - 1):
                        if revenues[i+1] > 0:
                            growth = (revenues[i] - revenues[i+1]) / revenues[i+1] * 100
                            growth_rates.append(growth)
    except:
        pass
    return growth_rates

def calculate_wacc(info, risk_free_rate=0.07, market_premium=0.06):
    """Calculate Weighted Average Cost of Capital"""
    sector = info.get('sector', 'Default')
    params = INDUSTRY_PARAMS.get(sector, INDUSTRY_PARAMS['Default'])
    
    # Get beta from info or use industry default
    beta = info.get('beta', params['beta']) or params['beta']
    beta = max(0.5, min(2.0, beta))  # Constrain beta between 0.5 and 2.0
    
    # Cost of Equity using CAPM
    cost_of_equity = risk_free_rate + beta * market_premium
    
    # Cost of Debt (approximate from interest expense)
    total_debt = info.get('totalDebt', 0) or 0
    interest_expense = info.get('interestExpense', 0) or 0
    
    if total_debt > 0 and interest_expense > 0:
        cost_of_debt = abs(interest_expense) / total_debt
    else:
        cost_of_debt = risk_free_rate + 0.02  # Risk-free + 2% spread
    
    cost_of_debt = min(cost_of_debt, 0.15)  # Cap at 15%
    
    # Tax rate
    tax_rate = params['tax_rate']
    
    # Capital structure
    market_cap = info.get('marketCap', 0) or 0
    
    if market_cap > 0 and total_debt > 0:
        total_value = market_cap + total_debt
        equity_weight = market_cap / total_value
        debt_weight = total_debt / total_value
    else:
        debt_equity = params['debt_equity']
        equity_weight = 1 / (1 + debt_equity)
        debt_weight = debt_equity / (1 + debt_equity)
    
    # Calculate WACC
    wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
    
    return {
        'wacc': wacc,
        'cost_of_equity': cost_of_equity,
        'cost_of_debt': cost_of_debt,
        'beta': beta,
        'equity_weight': equity_weight,
        'debt_weight': debt_weight,
        'tax_rate': tax_rate
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
    """Calculate Terminal Value using Gordon Growth Model"""
    if wacc <= terminal_growth:
        terminal_growth = wacc - 0.02  # Ensure WACC > g
    return final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)

def calculate_terminal_value_exit_multiple(final_ebitda, exit_multiple):
    """Calculate Terminal Value using Exit Multiple Method"""
    return final_ebitda * exit_multiple

def calculate_dcf_value(projected_fcf, terminal_value, wacc, net_debt, shares_outstanding):
    """Calculate DCF-based fair value per share"""
    # Discount projected FCFs
    pv_fcfs = 0
    for item in projected_fcf:
        discount_factor = (1 + wacc) ** item['year']
        pv_fcfs += item['fcf'] / discount_factor
    
    # Discount terminal value
    final_year = len(projected_fcf)
    pv_terminal = terminal_value / ((1 + wacc) ** final_year)
    
    # Enterprise Value
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
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'fair_value': max(0, fair_value)
    }

def run_sensitivity_analysis(base_fcf, growth_rates, wacc_base, terminal_growth_base, 
                             net_debt, shares, final_ebitda=None):
    """Run sensitivity analysis on key assumptions"""
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
            projected = project_fcf(base_fcf, growth_rates, 5)
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
# VISUALIZATION FUNCTIONS
# ============================================
def create_fcf_projection_chart(historical_fcf, projected_fcf):
    """Create FCF projection chart"""
    fig = go.Figure()
    
    # Historical FCF
    if historical_fcf:
        years = list(historical_fcf.keys())
        values = [v / 10000000 for v in historical_fcf.values()]  # Convert to Crores
        fig.add_trace(go.Bar(
            x=years, y=values,
            name='Historical FCF',
            marker_color='#3498db',
            text=[f'₹{v:.1f} Cr' for v in values],
            textposition='outside'
        ))
    
    # Projected FCF
    if projected_fcf:
        proj_years = [f'Year {p["year"]}' for p in projected_fcf]
        proj_values = [p['fcf'] / 10000000 for p in projected_fcf]  # Convert to Crores
        fig.add_trace(go.Bar(
            x=proj_years, y=proj_values,
            name='Projected FCF',
            marker_color='#27ae60',
            text=[f'₹{v:.1f} Cr' for v in proj_values],
            textposition='outside'
        ))
    
    fig.update_layout(
        title='Free Cash Flow: Historical & Projected',
        xaxis_title='Period',
        yaxis_title='FCF (₹ Crores)',
        template='plotly_dark',
        height=400,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    return fig

def create_valuation_waterfall(pv_fcfs, pv_terminal, net_debt, equity_value):
    """Create valuation waterfall chart"""
    fig = go.Figure(go.Waterfall(
        name="DCF Valuation",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["PV of FCFs", "PV of Terminal Value", "Less: Net Debt", "Equity Value"],
        y=[pv_fcfs / 10000000, pv_terminal / 10000000, -net_debt / 10000000, 0],
        text=[f'₹{pv_fcfs/10000000:.0f} Cr', f'₹{pv_terminal/10000000:.0f} Cr', 
              f'-₹{net_debt/10000000:.0f} Cr', f'₹{equity_value/10000000:.0f} Cr'],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#27ae60"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        totals={"marker": {"color": "#3498db"}}
    ))
    
    fig.update_layout(
        title='DCF Valuation Waterfall',
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    
    return fig

def create_sensitivity_heatmap(sensitivity_data):
    """Create sensitivity analysis heatmap"""
    matrix = sensitivity_data['matrix']
    wacc_labels = [f'{w*100:.1f}%' for w in sensitivity_data['wacc_range']]
    growth_labels = [f'{g*100:.1f}%' for g in sensitivity_data['growth_range']]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=growth_labels,
        y=wacc_labels,
        colorscale='RdYlGn',
        text=[[f'₹{val:.0f}' for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Sensitivity Analysis: Fair Value (WACC vs Terminal Growth)',
        xaxis_title='Terminal Growth Rate',
        yaxis_title='WACC',
        template='plotly_dark',
        height=400
    )
    
    return fig

def create_value_comparison_gauge(current_price, fair_value):
    """Create gauge chart comparing current price vs fair value"""
    upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fair_value,
        number={'prefix': "₹", 'font': {'size': 40}},
        delta={'reference': current_price, 'relative': True, 'valueformat': '.1%'},
        title={'text': "DCF Fair Value", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, max(fair_value * 1.5, current_price * 1.5)]},
            'bar': {'color': "#00b4d8"},
            'steps': [
                {'range': [0, current_price * 0.8], 'color': '#c0392b'},
                {'range': [current_price * 0.8, current_price], 'color': '#f39c12'},
                {'range': [current_price, current_price * 1.2], 'color': '#27ae60'},
                {'range': [current_price * 1.2, max(fair_value * 1.5, current_price * 1.5)], 'color': '#16a085'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': current_price
            }
        }
    ))
    
    fig.update_layout(
        template='plotly_dark',
        height=350,
        annotations=[
            dict(
                x=0.5, y=-0.15,
                xref='paper', yref='paper',
                text=f'Current Price: ₹{current_price:.2f}',
                showarrow=False,
                font=dict(size=16, color='white')
            )
        ]
    )
    
    return fig

def create_pie_value_composition(pv_fcfs, pv_terminal):
    """Create pie chart showing value composition"""
    total = pv_fcfs + pv_terminal
    
    fig = go.Figure(data=[go.Pie(
        labels=['PV of FCFs', 'PV of Terminal Value'],
        values=[pv_fcfs, pv_terminal],
        hole=0.4,
        marker_colors=['#3498db', '#27ae60'],
        textinfo='label+percent',
        textfont_size=14
    )])
    
    fig.update_layout(
        title='Enterprise Value Composition',
        template='plotly_dark',
        height=350,
        annotations=[dict(text=f'₹{total/10000000:.0f}Cr', x=0.5, y=0.5, 
                         font_size=16, showarrow=False)]
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
                                  textColor=colors.HexColor('#e94560'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, 
                                     textColor=colors.grey, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, 
                                    textColor=colors.HexColor('#00b4d8'))
    
    story = []
    
    # Header
    story.append(Paragraph("NYZTrade DCF Valuation Report", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Discounted Cash Flow Analysis", subtitle_style))
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
        ['DCF Fair Value', f"₹{dcf_results['fair_value']:.2f}"],
        ['Current Price', f"₹{assumptions['current_price']:.2f}"],
        ['Upside/Downside', f"{assumptions['upside']:+.1f}%"],
        ['Enterprise Value', f"₹{dcf_results['enterprise_value']/10000000:.0f} Cr"],
        ['Equity Value', f"₹{dcf_results['equity_value']/10000000:.0f} Cr"]
    ]
    
    val_table = Table(val_data, colWidths=[3*inch, 2.5*inch])
    val_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00b4d8')),
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
        ['WACC', f"{wacc_data['wacc']*100:.2f}%"],
        ['Cost of Equity', f"{wacc_data['cost_of_equity']*100:.2f}%"],
        ['Cost of Debt', f"{wacc_data['cost_of_debt']*100:.2f}%"],
        ['Beta', f"{wacc_data['beta']:.2f}"],
        ['Terminal Growth Rate', f"{assumptions['terminal_growth']*100:.1f}%"],
        ['Projection Period', f"{assumptions['projection_years']} Years"]
    ]
    
    assump_table = Table(assumptions_data, colWidths=[3*inch, 2.5*inch])
    assump_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
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
    
    breakdown_data = [
        ['Component', 'Value (₹ Cr)', '% of EV'],
        ['PV of FCFs (Years 1-5)', f"{dcf_results['pv_fcfs']/10000000:.0f}", 
         f"{dcf_results['pv_fcfs']/(dcf_results['pv_fcfs']+dcf_results['pv_terminal'])*100:.1f}%"],
        ['PV of Terminal Value', f"{dcf_results['pv_terminal']/10000000:.0f}",
         f"{dcf_results['pv_terminal']/(dcf_results['pv_fcfs']+dcf_results['pv_terminal'])*100:.1f}%"],
        ['Enterprise Value', f"{dcf_results['enterprise_value']/10000000:.0f}", '100%'],
        ['Less: Net Debt', f"-{assumptions['net_debt']/10000000:.0f}", '-'],
        ['Equity Value', f"{dcf_results['equity_value']/10000000:.0f}", '-']
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
        "Investors should conduct their own due diligence before making investment decisions.",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================
# MAIN APPLICATION
# ============================================
st.markdown('''
<div class="main-header">
    <h1>📊 DCF VALUATION MODEL</h1>
    <p>Professional Discounted Cash Flow Analysis | Real-Time Data</p>
</div>
''', unsafe_allow_html=True)

# Info cards
col1, col2, col3 = st.columns(3)
with col1:
    st.info("💰 **DCF Analysis** - Intrinsic Value Calculation")
with col2:
    st.success("📈 **5-Year Projections** - Growth & Terminal Value")
with col3:
    st.warning("🎯 **Sensitivity Analysis** - Risk Assessment")

# Sidebar
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.header("📊 Stock Selection")

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
st.sidebar.subheader("⚙️ DCF Assumptions")

# User-adjustable assumptions
with st.sidebar.expander("📊 Growth Assumptions", expanded=True):
    revenue_growth_y1 = st.slider("Revenue Growth Y1 (%)", -20, 50, 15) / 100
    revenue_growth_y2 = st.slider("Revenue Growth Y2 (%)", -20, 50, 12) / 100
    revenue_growth_y3 = st.slider("Revenue Growth Y3 (%)", -20, 50, 10) / 100
    revenue_growth_y4 = st.slider("Revenue Growth Y4 (%)", -20, 50, 8) / 100
    revenue_growth_y5 = st.slider("Revenue Growth Y5 (%)", -20, 50, 6) / 100
    growth_rates = [revenue_growth_y1, revenue_growth_y2, revenue_growth_y3, revenue_growth_y4, revenue_growth_y5]

with st.sidebar.expander("💵 WACC Parameters", expanded=False):
    risk_free_rate = st.slider("Risk-Free Rate (%)", 4.0, 10.0, 7.0) / 100
    market_premium = st.slider("Market Risk Premium (%)", 3.0, 10.0, 6.0) / 100
    custom_wacc = st.checkbox("Use Custom WACC")
    if custom_wacc:
        manual_wacc = st.slider("Custom WACC (%)", 8.0, 20.0, 12.0) / 100

with st.sidebar.expander("🔮 Terminal Value", expanded=False):
    terminal_method = st.radio("Method", ["Gordon Growth", "Exit Multiple"])
    if terminal_method == "Gordon Growth":
        terminal_growth = st.slider("Perpetual Growth (%)", 1.0, 5.0, 3.0) / 100
        exit_multiple = None
    else:
        exit_multiple = st.slider("Exit EV/EBITDA Multiple", 5.0, 20.0, 10.0)
        terminal_growth = 0.03

projection_years = st.sidebar.slider("Projection Period (Years)", 3, 10, 5)

# Analyze button
if st.sidebar.button("🚀 RUN DCF ANALYSIS", use_container_width=True, type="primary"):
    st.session_state.analyze = custom.upper() if custom else ticker

# Main analysis
if 'analyze' in st.session_state:
    t = st.session_state.analyze
    
    with st.spinner(f"📊 Fetching data for {t}..."):
        info, income_stmt, balance_sheet, cash_flow = fetch_stock_data(t)
    
    if isinstance(cash_flow, str):  # Error message
        if cash_flow == "RATE_LIMIT":
            st.error("⏱️ RATE LIMIT REACHED")
            st.warning("""
            **Yahoo Finance API limit hit. Please:**
            1. ⏰ Wait 3-5 minutes and try again
            2. 🔄 Try a different stock
            3. 📊 Cached stocks load instantly!
            """)
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
    
    # Calculate historical FCF
    historical_fcf = calculate_fcf_from_financials(info, income_stmt, cash_flow)
    
    # Get base FCF for projections
    if historical_fcf:
        base_fcf = list(historical_fcf.values())[0]
    else:
        # Fallback: Use operating cash flow - capex
        operating_cf = info.get('operatingCashflow', 0) or 0
        capex = abs(info.get('capitalExpenditures', 0) or 0)
        base_fcf = operating_cf - capex
    
    if base_fcf <= 0:
        st.warning("⚠️ Negative or zero Free Cash Flow detected. Using EBITDA-based estimation.")
        base_fcf = ebitda * 0.5 if ebitda > 0 else market_cap * 0.05
    
    # Calculate WACC
    if custom_wacc:
        wacc = manual_wacc
        wacc_data = {
            'wacc': wacc,
            'cost_of_equity': wacc,
            'cost_of_debt': wacc * 0.7,
            'beta': info.get('beta', 1.0),
            'equity_weight': 0.8,
            'debt_weight': 0.2,
            'tax_rate': 0.25
        }
    else:
        wacc_data = calculate_wacc(info, risk_free_rate, market_premium)
        wacc = wacc_data['wacc']
    
    # Project FCFs
    projected_fcf = project_fcf(base_fcf, growth_rates, projection_years)
    
    # Calculate Terminal Value
    if terminal_method == "Gordon Growth":
        sector_params = INDUSTRY_PARAMS.get(sector, INDUSTRY_PARAMS['Default'])
        tv = calculate_terminal_value_gordon(projected_fcf[-1]['fcf'], wacc, terminal_growth)
    else:
        # Use EBITDA for exit multiple
        final_year_ebitda = ebitda * np.prod([1 + g for g in growth_rates[:projection_years]])
        tv = calculate_terminal_value_exit_multiple(final_year_ebitda, exit_multiple)
    
    # Calculate DCF Value
    dcf_results = calculate_dcf_value(projected_fcf, tv, wacc, net_debt, shares_outstanding)
    fair_value = dcf_results['fair_value']
    upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
    
    # Sensitivity Analysis
    sensitivity = run_sensitivity_analysis(base_fcf, growth_rates, wacc, terminal_growth, 
                                           net_debt, shares_outstanding)
    
    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    
    st.markdown(f"## {company}")
    st.markdown(f"**Sector:** {sector} | **Ticker:** {t}")
    
    # Fair Value Display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="dcf-value-box">
            <h3>📊 DCF FAIR VALUE</h3>
            <h1 style="font-size: 3rem;">₹{fair_value:.2f}</h1>
            <p>Current Price: ₹{current_price:.2f}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        upside_class = "upside-positive" if upside > 0 else "upside-negative"
        upside_text = "UNDERVALUED" if upside > 0 else "OVERVALUED"
        st.markdown(f'''
        <div class="{upside_class}">
            <h3>{upside_text}</h3>
            <h1>{upside:+.1f}%</h1>
            <p>Potential {"Upside" if upside > 0 else "Downside"}</p>
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
    
    st.markdown("---")
    
    # Key Metrics Row
    st.subheader("📊 Key Financial Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        st.metric("Current Price", f"₹{current_price:.2f}")
    with m2:
        st.metric("Market Cap", f"₹{market_cap/10000000:.0f} Cr")
    with m3:
        st.metric("EBITDA", f"₹{ebitda/10000000:.0f} Cr" if ebitda else "N/A")
    with m4:
        st.metric("Net Debt", f"₹{net_debt/10000000:.0f} Cr")
    with m5:
        st.metric("Base FCF", f"₹{base_fcf/10000000:.1f} Cr")
    
    # Recommendation
    if upside > 40:
        rec_class, rec_text = "rec-strong-buy", "🚀 STRONG BUY"
    elif upside > 20:
        rec_class, rec_text = "rec-buy", "✅ BUY"
    elif upside > 0:
        rec_class, rec_text = "rec-buy", "📈 ACCUMULATE"
    elif upside > -15:
        rec_class, rec_text = "rec-hold", "⏸️ HOLD"
    else:
        rec_class, rec_text = "rec-avoid", "❌ AVOID"
    
    st.markdown(f'<div class="{rec_class}">{rec_text}<br>DCF Upside: {upside:+.1f}%</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Section
    tab1, tab2, tab3, tab4 = st.tabs(["📈 FCF Projection", "💧 Valuation Waterfall", "🎯 Sensitivity Analysis", "📊 Value Composition"])
    
    with tab1:
        fig = create_fcf_projection_chart(historical_fcf, projected_fcf)
        st.plotly_chart(fig, use_container_width=True)
        
        # FCF Table
        st.subheader("📋 Projected Free Cash Flows")
        fcf_df = pd.DataFrame([
            {
                'Year': f'Year {p["year"]}',
                'FCF (₹ Cr)': f'{p["fcf"]/10000000:.1f}',
                'Growth Rate': f'{p["growth_rate"]*100:.1f}%',
                'Discount Factor': f'{1/(1+wacc)**p["year"]:.4f}',
                'PV of FCF (₹ Cr)': f'{(p["fcf"] / (1+wacc)**p["year"])/10000000:.1f}'
            }
            for p in projected_fcf
        ])
        st.dataframe(fcf_df, use_container_width=True, hide_index=True)
    
    with tab2:
        fig = create_valuation_waterfall(dcf_results['pv_fcfs'], dcf_results['pv_terminal'], 
                                         net_debt, dcf_results['equity_value'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Value breakdown
        st.subheader("💰 Value Breakdown")
        breakdown_df = pd.DataFrame({
            'Component': ['PV of FCFs (Years 1-5)', 'PV of Terminal Value', 'Enterprise Value', 
                         'Less: Net Debt', 'Equity Value', 'Shares Outstanding', 'Fair Value/Share'],
            'Value': [
                f'₹{dcf_results["pv_fcfs"]/10000000:.0f} Cr',
                f'₹{dcf_results["pv_terminal"]/10000000:.0f} Cr',
                f'₹{dcf_results["enterprise_value"]/10000000:.0f} Cr',
                f'-₹{net_debt/10000000:.0f} Cr',
                f'₹{dcf_results["equity_value"]/10000000:.0f} Cr',
                f'{shares_outstanding/10000000:.2f} Cr',
                f'₹{fair_value:.2f}'
            ]
        })
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
    
    with tab3:
        fig = create_sensitivity_heatmap(sensitivity)
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **How to read this chart:**
        - Rows show different WACC (discount rate) assumptions
        - Columns show different terminal growth rate assumptions
        - Green = Higher fair values (more attractive)
        - Red = Lower fair values (less attractive)
        """)
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_pie_value_composition(dcf_results['pv_fcfs'], dcf_results['pv_terminal'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_value_comparison_gauge(current_price, fair_value)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # WACC Breakdown
    st.subheader("📐 WACC Calculation Details")
    
    wacc_col1, wacc_col2 = st.columns(2)
    
    with wacc_col1:
        wacc_df = pd.DataFrame({
            'Parameter': ['WACC', 'Cost of Equity', 'Cost of Debt (After Tax)', 'Beta', 
                         'Equity Weight', 'Debt Weight', 'Tax Rate'],
            'Value': [
                f'{wacc_data["wacc"]*100:.2f}%',
                f'{wacc_data["cost_of_equity"]*100:.2f}%',
                f'{wacc_data["cost_of_debt"]*(1-wacc_data["tax_rate"])*100:.2f}%',
                f'{wacc_data["beta"]:.2f}',
                f'{wacc_data["equity_weight"]*100:.1f}%',
                f'{wacc_data["debt_weight"]*100:.1f}%',
                f'{wacc_data["tax_rate"]*100:.0f}%'
            ]
        })
        st.dataframe(wacc_df, use_container_width=True, hide_index=True)
    
    with wacc_col2:
        st.markdown("""
        **WACC Formula:**
        ```
        WACC = (E/V × Re) + (D/V × Rd × (1-T))
        
        Where:
        E = Market value of equity
        D = Market value of debt
        V = E + D (Total value)
        Re = Cost of equity (CAPM)
        Rd = Cost of debt
        T = Tax rate
        
        Cost of Equity (CAPM):
        Re = Rf + β × (Rm - Rf)
        ```
        """)
    
    st.markdown("---")
    
    # Company Fundamentals
    st.subheader("🏢 Company Fundamentals")
    
    fund_df = pd.DataFrame({
        'Metric': ['P/E Ratio', 'Forward P/E', 'PEG Ratio', 'Price to Book', 
                  'EV/EBITDA', 'Profit Margin', 'ROE', 'Debt/Equity'],
        'Value': [
            f'{info.get("trailingPE", "N/A"):.2f}' if info.get("trailingPE") else 'N/A',
            f'{info.get("forwardPE", "N/A"):.2f}' if info.get("forwardPE") else 'N/A',
            f'{info.get("pegRatio", "N/A"):.2f}' if info.get("pegRatio") else 'N/A',
            f'{info.get("priceToBook", "N/A"):.2f}' if info.get("priceToBook") else 'N/A',
            f'{info.get("enterpriseToEbitda", "N/A"):.2f}' if info.get("enterpriseToEbitda") else 'N/A',
            f'{info.get("profitMargins", 0)*100:.1f}%' if info.get("profitMargins") else 'N/A',
            f'{info.get("returnOnEquity", 0)*100:.1f}%' if info.get("returnOnEquity") else 'N/A',
            f'{info.get("debtToEquity", "N/A"):.2f}' if info.get("debtToEquity") else 'N/A'
        ]
    })
    st.dataframe(fund_df, use_container_width=True, hide_index=True)

else:
    # Welcome screen
    st.info("👈 Select a stock from the sidebar and click **RUN DCF ANALYSIS** to begin")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 What is DCF Valuation?
        
        **Discounted Cash Flow (DCF)** is a valuation method that estimates the intrinsic value of a company based on its expected future cash flows.
        
        **Key Components:**
        - **Free Cash Flow (FCF)**: Cash generated after all expenses
        - **WACC**: Weighted Average Cost of Capital (discount rate)
        - **Terminal Value**: Value beyond the projection period
        - **Net Present Value**: Sum of all discounted cash flows
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 Features
        
        - ✅ **Real-time data** from Yahoo Finance
        - ✅ **Customizable assumptions** for growth & WACC
        - ✅ **Sensitivity analysis** matrix
        - ✅ **Gordon Growth & Exit Multiple** terminal value methods
        - ✅ **Professional PDF reports**
        - ✅ **Interactive visualizations**
        - ✅ **100+ Indian stocks** pre-loaded
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 📈 DCF Formula
    
    ```
    Enterprise Value = Σ (FCFt / (1 + WACC)^t) + (Terminal Value / (1 + WACC)^n)
    
    Equity Value = Enterprise Value - Net Debt
    
    Fair Value per Share = Equity Value / Shares Outstanding
    ```
    
    **Terminal Value (Gordon Growth):**
    ```
    TV = FCFn × (1 + g) / (WACC - g)
    ```
    
    **Terminal Value (Exit Multiple):**
    ```
    TV = Final Year EBITDA × Exit Multiple
    ```
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><b>NYZTrade DCF Valuation Platform</b> | Professional Analysis Tool</p>
    <p style='font-size: 0.8rem;'>⚠️ Educational purposes only. Not financial advice. Always do your own research.</p>
</div>
""", unsafe_allow_html=True)
