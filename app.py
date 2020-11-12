import datetime
from functools import reduce
from pkg_resources import normalize_path
import streamlit as st
import pandas as pd
import altair as alt
import os
 

try:
    from app_secrets import MINIO_ACCESS_KEY, MINIO_ENCRYPT_KEY
except:
    access_key=os.getenv("MINIO_ACCESS_KEY")
    secret_key=os.getenv("MINIO_SECRET_KEY")

# numbers for 2019
inhabitants = {'Germany': 83.16,
            'France': 67.2,
            'United Kingdom': 67.1,
            'Italy': 60.23,
            'Spain': 47.05,
            'Poland': 37.97,
            'Romania': 19.28,
            'Netherlands': 17.34,
            'Belgium': 11.49,
            'Greece': 10.69,
            'Sweden': 10.15, 
            'Switzerland': 8.57,
            'Austria': 8.91,
            'Norway': 5.36,
            'Denmark': 5.77}

# invalidate cache every 1h so user gets new data without resetting cache in the hamburger menue 
@st.cache(ttl=60*60*1)
def read_data():
    BASEURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"    
    url_confirmed = f"{BASEURL}/time_series_covid19_confirmed_global.csv"
    url_deaths = f"{BASEURL}/time_series_covid19_deaths_global.csv"
    url_recovered = f"{BASEURL}/time_series_covid19_recovered_global.csv"

    confirmed = pd.read_csv(url_confirmed, index_col=0)
    deaths = pd.read_csv(url_deaths, index_col=0)
    recovered = pd.read_csv(url_recovered, index_col=0)

    # sum over potentially duplicate rows (France and their territories)
    confirmed = confirmed.groupby("Country/Region").sum().reset_index()
    deaths = deaths.groupby("Country/Region").sum().reset_index()
    recovered = recovered.groupby("Country/Region").sum().reset_index()


    return (confirmed, deaths, recovered)

def transform(df, collabel='confirmed', norm=False):
    dfm = pd.melt(df)
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["value"]]
    dfm.columns = [collabel]
    if norm:
        dfm[[collabel]] = dfm[[collabel]] / (inhabitants[norm]* 1_000_000) * 100_000
    return dfm

def transform2(df, collabel='confirmed'):
    dfm = pd.melt(df, id_vars=["Country/Region"])
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["Country/Region","value"]]
    dfm.columns = ["country", collabel]
    return dfm

def main():
    st.set_page_config(page_title="Covid-19", page_icon=None, layout='centered', initial_sidebar_state='auto')
    st.title("🦠 Covid-19 Data Explorer")
    st.markdown("""\
        This app illustrates the spread of COVID-19 in select countries of Europe over time.
    """)

    #st.error("⚠️ There is currently an issue in the datasource of JHU. Data for 03/13 is invalid and thus removed!")

    countries = ["Germany", "Austria", "Belgium", "Denmark", "France", "Greece", "Italy", \
                 "Netherlands", "Norway", "Poland", "Romania", "Spain", "Sweden", \
                 "Switzerland", "United Kingdom"]

    analysis = st.sidebar.selectbox("Choose Analysis", ["Overview", "By Country"])

    if analysis == "Overview":

        st.header("COVID-19 cases and fatality rate in Europe")
        st.markdown("""\
            These are the reported case numbers for a selection of european countries"""
            f""" (currently only {', '.join(countries)}). """
            """The case fatality rate (CFR) is calculated as:  
            $$
            CFR[\%] = \\frac{fatalities}{\\textit{all cases}}
            $$

            ℹ️ You can select/ deselect countries and switch between linear and log scales.
            """)

        confirmed, deaths, recovered = read_data()

        multiselection = st.multiselect("Select countries:", countries, default=countries)
        logscale = st.checkbox("Log scale", False)

        confirmed = confirmed[confirmed["Country/Region"].isin(multiselection)]
        confirmed = confirmed.drop(["Lat", "Long"],axis=1)
        confirmed = transform2(confirmed, collabel="confirmed")

        deaths = deaths[deaths["Country/Region"].isin(multiselection)]
        deaths = deaths.drop(["Lat", "Long"],axis=1)
        deaths = transform2(deaths, collabel="deaths")

        frate = confirmed[["country"]]
        frate["frate"] = (deaths.deaths / confirmed.confirmed)*100

        # saveguard for empty selection 
        if len(multiselection) == 0:
            return 

        SCALE = alt.Scale(type='linear')
        if logscale:
            confirmed["confirmed"] += 0.00001

            confirmed = confirmed[confirmed.index > '2020-02-16']
            frate = frate[frate.index > '2020-02-16']
            
            SCALE = alt.Scale(type='log', domain=[10, int(max(confirmed.confirmed))], clamp=True)


        c2 = alt.Chart(confirmed.reset_index()).properties(height=150).mark_line().encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("confirmed:Q", title="Cases", scale=SCALE),
            color=alt.Color('country:N', title="Country")
        )

        # case fatality rate...
        c3 = alt.Chart(frate.reset_index()).properties(height=100).mark_line().encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("frate:Q", title="Fatality rate [%]", scale=alt.Scale(type='linear')),
            color=alt.Color('country:N', title="Country")
        )

        per100k = confirmed.loc[[confirmed.index.max()]].copy()
        per100k.loc[:,'inhabitants'] = per100k.apply(lambda x: inhabitants[x['country']], axis=1)
        per100k.loc[:,'per100k'] = per100k.confirmed / (per100k.inhabitants * 1_000_000) * 100_000
        per100k = per100k.set_index("country")
        per100k = per100k.sort_values(ascending=False, by='per100k')
        per100k.loc[:,'per100k'] = per100k.per100k.round(2)

        c4 = alt.Chart(per100k.reset_index()).properties(width=75).mark_bar().encode(
            x=alt.X("per100k:Q", title="Cases per 100k inhabitants"),
            y=alt.Y("country:N", title="Countries", sort=None),
            color=alt.Color('country:N', title="Country"),
            tooltip=[alt.Tooltip('country:N', title='Country'), 
                     alt.Tooltip('per100k:Q', title='Cases per 100k'),
                     alt.Tooltip('inhabitants:Q', title='Inhabitants [mio]')]
        )

        st.altair_chart(alt.hconcat(c4, alt.vconcat(c2, c3)), use_container_width=True)

        st.markdown(f"""\
            <div style="font-size: small">
            ⚠️ Please take the CFR with a grain of salt. The ratio is 
            highly dependend on the total number of tests conducted in a country. In the early stages
            of the outbreak often mainly severe cases with clear symptoms are detected. Thus mild cases
            are not recorded which skews the CFR.
            </div><br/>  

            """, unsafe_allow_html=True)


    elif analysis == "By Country":        

        confirmed, deaths, recovered = read_data()

        st.header("Country statistics")
        st.markdown("""\
            The reported number of active, recovered and deceased COVID-19 cases by country """
            f""" (currently only {', '.join(countries)}).  
            """
            """  
            ℹ️ You can select countries and plot data as cummulative counts or new active cases per day.
            Normalize scales the values to counts per 100k inhabitants. 
            """)

        # selections
        col1, col2, col3, _, _ = st.beta_columns(5)

        selection = col1.selectbox("Select country:", countries)
        cummulative = col2.radio("Display type:", ["total", "new cases"])
        norm_sel = col3.radio("Normalize:", ["no", "yes"])
        normalize = selection if norm_sel == "yes" else False
        
        confirmed = confirmed[confirmed["Country/Region"] == selection].iloc[:,3:]
        confirmed = transform(confirmed, collabel="confirmed", norm=normalize)

        deaths = deaths[deaths["Country/Region"] == selection].iloc[:,3:]
        deaths = transform(deaths, collabel="deaths", norm=normalize)

        recovered = recovered[recovered["Country/Region"] == selection].iloc[:,3:]
        recovered = transform(recovered, collabel="recovered", norm=normalize)

        
        df = reduce(lambda a,b: pd.merge(a,b, on='date'), [confirmed, recovered, deaths])
        df["active"] = df.confirmed - (df.deaths + df.recovered)

        variables = ["recovered", "active", "deaths"]
        colors = ["steelblue", "orange", "black"]

        value_vars = variables
        SCALE = alt.Scale(domain=variables, range=colors)
        if cummulative == 'new cases':
            value_vars = ["new"]
            df["new"] = df.confirmed - df.shift(1).confirmed
            df["new"].loc[df.new < 0]  = 0
            SCALE = alt.Scale(domain=["new"], range=["orange"]) 

        dfm = pd.melt(df.reset_index(), id_vars=["date"], value_vars=value_vars)

        # introduce order col as altair does auto-sort on stacked elements
        dfm['order'] = dfm['variable'].replace(
            {val: i for i, val in enumerate(variables[::-1])}
        )

        cases_label = "Cases" if normalize == False else "Cases per 100k"

        c = alt.Chart(dfm.reset_index()).mark_bar().properties(height=200).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("sum(value):Q", title=cases_label, scale=alt.Scale(type='linear')),
            color=alt.Color('variable:N', title="Category", scale=SCALE), #, sort=alt.EncodingSortField('value', order='ascending')),
            order='order'
        )

        if cummulative != 'new cases':
            st.altair_chart(c, use_container_width=True)
        else:
            # add smooth 7-day trend
            rm_7day = df[['new']].rolling('7D').mean().rename(columns={'new': 'value'})
            c_7day = alt.Chart(rm_7day.reset_index()).properties(height=200).mark_line(strokeDash=[1,1], color='red').encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("value:Q", title=cases_label, scale=alt.Scale(type='linear')),
            )
            st.altair_chart((c + c_7day), use_container_width=True)
            st.markdown(f"""\
                <div style="font-size: small">Daily reported new cases (incl. 7-day average).</div><br/>
                """, unsafe_allow_html=True)


    st.info("""\
          
        by: [C. Werner](https://www.christianwerner.net) | source: [GitHub](https://www.github.com/cwerner/covid19)
        | data source: [Johns Hopkins Univerity (GitHub)](https://github.com/CSSEGISandData/COVID-19). 
    """)


    # ----------------------








if __name__ == "__main__":
    main()
