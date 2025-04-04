"""
CV analysis component for displaying CV-related visualizations and insights
"""

import streamlit as st
import pandas as pd
from visualizations.charts import create_cv_bar_chart

def display_cv_analysis(df, db):
    """Display the CV analysis view"""
    st.subheader("CV Analysis")
    
    # Sort all populations by CV Value
    sorted_df = df.sort_values(by="CV Value")
    
    # Create and display the CV bar chart
    fig = create_cv_bar_chart(sorted_df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show table of populations with poor CV
    st.subheader("Populations with Higher CV (>10%)")
    high_cv_df = df[df["CV Value"] > 10].sort_values(by="CV Value", ascending=False)
    
    if not high_cv_df.empty:
        st.dataframe(high_cv_df[["Population", "Cell Count", "% of Parent", "CV (%)", "CV Quality"]])
        
        st.info("""
        💡 **Tip:** Populations with high CV values may have unreliable measurements. 
        Consider increasing the total input cells or pooling samples if precise measurements 
        of these populations are important.
        """)
    else:
        st.success("No populations with CV >10% found with current input cells") 