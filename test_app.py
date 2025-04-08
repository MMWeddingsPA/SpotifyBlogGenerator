import streamlit as st

st.title("Test Application")
st.write("This is a simple test to see if Streamlit works correctly.")

# Basic button interaction
if st.button("Click Me"):
    st.success("Button clicked!")

# Show some example data
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'A': np.random.randn(5),
    'B': np.random.randn(5)
})

st.dataframe(df)