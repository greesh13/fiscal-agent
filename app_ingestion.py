import streamlit as st
import pandas as pd
import fitz  # PyMuPDF for PDF reading
import plotly.express as px
import openai
import os

st.set_page_config(page_title="💸 Financial Sanity Agent", layout="wide")

# Add your OpenAI API key securely
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

# Sidebar navigation
st.sidebar.title("💸 Financial Sanity Agent")
user_role = st.sidebar.selectbox("Who are you?", ["Student", "Working Professional", "Parent"])

# Tabbed navigation
tab1, tab2, tab3 = st.tabs(["📁 Upload Documents", "📊 Budget Insights", "🎯 Financial Goals"])

# Session state
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "category_limits" not in st.session_state:
    st.session_state.category_limits = {}

# 📁 Upload Documents Page
with tab1:
    st.title("📁 Upload Your Financial Files")
    st.markdown("Upload your latest paystub and transaction history to begin your financial analysis.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Paystub PDF")
        uploaded_pdf = st.file_uploader("Upload Paystub", type="pdf")
        if uploaded_pdf:
            try:
                pdf_text = ""
                with fitz.open(stream=uploaded_pdf.read(), filetype="pdf") as doc:
                    for page in doc:
                        pdf_text += page.get_text()
                st.session_state.pdf_text = pdf_text
                st.success("✅ Paystub uploaded.")
                st.text_area("Extracted Paystub Text", value=pdf_text, height=200)
            except Exception as e:
                st.error(f"⚠️ Error reading PDF: {e}")

    with col2:
        st.subheader("📊 Bank CSV")
        uploaded_csv = st.file_uploader("Upload CSV", type="csv")
        if uploaded_csv:
            try:
                raw_df = pd.read_csv(uploaded_csv)
                raw_df = raw_df.dropna(subset=['Amount', 'Date'])
                raw_df['Amount'] = pd.to_numeric(raw_df['Amount'], errors='coerce')
                raw_df = raw_df.dropna(subset=['Amount'])
                raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
                raw_df = raw_df.dropna(subset=['Date'])
                raw_df['Month'] = raw_df['Date'].dt.to_period('M').dt.to_timestamp()
                df = raw_df[raw_df['Amount'] < 0].copy()
                df['Amount'] = df['Amount'].abs()
                st.session_state.df = df
                st.success("✅ Transactions uploaded.")
                st.dataframe(df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"⚠️ Error reading CSV: {e}")

    st.subheader("📊 Set Your Category Limits")
    categories = ["Rent", "Groceries", "Transport", "Dining", "Subscriptions", "Education", "Miscellaneous", "Shopping"]
    for cat in categories:
        st.session_state.category_limits[cat] = st.number_input(f"{cat} Budget Limit", min_value=0, value=300)

# 📊 Budget Insights Page
with tab2:
    st.title("📊 Budget Insights")
    st.markdown("Your financial health, visualized and optimized like a pro money consultant.")

    if st.session_state.df.empty:
        st.warning("Please upload your transaction CSV first.")
    else:
        df = st.session_state.df
        st.metric("💳 Total Spending", f"${df['Amount'].sum():,.2f}")

        st.subheader("📈 Monthly Spending Overview")
        monthly_spend = df.groupby('Month')['Amount'].sum().reset_index()
        fig = px.line(monthly_spend, x='Month', y='Amount', title='Monthly Spending Trend')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔍 Smart Spending Analysis")
        for _, row in monthly_spend.iterrows():
            month = row['Month'].strftime("%B %Y")
            amount = row['Amount']
            if amount > 2000:
                st.warning(f"{month}: ⚠️ High spending of ${amount:.2f}. Cut dining or subscriptions.")
            elif amount > 1500:
                st.info(f"{month}: 👍 Moderate spending at ${amount:.2f}. Consider carpooling or cooking.")
            else:
                st.success(f"{month}: 🎯 Excellent! You spent only ${amount:.2f}.")

        st.subheader("💥 High-Spend Categories")
        if 'Category' in df.columns:
            cat_spend = df.groupby('Category')['Amount'].sum().reset_index()
            st.bar_chart(cat_spend.set_index("Category"))

            for _, row in cat_spend.iterrows():
                cat = row['Category']
                amt = row['Amount']
                limit = st.session_state.category_limits.get(cat, 300)
                if amt > limit:
                    st.warning(f"⚠️ Overspent in {cat}: ${amt:.2f} (Limit: ${limit:.2f})")

# 🎯 Financial Goals Page
with tab3:
    st.title("🎯 Set Your Financial Goals")
    st.markdown("Build your money tree. Set consistent, realistic, and smart financial targets.")

    if user_role == "Student":
        tuition = st.number_input("🎓 Monthly Tuition Savings Goal", min_value=0, value=500)
        books = st.number_input("📚 Books & Materials Goal", min_value=0, value=100)
        custom = st.text_input("✍️ Custom Goal")
        custom_val = st.number_input("💰 Custom Goal Amount", min_value=0, value=0)
        total = tuition + books + custom_val
        st.success(f"📘 You aim to save ${total} monthly to graduate debt-free.")

    elif user_role == "Working Professional":
        retirement = st.number_input("🏖 Retirement Savings Goal", min_value=0, value=700)
        emergency = st.number_input("🚨 Emergency Fund Goal", min_value=0, value=300)
        custom = st.text_input("✍️ Custom Goal")
        custom_val = st.number_input("💰 Custom Goal Amount", min_value=0, value=0)
        total = retirement + emergency + custom_val
        st.success(f"💸 You aim to save ${total} monthly for your financial runway.")

    elif user_role == "Parent":
        child_fund = st.number_input("👶 Child Education Fund Goal", min_value=0, value=400)
        gold = st.number_input("🥇 Gold Savings for Daughter Goal", min_value=0, value=200)
        custom = st.text_input("✍️ Custom Goal")
        custom_val = st.number_input("💰 Custom Goal Amount", min_value=0, value=0)
        total = child_fund + gold + custom_val
        st.success(f"👨‍👩‍👧 You aim to save ${total} monthly for your family’s legacy.")
