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


import pandas as pd

@st.cache
def read_data():
    BASEURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"    
    url_confirmed = f"{BASEURL}/time_series_19-covid-Confirmed.csv"
    url_deaths = f"{BASEURL}/time_series_19-covid-Deaths.csv"
    url_recovered = f"{BASEURL}/time_series_19-covid-Recovered.csv"

    confirmed = pd.read_csv(url_confirmed, index_col=0)
    deaths = pd.read_csv(url_deaths, index_col=0)
    recovered = pd.read_csv(url_recovered, index_col=0)
    return (confirmed, deaths, recovered)

def transform(df, collabel='confirmed'):
    dfm = pd.melt(df)
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["value"]]
    dfm.columns = [collabel]
    return dfm

def transform2(df, collabel='confirmed'):
    dfm = pd.melt(df, id_vars=["Country/Region"])
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["Country/Region","value"]]
    dfm.columns = ["country", collabel]
    return dfm

def main():
    st.title("🦠 Covid-19 Data Explorer")
    st.markdown("""\
        This app illustrates the spread of COVID-19 in select countries over time.
        Data is ingested from [Johns Hopkins Univerity, Center for System Science & Engineering (GitHub)](https://github.com/CSSEGISandData/COVID-19).
        Due to the situation changing rapidly data might be out of date. Please consult your governmental organizations information sites for thorough advice. This
        page is merely a data visualization exercise!  
    """)

    countries = ["Germany", "Austria", "Belgium", "France", "Greece", "Italy", "Netherlands", "Norway", "Spain", "Sweden", "Switzerland", "UK"]

    analysis = st.sidebar.selectbox("Analysis", ["Overview", "By Country"])


    if analysis == "Overview":

        confirmed, deaths, recovered = read_data()

        multiselection = st.multiselect("Select countries:", countries, default=["Germany", "France", "Italy"])

        confirmed = confirmed[confirmed["Country/Region"].isin(multiselection)]
        confirmed = confirmed.drop(["Lat", "Long"],axis=1)
        confirmed = transform2(confirmed, collabel="confirmed")

        deaths = deaths[deaths["Country/Region"].isin(multiselection)]
        deaths = deaths.drop(["Lat", "Long"],axis=1)
        deaths = transform2(deaths, collabel="deaths")

        frate = confirmed[["country"]]
        frate["frate"] = (deaths.deaths / confirmed.confirmed)*100

        st.subheader("Confirmed cases and fatality rate in Europe [*]")

        c2 = alt.Chart(confirmed.reset_index()).properties(height=150).mark_line().encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("confirmed:Q", title="Cases", scale=alt.Scale(type='linear')),
            color=alt.Color('country:N', title="Country")
        )

        # case fatality rate...
        c3 = alt.Chart(frate.reset_index()).properties(height=100).mark_line().encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("frate:Q", title="Fatality rate [%]", scale=alt.Scale(type='linear')),
            color=alt.Color('country:N', title="Country")
        )
        st.altair_chart(alt.vconcat(c2, c3), use_container_width=True)

        st.markdown(f"""\
            <div style="font-size: small">
            [*] Note: Currently only the following countries are provided: {', '.join(countries)}.
            Also, please take the fatality rate with a grain of salt since this number is 
            highly dependend on the total number of tests conducted in the country.
            </div>
            """, unsafe_allow_html=True)

    elif analysis == "By Country":        

        confirmed, deaths, recovered = read_data()

        st.subheader("Country statistics")

        # selections
        selection = st.selectbox("Select country:", countries)
        cummulative = st.radio("Display type:", ["total", "new cases"])
        #scaletransform = st.radio("Plot y-axis", ["linear", "pow"])
        
        confirmed = confirmed[confirmed["Country/Region"] == selection].iloc[:,3:]
        confirmed = transform(confirmed, collabel="confirmed")

        deaths = deaths[deaths["Country/Region"] == selection].iloc[:,3:]
        deaths = transform(deaths, collabel="deaths")

        recovered = recovered[recovered["Country/Region"] == selection].iloc[:,3:]
        recovered = transform(recovered, collabel="recovered")

        variables = ["active", "deaths", "recovered"]

        df = pd.concat([confirmed, deaths, recovered], axis=1)
        df["active"] = df.confirmed - df.deaths - df.recovered

        if cummulative == 'new cases':
            df = df.diff()

        dfm = pd.melt(df.reset_index(), id_vars=["date"], value_vars=variables)
        
        colors = ["orange", "purple", "gray"]

        brush = alt.selection(type='interval', encodings=['x'])

        c = alt.Chart(dfm.reset_index()).properties(height=200).mark_bar(size=10).encode(
            x=alt.X("date:T", title="Date", scale=alt.Scale(type='linear')),
            y=alt.Y("value:Q", title="Cases", scale=alt.Scale(type='linear')),
            color=alt.Color('variable:N', title="Category", scale=alt.Scale(domain=variables, range=colors))
        )
        # ).add_selection(
        #     brush
        # )
        st.altair_chart(c, use_container_width=True)

        st.markdown(f"""\
            <div style="font-size: small">
            [*] Note: Currently only the following countries are provided: {', '.join(countries)}.
            </div>  

            """, unsafe_allow_html=True)

    st.info("""\
          
        by: [C. Werner](https://www.christianwerner.net) | source: [GitHub](https://www.github.com/cwerner/covid19)  
    """)



    # ----------------------








if __name__ == "__main__":
    main()
