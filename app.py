import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# ============= PAGE CONFIG =================
st.set_page_config(
    page_title="CORD-19 Interactive Explorer",
    layout="wide"
)

# ============= DATA LOADING =================
@st.cache_data
def load_data():
    df = pd.read_csv("metadata_cleaned.csv", low_memory=False)
    if 'publish_time' in df.columns:
        df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
        df['year'] = df['publish_time'].dt.year
    return df

df = load_data()

st.title("📊 CORD-19 Interactive Explorer")
st.markdown("""
Explore the **cleaned CORD-19 dataset**.  
Use the sidebar filters or search box to narrow results and update the visualizations in real time.
""")

# ============= SIDEBAR FILTERS ==============
st.sidebar.header("🔧 Filters")

# Search keyword
search_term = st.sidebar.text_input("🔍 Search in title or abstract")

# Year range slider
if "year" in df.columns:
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    year_range = st.sidebar.slider("Select Year Range",
                                   min_value=min_year,
                                   max_value=max_year,
                                   value=(min_year, max_year))
else:
    year_range = (None, None)

# Journal multiselect
journals = st.sidebar.multiselect(
    "Select Journals",
    options=sorted(df['journal'].dropna().unique())
)

# ============= DATA FILTERING ===============
filtered = df.copy()

# Apply keyword filter
if search_term:
    mask = (
        df['title'].str.contains(search_term, case=False, na=False) |
        df['abstract'].str.contains(search_term, case=False, na=False)
    )
    filtered = filtered[mask]

# Apply year filter
if "year" in filtered.columns:
    filtered = filtered[
        (filtered['year'] >= year_range[0]) &
        (filtered['year'] <= year_range[1])
    ]

# Apply journal filter
if journals:
    filtered = filtered[filtered['journal'].isin(journals)]

st.success(f"Showing **{len(filtered):,}** papers after applying filters.")

# ============= DATA PREVIEW =================
st.subheader("📑 Sample of Filtered Data")
st.dataframe(filtered.head(20))

# ============= VISUALIZATIONS ===============
col1, col2 = st.columns(2)

with col1:
    st.subheader("Publications Per Year")
    if "year" in filtered.columns and not filtered.empty:
        fig, ax = plt.subplots(figsize=(6,4))
        sns.countplot(data=filtered, x="year",
                      order=sorted(filtered["year"].dropna().unique()),
                      color="skyblue")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("No data to display for Year chart.")

with col2:
    st.subheader("Top Publishing Journals")
    if not filtered.empty:
        top_journals = filtered['journal'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(6,4))
        sns.barplot(y=top_journals.index, x=top_journals.values,
                    palette="viridis", ax=ax)
        ax.set_xlabel("Number of Papers")
        st.pyplot(fig)
    else:
        st.info("No data to display for Journals chart.")

st.subheader("Word Cloud of Filtered Titles")
if not filtered.empty:
    all_titles = " ".join(filtered["title"].dropna())
    if all_titles.strip():
        wc = WordCloud(width=1000, height=400, background_color="white").generate(all_titles)
        fig_wc, ax_wc = plt.subplots(figsize=(10,4))
        ax_wc.imshow(wc, interpolation="bilinear")
        ax_wc.axis("off")
        st.pyplot(fig_wc)
    else:
        st.info("No titles available to generate a word cloud.")
else:
    st.info("No data to display for Word Cloud.")

# ============= DOWNLOAD BUTTON ==============
st.download_button(
    label="💾 Download Filtered Data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="cord19_filtered.csv",
    mime="text/csv"
)
