import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pdb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Singapore Family Finance Planner",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e8df5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("新加坡家庭财务规划器")
st.markdown("这个应用程序帮助您规划和可视化未来6年的家庭财务状况。")

# Initialize session state for one-time expenses
if 'one_time_expenses' not in st.session_state:
    st.session_state.one_time_expenses = []

# Sidebar for inputs
with st.sidebar:
    st.header("基本财务信息")
    
    # Initial funds
    initial_funds = st.number_input("现有资金 (SGD)", min_value=0.0, value=500000.0, step=1000.0, help="您目前已有的储蓄或投资")
    
    # Housing status
    st.subheader("住房状况")
    housing_status = st.radio("住房状态", ["计划购房", "已购房", "暂无购房计划"], index=0)
    
    logger.info(f"Processing housing status: {housing_status}")
    
    if housing_status == "已购房":
        monthly_mortgage = st.number_input("月房贷 (SGD)", min_value=0.0, value=1500.0, step=100.0)
    elif housing_status == "计划购房":
        house_purchase_date = st.date_input("计划购房日期", value=datetime(2025, 5, 1))
        house_price = st.number_input("房屋总价 (SGD)", min_value=0.0, value=1700000.0, step=10000.0)
        down_payment_percent = st.slider("首付比例 (%)", min_value=5, max_value=50, value=25)
        down_payment = house_price * (down_payment_percent / 100)
        st.write(f"首付金额: ${down_payment:,.2f}")
        loan_amount = house_price - down_payment
        st.write(f"贷款金额: ${loan_amount:,.2f}")
        loan_years = st.slider("贷款年限", min_value=5, max_value=30, value=20)
        interest_rate = st.slider("年利率 (%)", min_value=1.0, max_value=5.0, value=2.5, step=0.1)
        
        # Calculate monthly mortgage payment using the formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
        # where P is payment, L is loan amount, c is monthly interest rate, n is number of payments
        monthly_interest_rate = interest_rate / 100 / 12
        total_payments = loan_years * 12
        if monthly_interest_rate > 0:
            monthly_mortgage = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** total_payments) / ((1 + monthly_interest_rate) ** total_payments - 1)
        else:
            monthly_mortgage = loan_amount / total_payments
        
        st.write(f"预计月供: ${monthly_mortgage:.2f}")
        
        # Housing taxes and fees
        st.subheader("购房税费")
        
        # Buyer's citizenship status affects ABSD rates
        buyer_status = st.selectbox("买家身份", ["新加坡公民 (首套房)", "新加坡公民 (二套房+)", 
                                           "新加坡永久居民 (首套房)", "新加坡永久居民 (二套房+)", 
                                           "外国人"])
        
        # Calculate Buyer's Stamp Duty (BSD)
        # BSD rates in Singapore (as of 2023):
        # First $180,000: 1%
        # Next $180,000: 2%
        # Next $640,000: 3%
        # Remaining amount: 4%
        def calculate_bsd(price):
            if price <= 180000:
                return price * 0.01
            elif price <= 360000:
                return 180000 * 0.01 + (price - 180000) * 0.02
            elif price <= 1000000:
                return 180000 * 0.01 + 180000 * 0.02 + (price - 360000) * 0.03
            else:
                return 180000 * 0.01 + 180000 * 0.02 + 640000 * 0.03 + (price - 1000000) * 0.04
        
        bsd = calculate_bsd(house_price)
        st.write(f"买方印花税 (BSD): ${bsd:,.2f}")
        
        # Calculate Additional Buyer's Stamp Duty (ABSD)
        absd_rates = {
            "新加坡公民 (首套房)": 0,
            "新加坡公民 (二套房+)": 0.17,
            "新加坡永久居民 (首套房)": 0.05,
            "新加坡永久居民 (二套房+)": 0.25,
            "外国人": 0.30
        }
        
        absd_rate = absd_rates[buyer_status]
        absd = house_price * absd_rate
        
        if absd > 0:
            st.write(f"额外买方印花税 (ABSD): ${absd:,.2f} ({absd_rate*100}%)")
        else:
            st.write("额外买方印花税 (ABSD): $0.00 (0%)")
        
        # Legal fees and other costs
        include_legal_fees = st.checkbox("包含法律费用和其他费用", value=True)
        
        if include_legal_fees:
            legal_fees = st.number_input("法律费用 (SGD)", min_value=0.0, value=6000.0, step=500.0)
            other_fees = st.number_input("其他费用 (SGD)", min_value=0.0, value=2000.0, step=500.0, 
                                       help="包括估价费、房屋检查费、保险费等")
        else:
            legal_fees = 0.0
            other_fees = 0.0
        
        # Calculate total one-time costs
        total_taxes_fees = bsd + absd + legal_fees + other_fees
        st.write(f"购房一次性税费总计: ${total_taxes_fees:,.2f}")
        
        # Total cash outlay at purchase
        total_cash_outlay = down_payment + total_taxes_fees
        st.write(f"购房时总现金支出: ${total_cash_outlay:,.2f}", unsafe_allow_html=True)
        
        # Check if this exceeds available funds
        if total_cash_outlay > initial_funds:
            st.warning(f"⚠️ 购房总现金支出 (${total_cash_outlay:,.2f}) 超过了您的现有资金 (${initial_funds:,.2f})。您需要额外筹集 ${total_cash_outlay - initial_funds:,.2f}。")
    else:
        monthly_mortgage = 0.0
    
    # Monthly income and expenses
    st.subheader("月度收入与支出")
    monthly_income = st.number_input("月收入 (SGD)", min_value=0.0, value=11000.0, step=100.0)
    monthly_expenses = st.number_input("月常规支出 (SGD)", min_value=0.0, value=2000.0, step=100.0)
    monthly_child_expenses = st.number_input("月小孩常规支出 (SGD)", min_value=0.0, value=500.0, step=100.0)
    
    # Annual expenses
    st.subheader("年度支出")
    annual_insurance = st.number_input("年度保险 (SGD)", min_value=0.0, value=5000.0, step=100.0)
    annual_tax = st.number_input("年度税款 (SGD)", min_value=0.0, value=7000.0, step=100.0)
    annual_bonus = st.number_input("年度奖金 (SGD)", min_value=0.0, value=30000.0, step=500.0)
    
    # Child education expenses
    st.subheader("教育支出")
    childcare_monthly = st.number_input("托儿所月费 (SGD)", min_value=0.0, value=1000.0, step=100.0)
    preschool_monthly = st.number_input("学前班月费 (SGD)", min_value=0.0, value=1200.0, step=100.0)
    primary_school_monthly = st.number_input("小学月费 (SGD)", min_value=0.0, value=300.0, step=50.0)
    
    # Child age or expected birth date
    st.subheader("小孩信息")
    child_status = st.radio("小孩状态", ["已出生", "预产期", "计划中"])
    
    if child_status == "已出生":
        child_birth_date = st.date_input("出生日期", value=datetime.now() - timedelta(days=365))
    elif child_status == "预产期":
        child_birth_date = st.date_input("预产期", value=datetime.now() + timedelta(days=90))
    else:
        child_birth_date = st.date_input("计划生育日期", value=datetime(2026, 12, 1))

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["财务规划", "一次性支出", "图表分析"])

with tab1:
    st.header("6年财务规划")
    
    # Calculate start date and generate month range
    start_date = datetime.now().replace(day=1)
    months = pd.date_range(start=start_date, periods=72, freq='M')
    
    # Create dataframe for financial projection
    df = pd.DataFrame(index=months)
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['MonthName'] = df.index.strftime('%b')
    
    # Calculate child age in months at each point
    child_birth_date_dt = pd.to_datetime(child_birth_date)
    df['ChildAgeMonths'] = ((df.index.year - child_birth_date_dt.year) * 12 + 
                           df.index.month - child_birth_date_dt.month)
    
    # Basic monthly calculations
    df['MonthlyIncome'] = monthly_income
    
    # Handle mortgage based on housing status
    df['MonthlyMortgage'] = 0.0
    df['PropertyValue'] = 0.0  # Add property value column
    df['PropertyEquity'] = 0.0  # Add property equity column
    df['OutstandingLoan'] = 0.0  # Initialize OutstandingLoan column for all scenarios
    
    if housing_status == "已购房":
        df['MonthlyMortgage'] = monthly_mortgage
        
        # For already purchased homes, ask for property value and outstanding loan
        property_value = st.sidebar.number_input("房产当前市值 (SGD)", min_value=0.0, value=500000.0, step=10000.0)
        outstanding_loan = st.sidebar.number_input("剩余贷款金额 (SGD)", min_value=0.0, value=300000.0, step=10000.0)
        
        # Set property value (with 2% annual appreciation)
        months = np.arange(len(df))
        df['PropertyValue'] = property_value * np.power(1 + 0.02/12, months)
        
        # Calculate equity (property value minus outstanding loan)
        # Loan decreases with each payment
        monthly_principal = 0
        if monthly_mortgage > 0:
            # Estimate monthly principal payment (simplified)
            remaining_months = outstanding_loan / monthly_mortgage
            monthly_principal = outstanding_loan / remaining_months
        
        # Initialize outstanding loan for each month
        current_loan = outstanding_loan
        
        for i in range(len(df)):
            if i == 0:
                df.loc[df.index[i], 'OutstandingLoan'] = current_loan
            else:
                current_loan = max(0, current_loan - monthly_principal)
                df.loc[df.index[i], 'OutstandingLoan'] = current_loan
        
        df['PropertyEquity'] = df['PropertyValue'] - df['OutstandingLoan']
        
    elif housing_status == "计划购房":
        house_purchase_date_dt = pd.to_datetime(house_purchase_date)
        purchase_month = house_purchase_date_dt.replace(day=1)
        
        # Add down payment and taxes/fees as one-time expenses
        if 'OneTimeExpenses' not in df.columns:
            df['OneTimeExpenses'] = 0.0
        
        logger.info(f"Purchase index: {purchase_month}, df.index: {df.index}")
        
        # Fix: Find the closest date AFTER the purchase_month
        if purchase_month not in df.index:
            # Get all dates that are on or after the purchase month
            future_dates = [date for date in df.index if date >= purchase_month]
            
            if future_dates:
                # Get the first date that's on or after the purchase month
                closest_date = min(future_dates)
                logger.info(f"Purchase month {purchase_month} not found in index. Using next available date: {closest_date}")
                purchase_month = closest_date
            else:
                logger.warning(f"No future dates available after {purchase_month}. Housing purchase may not be reflected in projections.")
        
        if purchase_month in df.index:
            # Add down payment
            df.loc[purchase_month, 'OneTimeExpenses'] += down_payment
            
            # Add taxes and fees
            df.loc[purchase_month, 'OneTimeExpenses'] += total_taxes_fees
            
            # Add special columns to track these major expenses
            if 'HousingDownPayment' not in df.columns:
                df['HousingDownPayment'] = 0.0
            df.loc[purchase_month, 'HousingDownPayment'] = down_payment
            
            if 'HousingTaxesFees' not in df.columns:
                df['HousingTaxesFees'] = 0.0
            df.loc[purchase_month, 'HousingTaxesFees'] = total_taxes_fees
            
            # Apply mortgage payments after purchase date
            mortgage_mask = df.index >= purchase_month
            df.loc[mortgage_mask, 'MonthlyMortgage'] = monthly_mortgage
            
            # Set property value (with 2% annual appreciation)
            purchase_index = df.index.get_loc(purchase_month)
            logger.info(f"Purchase index: {purchase_index}")
            for i in range(len(df)):
                if i >= purchase_index:
                    months_since_purchase = i - purchase_index
                    df.loc[df.index[i], 'PropertyValue'] = house_price * (1 + 0.02/12) ** months_since_purchase
            
            # Calculate outstanding loan for each month
            current_loan = loan_amount
            
            # Calculate monthly principal payment
            monthly_interest_rate = interest_rate / 100 / 12
            if monthly_interest_rate > 0:
                for i in range(len(df)):
                    if i >= purchase_index:
                        if i == purchase_index:
                            df.loc[df.index[i], 'OutstandingLoan'] = current_loan
                        else:
                            # Calculate interest portion
                            interest_payment = current_loan * monthly_interest_rate
                            principal_payment = monthly_mortgage - interest_payment
                            current_loan = max(0, current_loan - principal_payment)
                            df.loc[df.index[i], 'OutstandingLoan'] = current_loan
            
            # Calculate property equity (property value minus outstanding loan)
            df['PropertyEquity'] = df['PropertyValue'] - df['OutstandingLoan']
    
    df['MonthlyExpenses'] = monthly_expenses
    
    # Child expenses based on age
    df['ChildcareExpense'] = 0.0
    df['PreschoolExpense'] = 0.0
    df['PrimarySchoolExpense'] = 0.0
    
    # Apply education expenses based on child's age
    # Childcare (6 months to 4 years)
    childcare_mask = (df['ChildAgeMonths'] >= 6) & (df['ChildAgeMonths'] < 48)
    df.loc[childcare_mask, 'ChildcareExpense'] = childcare_monthly
    
    # Preschool (4 years to 7 years)
    preschool_mask = (df['ChildAgeMonths'] >= 48) & (df['ChildAgeMonths'] < 84)
    df.loc[preschool_mask, 'PreschoolExpense'] = preschool_monthly
    
    # Primary school (7 years and above)
    primary_mask = df['ChildAgeMonths'] >= 84
    df.loc[primary_mask, 'PrimarySchoolExpense'] = primary_school_monthly
    
    # Regular child expenses only after birth
    df['MonthlyChildExpenses'] = np.where(df['ChildAgeMonths'] >= 0, monthly_child_expenses, 0)
    
    # Annual expenses (divided by 12 for monthly impact)
    df['MonthlyInsurance'] = annual_insurance / 12
    df['MonthlyTax'] = annual_tax / 12
    
    # Annual bonus (only in December)
    df['Bonus'] = 0.0
    df.loc[df['Month'] == 12, 'Bonus'] = annual_bonus

    # Function to add one-time expenses
    with tab2:
        st.header("添加一次性支出")
        
        # Form for adding one-time expenses
        with st.form("one_time_expense_form"):
            col1, col2 = st.columns(2)
            with col1:
                expense_name = st.text_input("支出名称", placeholder="例如: 产检费用")
                expense_amount = st.number_input("金额 (SGD)", min_value=0.0, value=1000.0, step=100.0)
            with col2:
                expense_date = st.date_input("日期", value=datetime.now() + timedelta(days=30))
                expense_category = st.selectbox("类别", 
                                              ["产检费用", "生育费用", "坐月子费用", "教育费用", "房屋相关", "其他"])
            
            submit_button = st.form_submit_button("添加支出")
            
            if submit_button and expense_name and expense_amount > 0:
                st.session_state.one_time_expenses.append({
                    "name": expense_name,
                    "amount": expense_amount,
                    "date": expense_date,
                    "category": expense_category
                })
                st.success(f"已添加: {expense_name} - ${expense_amount:.2f}")
        
        # Display and manage one-time expenses
        if st.session_state.one_time_expenses:
            st.subheader("已添加的一次性支出")
            
            expense_df = pd.DataFrame(st.session_state.one_time_expenses)
            expense_df['date'] = pd.to_datetime(expense_df['date'])
            expense_df = expense_df.sort_values('date')
            
            # Display expenses in a table
            st.dataframe(
                expense_df.rename(columns={
                    "name": "名称",
                    "amount": "金额 (SGD)",
                    "date": "日期",
                    "category": "类别"
                }),
                hide_index=True,
                use_container_width=True
            )
            
            # Add button to clear all expenses
            if st.button("清除所有一次性支出"):
                st.session_state.one_time_expenses = []
                st.experimental_rerun()
            
            # Add one-time expenses to the financial projection
            for _, expense in expense_df.iterrows():
                expense_month = expense['date'].replace(day=1)
                if expense_month in df.index:
                    if 'OneTimeExpenses' not in df.columns:
                        df['OneTimeExpenses'] = 0.0
                    df.loc[expense_month, 'OneTimeExpenses'] += expense['amount']
        else:
            st.info("尚未添加任何一次性支出")
    
    # If OneTimeExpenses column doesn't exist, create it with zeros
    if 'OneTimeExpenses' not in df.columns:
        df['OneTimeExpenses'] = 0.0
    
    # Calculate total monthly expenses and savings
    df['TotalEducationExpenses'] = df['ChildcareExpense'] + df['PreschoolExpense'] + df['PrimarySchoolExpense']
    df['TotalMonthlyExpenses'] = (df['MonthlyMortgage'] + df['MonthlyExpenses'] + 
                                 df['MonthlyChildExpenses'] + df['MonthlyInsurance'] + 
                                 df['MonthlyTax'] + df['TotalEducationExpenses'] + 
                                 df['OneTimeExpenses'])
    
    df['MonthlySavings'] = df['MonthlyIncome'] + df['Bonus'] - df['TotalMonthlyExpenses']
    
    # Calculate cumulative savings
    df['CumulativeSavings'] = initial_funds

    # Recalculate cumulative savings to account for housing purchase
    for i in range(1, len(df)):
        df.loc[df.index[i], 'CumulativeSavings'] = df.loc[df.index[i-1], 'CumulativeSavings'] + df.loc[df.index[i], 'MonthlySavings']

    # Calculate total assets (savings + property equity)
    df['TotalAssets'] = df['CumulativeSavings'] + df['PropertyEquity']
    
    # Display the financial projection table
    st.subheader("月度财务预测")
    
    # Format the dataframe for display
    display_df = df.copy()
    
    # Define columns based on housing status to avoid KeyError
    base_columns = [
        'Year', 'MonthName', 'MonthlyIncome', 'Bonus', 'MonthlyMortgage', 
        'MonthlyExpenses', 'MonthlyChildExpenses', 'TotalEducationExpenses',
        'OneTimeExpenses', 'TotalMonthlyExpenses', 'MonthlySavings', 'CumulativeSavings'
    ]
    
    # Add property-related columns if they exist
    property_columns = ['PropertyValue', 'OutstandingLoan', 'PropertyEquity', 'TotalAssets']
    display_columns = base_columns + [col for col in property_columns if col in df.columns]
    
    display_df = display_df[display_columns]
    
    # Define column names mapping
    column_names = {
        'Year': '年份', 
        'MonthName': '月份', 
        'MonthlyIncome': '月收入', 
        'Bonus': '奖金', 
        'MonthlyMortgage': '房贷', 
        'MonthlyExpenses': '常规支出', 
        'MonthlyChildExpenses': '小孩支出', 
        'TotalEducationExpenses': '教育支出',
        'OneTimeExpenses': '一次性支出', 
        'TotalMonthlyExpenses': '总支出', 
        'MonthlySavings': '月度储蓄', 
        'CumulativeSavings': '累计储蓄'
    }
    
    # Add property column names if they exist
    if 'PropertyValue' in display_df.columns:
        column_names['PropertyValue'] = '房产价值'
    if 'OutstandingLoan' in display_df.columns:
        column_names['OutstandingLoan'] = '剩余贷款'
    if 'PropertyEquity' in display_df.columns:
        column_names['PropertyEquity'] = '房产净值'
    if 'TotalAssets' in display_df.columns:
        column_names['TotalAssets'] = '总资产'
    
    # Rename columns
    display_df.columns = [column_names.get(col, col) for col in display_df.columns]
    
    # Format numbers to 2 decimal places
    for col in display_df.columns:
        if col not in ['年份', '月份']:
            display_df[col] = display_df[col].map('${:,.2f}'.format)
    
    st.dataframe(display_df, use_container_width=True)

with tab3:
    st.header("财务图表分析")
    
    # Create multiple charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Cash Savings with Key Events
        st.subheader("现金储蓄变化与重大事件")
        
        fig_events = go.Figure()
        
        # Convert datetime to string for plotly to avoid orjson issues
        date_strings = [d.strftime('%Y-%m-%d') for d in df.index]
        initial_date_str = (df.index[0] - pd.Timedelta(days=15)).strftime('%Y-%m-%d')
        
        # Add a marker for initial funds
        fig_events.add_trace(go.Scatter(
            x=[initial_date_str],  # Use string format instead of datetime
            y=[initial_funds],
            name='初始资金',
            mode='markers',
            marker=dict(size=12, color='green', symbol='diamond')
        ))
        
        # Add cumulative savings line
        fig_events.add_trace(go.Scatter(
            x=date_strings,  # Use string format instead of datetime
            y=df['CumulativeSavings'],
            name='累计储蓄',
            line=dict(color='blue', width=3)
        ))
        
        # Add annotation for initial funds
        fig_events.add_annotation(
            x=initial_date_str,
            y=initial_funds,
            text=f"初始资金: ${initial_funds:,.2f}",
            showarrow=True,
            arrowhead=1,
            ax=-40,
            ay=-40
        )
        
        # Add markers and annotations for housing purchase
        if housing_status == "计划购房":
            house_purchase_date_dt = pd.to_datetime(house_purchase_date)
            purchase_month = house_purchase_date_dt.replace(day=1)
            
            if purchase_month in df.index:
                purchase_idx = df.index.get_loc(purchase_month)
                purchase_month_str = purchase_month.strftime('%Y-%m-%d')
                
                # Get savings value right before purchase
                pre_purchase_savings = df['CumulativeSavings'].iloc[purchase_idx]
                
                # Get savings value right after purchase (after down payment and fees)
                post_purchase_savings = pre_purchase_savings - total_cash_outlay
                
                # Add markers for pre and post purchase
                fig_events.add_trace(go.Scatter(
                    x=[purchase_month_str],
                    y=[pre_purchase_savings],
                    name='购房前储蓄',
                    mode='markers',
                    marker=dict(size=12, color='orange', symbol='circle')
                ))
                
                fig_events.add_trace(go.Scatter(
                    x=[purchase_month_str],
                    y=[post_purchase_savings],
                    name='购房后储蓄',
                    mode='markers',
                    marker=dict(size=12, color='red', symbol='circle')
                ))
                
                # Add annotation for housing purchase
                fig_events.add_annotation(
                    x=purchase_month_str,
                    y=(pre_purchase_savings + post_purchase_savings) / 2,
                    text=f"购房支出: ${total_cash_outlay:,.2f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor="red",
                    ax=50,
                    ay=0
                )
                
                # Add a vertical line at purchase date
                fig_events.add_shape(
                    type="line",
                    x0=purchase_month_str,
                    y0=0,
                    x1=purchase_month_str,
                    y1=pre_purchase_savings,
                    line=dict(color="red", width=1, dash="dash")
                )
        
        # Add markers and annotations for child-related events
        child_birth_date_dt = pd.to_datetime(child_birth_date)
        
        # Find significant child-related events
        child_events = []
        
        # Birth event
        if child_status in ["已出生", "预产期"]:
            birth_month = child_birth_date_dt.replace(day=1)
            if birth_month in df.index:
                child_events.append({
                    "date": birth_month,
                    "date_str": birth_month.strftime('%Y-%m-%d'),
                    "name": "宝宝出生",
                    "symbol": "star",
                    "color": "purple"
                })
        
        # Childcare start (around 6 months)
        childcare_start = child_birth_date_dt + pd.DateOffset(months=6)
        childcare_start = childcare_start.replace(day=1)
        if childcare_start in df.index:
            child_events.append({
                "date": childcare_start,
                "date_str": childcare_start.strftime('%Y-%m-%d'),
                "name": "开始托儿所",
                "symbol": "triangle-up",
                "color": "blue"
            })
        
        # Preschool start (around 4 years)
        preschool_start = child_birth_date_dt + pd.DateOffset(months=48)
        preschool_start = preschool_start.replace(day=1)
        if preschool_start in df.index:
            child_events.append({
                "date": preschool_start,
                "date_str": preschool_start.strftime('%Y-%m-%d'),
                "name": "开始学前班",
                "symbol": "triangle-up",
                "color": "green"
            })
        
        # Primary school start (around 7 years)
        primary_start = child_birth_date_dt + pd.DateOffset(months=84)
        primary_start = primary_start.replace(day=1)
        if primary_start in df.index:
            child_events.append({
                "date": primary_start,
                "date_str": primary_start.strftime('%Y-%m-%d'),
                "name": "开始小学",
                "symbol": "triangle-up",
                "color": "orange"
            })
        
        # Add one-time child expenses from user input
        if st.session_state.one_time_expenses:
            expense_df = pd.DataFrame(st.session_state.one_time_expenses)
            expense_df['date'] = pd.to_datetime(expense_df['date'])
            
            for _, expense in expense_df.iterrows():
                if expense['category'] in ["产检费用", "生育费用", "坐月子费用", "教育费用"]:
                    expense_month = expense['date'].replace(day=1)
                    if expense_month in df.index:
                        child_events.append({
                            "date": expense_month,
                            "date_str": expense_month.strftime('%Y-%m-%d'),
                            "name": expense['name'],
                            "amount": expense['amount'],
                            "symbol": "circle",
                            "color": "red"
                        })
        
        # Add child events to chart
        for event in child_events:
            if event["date"] in df.index:
                event_idx = df.index.get_loc(event["date"])
                savings_at_event = df['CumulativeSavings'].iloc[event_idx]
                
                # Add marker
                fig_events.add_trace(go.Scatter(
                    x=[event["date_str"]],  # Use string format
                    y=[savings_at_event],
                    name=event["name"],
                    mode='markers',
                    marker=dict(size=10, color=event["color"], symbol=event["symbol"])
                ))
                
                # Add annotation
                annotation_text = event["name"]
                if "amount" in event:
                    annotation_text += f": ${event['amount']:,.2f}"
                    
                fig_events.add_annotation(
                    x=event["date_str"],
                    y=savings_at_event,
                    text=annotation_text,
                    showarrow=True,
                    arrowhead=1,
                    ax=40,
                    ay=-30
                )
        
        fig_events.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            height=500,  # Make this chart taller
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        # Use try-except to handle potential errors with plotly
        try:
            st.plotly_chart(fig_events, use_container_width=True)
        except Exception as e:
            st.error(f"图表渲染错误: {str(e)}")
            st.info("请尝试调整输入参数或刷新页面。")
        
        # Cumulative Savings and Total Assets
        st.subheader("累计储蓄与总资产")
        fig3 = go.Figure()
        
        # Add a marker for initial funds
        fig3.add_trace(go.Scatter(
            x=[initial_date_str],  # Use string format
            y=[initial_funds],
            name='初始资金',
            mode='markers',
            marker=dict(size=12, color='green', symbol='diamond')
        ))
        
        # Add cumulative savings line
        fig3.add_trace(go.Scatter(
            x=date_strings,  # Use string format
            y=df['CumulativeSavings'],
            name='累计储蓄',
            line=dict(color='blue', width=3)
        ))
        
        # Add property equity line if housing is included
        if housing_status in ["已购房", "计划购房"]:
            fig3.add_trace(go.Scatter(
                x=date_strings,  # Use string format
                y=df['PropertyEquity'],
                name='房产净值',
                line=dict(color='orange', width=2)
            ))
            
            # Add total assets line
            fig3.add_trace(go.Scatter(
                x=date_strings,  # Use string format
                y=df['TotalAssets'],
                name='总资产',
                line=dict(color='red', width=3)
            ))
        
        # Add annotation for initial funds
        fig3.add_annotation(
            x=initial_date_str,
            y=initial_funds,
            text=f"初始资金: ${initial_funds:,.2f}",
            showarrow=True,
            arrowhead=1,
            ax=-40,
            ay=-40
        )
        
        # Add markers and annotations for housing purchase impact on savings
        if housing_status == "计划购房":
            house_purchase_date_dt = pd.to_datetime(house_purchase_date)
            purchase_month = house_purchase_date_dt.replace(day=1)
            
            if purchase_month in df.index:
                purchase_idx = df.index.get_loc(purchase_month)
                purchase_month_str = purchase_month.strftime('%Y-%m-%d')
                
                # Get values right before purchase
                if purchase_idx > 0:
                    pre_purchase_month = df.index[purchase_idx - 1]
                    pre_purchase_month_str = pre_purchase_month.strftime('%Y-%m-%d')
                    pre_purchase_savings = df['CumulativeSavings'].iloc[purchase_idx - 1]
                else:
                    pre_purchase_month = purchase_month
                    pre_purchase_month_str = purchase_month_str
                    pre_purchase_savings = df['CumulativeSavings'].iloc[purchase_idx] + total_cash_outlay
                
                # Get values at purchase
                purchase_savings = df['CumulativeSavings'].iloc[purchase_idx]
                purchase_equity = df['PropertyEquity'].iloc[purchase_idx]
                purchase_assets = df['TotalAssets'].iloc[purchase_idx]
                
                # Add markers for the drop in savings
                fig3.add_trace(go.Scatter(
                    x=[pre_purchase_month_str, purchase_month_str],
                    y=[pre_purchase_savings, purchase_savings],
                    name='购房储蓄变化',
                    mode='lines+markers',
                    line=dict(color='red', width=4, dash='dash'),
                    marker=dict(size=10, color=['green', 'red'])
                ))
                
                # Add annotation for the drop
                fig3.add_annotation(
                    x=purchase_month_str,  # Simplified to avoid date arithmetic
                    y=(pre_purchase_savings + purchase_savings) / 2,
                    text=f"购房支出: ${total_cash_outlay:,.2f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor="red",
                    ax=0,
                    ay=-40
                )
                
                # Add annotation for property equity gained
                fig3.add_annotation(
                    x=purchase_month_str,
                    y=purchase_equity / 2,
                    text=f"获得房产净值: ${purchase_equity:,.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=40,
                    ay=0,
                    font=dict(color="orange")
                )
                
                # Add a vertical line at purchase date
                fig3.add_shape(
                    type="line",
                    x0=purchase_month_str,
                    y0=0,
                    x1=purchase_month_str,
                    y1=max(pre_purchase_savings, purchase_assets),
                    line=dict(color="black", width=1, dash="dash")
                )
                
                # Add an arrow showing the conversion from cash to equity
                fig3.add_annotation(
                    x=purchase_month_str,
                    y=purchase_savings + (purchase_equity / 2),
                    text="现金转换为房产净值",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor="orange",
                    ax=0,
                    ay=-60
                )
        
        fig3.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            height=500,  # Make this chart taller
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        try:
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"图表渲染错误: {str(e)}")
            st.info("请尝试调整输入参数或刷新页面。")
    
    with col2:
        # Expense Breakdown
        st.subheader("支出明细")
        
        # Group by year and calculate averages
        yearly_expenses = df.groupby('Year').agg({
            'MonthlyMortgage': 'mean',
            'MonthlyExpenses': 'mean',
            'MonthlyChildExpenses': 'mean',
            'TotalEducationExpenses': 'mean',
            'MonthlyInsurance': 'mean',
            'MonthlyTax': 'mean',
            'OneTimeExpenses': 'sum'
        }).reset_index()
        
        # Create a copy of the dataframe for the chart that excludes housing one-time expenses
        chart_expenses = yearly_expenses.copy()
        
        # If housing columns exist, exclude housing one-time expenses from the chart
        if 'HousingDownPayment' in df.columns and 'HousingTaxesFees' in df.columns:
            # Calculate housing expenses by year
            housing_expenses = df.groupby('Year').agg({
                'HousingDownPayment': 'sum',
                'HousingTaxesFees': 'sum'
            }).reset_index()
            
            # Subtract housing expenses from one-time expenses for the chart
            for idx, row in housing_expenses.iterrows():
                year = row['Year']
                housing_total = row['HousingDownPayment'] + row['HousingTaxesFees']
                if housing_total > 0:
                    year_idx = chart_expenses[chart_expenses['Year'] == year].index
                    if len(year_idx) > 0:
                        chart_expenses.loc[year_idx, 'OneTimeExpenses'] -= housing_total
        
        # Create a stacked bar chart
        expense_categories = [
            'MonthlyMortgage', 'MonthlyExpenses', 'MonthlyChildExpenses',
            'TotalEducationExpenses', 'MonthlyInsurance', 'MonthlyTax', 'OneTimeExpenses'
        ]
        
        category_names = {
            'MonthlyMortgage': '房贷',
            'MonthlyExpenses': '常规支出',
            'MonthlyChildExpenses': '小孩支出',
            'TotalEducationExpenses': '教育支出',
            'MonthlyInsurance': '保险',
            'MonthlyTax': '税款',
            'OneTimeExpenses': '一次性支出'
        }
        
        fig2 = go.Figure()
        
        for category in expense_categories:
            fig2.add_trace(go.Bar(
                x=chart_expenses['Year'],
                y=chart_expenses[category],
                name=category_names[category]
            ))
        
        fig2.update_layout(
            barmode='stack',
            xaxis_title='年份',
            yaxis_title='平均月支出 (SGD)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Child expenses over time
        st.subheader("小孩相关支出随时间变化")
        
        # Create a line chart for child expenses
        fig4 = go.Figure()
        
        # Regular child expenses
        fig4.add_trace(go.Scatter(
            x=df.index,
            y=df['MonthlyChildExpenses'],
            name='常规支出',
            line=dict(color='purple', width=2)
        ))
        
        # Education expenses
        fig4.add_trace(go.Scatter(
            x=df.index,
            y=df['TotalEducationExpenses'],
            name='教育支出',
            line=dict(color='orange', width=2)
        ))
        
        # One-time expenses
        fig4.add_trace(go.Scatter(
            x=df.index,
            y=df['OneTimeExpenses'],
            name='一次性支出',
            mode='markers',
            marker=dict(size=10, color='red')
        ))
        
        fig4.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Add a new chart showing asset composition over time if housing is included
        if housing_status in ["已购房", "计划购房"]:
            st.subheader("资产构成随时间变化")
            
            # Create a stacked area chart for asset composition
            fig7 = go.Figure()
            
            # Add savings area
            fig7.add_trace(go.Scatter(
                x=df.index,
                y=df['CumulativeSavings'],
                name='现金储蓄',
                mode='lines',
                line=dict(width=0),
                fill='tozeroy',
                stackgroup='assets'
            ))
            
            # Add property equity area
            fig7.add_trace(go.Scatter(
                x=df.index,
                y=df['PropertyEquity'],
                name='房产净值',
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                stackgroup='assets'
            ))
            
            fig7.update_layout(
                xaxis_title='日期',
                yaxis_title='金额 (SGD)',
                height=400,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig7, use_container_width=True)
            
            # Add a pie chart showing final asset composition
            st.subheader("最终资产构成")
            
            final_savings = df['CumulativeSavings'].iloc[-1]
            final_property_equity = df['PropertyEquity'].iloc[-1]
            
            asset_labels = ['现金储蓄', '房产净值']
            asset_values = [final_savings, final_property_equity]
            
            fig8 = px.pie(
                values=asset_values,
                names=asset_labels,
                title=f"6年后资产构成 (总计: ${final_savings + final_property_equity:,.2f})"
            )
            fig8.update_traces(textposition='inside', textinfo='percent+label+value')
            fig8.update_layout(height=300)
            
            st.plotly_chart(fig8, use_container_width=True)

        # Add a new chart showing monthly cash flow
        st.subheader("月度现金流")
        
        fig_cashflow = go.Figure()
        
        # Add income line
        fig_cashflow.add_trace(go.Scatter(
            x=date_strings,  # Use string format
            y=df['MonthlyIncome'] + df['Bonus'],
            name='总收入',
            line=dict(color='green', width=2)
        ))
        
        # Add expenses line
        fig_cashflow.add_trace(go.Scatter(
            x=date_strings,  # Use string format
            y=df['TotalMonthlyExpenses'],
            name='总支出',
            line=dict(color='red', width=2)
        ))
        
        # Add monthly savings line
        fig_cashflow.add_trace(go.Scatter(
            x=date_strings,  # Use string format
            y=df['MonthlySavings'],
            name='月度储蓄',
            line=dict(color='blue', width=2)
        ))
        
        # Add a horizontal line at zero
        fig_cashflow.add_shape(
            type="line",
            x0=date_strings[0],
            y0=0,
            x1=date_strings[-1],
            y1=0,
            line=dict(color="black", width=1, dash="dash")
        )
        
        # Add markers for significant one-time expenses
        if 'expense_df' in locals():
            for _, expense in expense_df.iterrows():
                expense_month = expense['date'].replace(day=1)
                if expense_month in df.index:
                    expense_idx = df.index.get_loc(expense_month)
                    expense_month_str = expense_month.strftime('%Y-%m-%d')
                    savings_at_expense = df['MonthlySavings'].iloc[expense_idx]
                    
                    # Add marker for large expenses (over 5000)
                    if expense['amount'] > 5000:
                        fig_cashflow.add_trace(go.Scatter(
                            x=[expense_month_str],
                            y=[savings_at_expense],
                            name=expense['name'],
                            mode='markers',
                            marker=dict(size=10, color='red', symbol='x')
                        ))
        
        fig_cashflow.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        try:
            st.plotly_chart(fig_cashflow, use_container_width=True)
        except Exception as e:
            st.error(f"图表渲染错误: {str(e)}")
            st.info("请尝试调整输入参数或刷新页面。")

# Footer
st.markdown("---")
st.markdown("© 2025 Singapore Family Finance Planner Done By Shihao | 此应用仅供参考，不构成财务建议") 