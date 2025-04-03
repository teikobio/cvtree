"""
Table view component for displaying cell counts and CV data
"""

import streamlit as st
import pandas as pd

def display_table_view(df, input_cells):
    """Display the table view with cell counts and CV data"""
    st.subheader("Estimated Cell Counts and CV")
    
    # Filter control - only max CV
    max_cv = st.slider("Maximum CV (%)", 0.0, 50.0, 50.0, help="Filter to show only populations with CV below this value")
    
    # Apply filter
    filtered_df = df[df["CV Value"] <= max_cv].sort_values(by="CV Value")
    
    # Display columns needed for the table view
    display_df = filtered_df[["Population", "Parent", "Cell Count", "% of Parent", "CV (%)", "CV Quality"]]
    
    st.dataframe(display_df, use_container_width=True)
    
    # Allow downloading as CSV
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"cell_counts_{input_cells/1000:.0f}K.csv",
        mime="text/csv"
    ) 