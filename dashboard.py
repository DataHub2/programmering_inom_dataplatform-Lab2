import streamlit as st

pg = st.navigation([
    st.Page("pages/partioversikt.py", title="Partiöversikt", default=True),
])
pg.run()

