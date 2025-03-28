"""
Cell distribution component for displaying cell population distributions
"""

import streamlit as st
from visualizations.charts import create_cell_distribution_treemap

def display_cell_distribution(df, input_cells):
    """Display the cell distribution view"""
    st.subheader("Cell Distribution")
    
    # Create and display the treemap
    fig = create_cell_distribution_treemap(df, input_cells)
    st.plotly_chart(fig, use_container_width=True) 