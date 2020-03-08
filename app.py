import pydeck as pdk
import streamlit as st
import pandas as pd
import altair as alt
import os

try:
    from app_secrets import MINIO_ACCESS_KEY, MINIO_ENCRYPT_KEY
except:
    access_key=os.getenv("MINIO_ACCESS_KEY")
    secret_key=os.getenv("MINIO_SECRET_KEY")


def main():
    st.title("Covid-19 Data Explorer")
    st.markdown("""\
        This app illustrates the spread of COVID-19 in select countries and regions over time.
        Data is ingested from JHU (global) and RKI (Germany). Note, due to the situation changing
        rapidly data might be out of date.  
        Please consult your governmental organizations information sites for thorough advice. This
        page is merly a data visualization exercise!  
        """)


if __name__ == "__main__":
    main()
