import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

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
    
    # Monthly income and expenses
    st.subheader("月度收入与支出")
    monthly_income = st.number_input("月收入 (SGD)", min_value=0.0, value=5000.0, step=100.0)
    monthly_mortgage = st.number_input("月房贷 (SGD)", min_value=0.0, value=1500.0, step=100.0)
    monthly_expenses = st.number_input("月常规支出 (SGD)", min_value=0.0, value=2000.0, step=100.0)
    monthly_child_expenses = st.number_input("月小孩常规支出 (SGD)", min_value=0.0, value=500.0, step=100.0)
    
    # Annual expenses
    st.subheader("年度支出")
    annual_insurance = st.number_input("年度保险 (SGD)", min_value=0.0, value=2000.0, step=100.0)
    annual_tax = st.number_input("年度税款 (SGD)", min_value=0.0, value=3000.0, step=100.0)
    annual_bonus = st.number_input("年度奖金 (SGD)", min_value=0.0, value=10000.0, step=500.0)
    
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
        child_birth_date = st.date_input("计划生育日期", value=datetime.now() + timedelta(days=365))

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
    df['MonthlyMortgage'] = monthly_mortgage
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
                                              ["产检费用", "生育费用", "坐月子费用", "教育费用", "其他"])
            
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
    df['CumulativeSavings'] = df['MonthlySavings'].cumsum()
    
    # Display the financial projection table
    st.subheader("月度财务预测")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_columns = [
        'Year', 'MonthName', 'MonthlyIncome', 'Bonus', 'MonthlyMortgage', 
        'MonthlyExpenses', 'MonthlyChildExpenses', 'TotalEducationExpenses',
        'OneTimeExpenses', 'TotalMonthlyExpenses', 'MonthlySavings', 'CumulativeSavings'
    ]
    
    display_df = display_df[display_columns]
    display_df.columns = [
        '年份', '月份', '月收入', '奖金', '房贷', 
        '常规支出', '小孩支出', '教育支出',
        '一次性支出', '总支出', '月度储蓄', '累计储蓄'
    ]
    
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
        # Monthly Income vs Expenses
        st.subheader("月度收入与支出")
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df.index, 
            y=df['MonthlyIncome'] + df['Bonus'],
            name='总收入',
            line=dict(color='green', width=2)
        ))
        fig1.add_trace(go.Scatter(
            x=df.index, 
            y=df['TotalMonthlyExpenses'],
            name='总支出',
            line=dict(color='red', width=2)
        ))
        fig1.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Cumulative Savings
        st.subheader("累计储蓄")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df.index, 
            y=df['CumulativeSavings'],
            name='累计储蓄',
            line=dict(color='blue', width=3),
            fill='tozeroy'
        ))
        fig3.update_layout(
            xaxis_title='日期',
            yaxis_title='金额 (SGD)',
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)
    
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
                x=yearly_expenses['Year'],
                y=yearly_expenses[category],
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

# Footer
st.markdown("---")
st.markdown("© 2023 Singapore Family Finance Planner | 此应用仅供参考，不构成财务建议") 