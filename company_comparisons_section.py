
import streamlit as st
import pandas as pd
import sqlite3

# Connect to DB
conn = sqlite3.connect("industry_activities_v2.db")

st.title("🧩 مقارنات بين شركات مجموعة المديفر")

# Load combined company-level3 data (this will be built-in in full app)
@st.cache_data
def load_company_activities():
    df_all = pd.read_csv("company_level3_all.csv")
    return df_all

df = load_company_activities()

tab1, tab2 = st.tabs(["📋 الأنشطة المشتركة", "🔎 بحث عن الشركات حسب النشاط"])

with tab1:
    st.subheader("📌 الأنشطة المشتركة بين شركتين أو أكثر")

    grouped = df.groupby("رمز النشاط")["company"].unique().reset_index()
    shared = grouped[grouped["company"].apply(lambda x: len(x) > 1)]
    shared.columns = ["رمز النشاط", "الشركات المرتبطة"]

    st.dataframe(shared)

with tab2:
    st.subheader("🔍 اختر رمز نشاط أو جزء من اسمه")

    activity_input = st.text_input("اكتب رمز النشاط أو جزء من اسمه")

    if activity_input:
        activity_filtered = df[
            df["رمز النشاط"].astype(str).str.contains(activity_input) |
            df["اسم النشاط"].str.contains(activity_input, case=False, na=False)
        ]
        st.dataframe(activity_filtered[["رمز النشاط", "اسم النشاط", "company"]])
