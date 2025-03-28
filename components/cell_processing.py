"""
Cell processing component for displaying processing steps and efficiency metrics
"""

import streamlit as st
import pandas as pd
from visualizations.charts import create_processing_waterfall_chart, create_retention_gauge
from config.settings import PROCESSING_STEPS

def display_cell_processing(cell_counts_waterfall, starting_cells):
    """Display the cell processing view"""
    st.subheader("Cell Processing Waterfall")
    
    # Add reference to the sidebar sliders
    st.info("""
    **Note:** This visualization is controlled by the sliders in the sidebar.
    Adjust the sliders in the **Processing Efficiency** section to see how changes in cell recovery
    at each step affect the final cell count.
    """)
    
    st.markdown("""
    This diagram shows how cells are processed from the initial blood sample through
    various steps until they become usable Single, Viable Cells for analysis.
    """)
    
    # Display the waterfall as a table
    st.write("**Cell Processing Waterfall:**")
    waterfall_data = []
    for step, count in cell_counts_waterfall.items():
        percent_of_start = (count / starting_cells) * 100
        percent_of_previous = 100
        if step != "Pre-Stain":
            prev_step = list(PROCESSING_STEPS.keys())[list(PROCESSING_STEPS.keys()).index(step)-1]
            percent_of_previous = (count / cell_counts_waterfall[prev_step]) * 100
            
        waterfall_data.append({
            "Processing Step": step,
            "Cell Count": f"{count:,}",
            "% of Starting": f"{percent_of_start:.1f}%",
            "% of Previous Step": f"{percent_of_previous:.1f}%",
            "Description": PROCESSING_STEPS[step]["description"]
        })
    
    waterfall_df = pd.DataFrame(waterfall_data)
    st.dataframe(waterfall_df, use_container_width=True, hide_index=True)
    
    # Create and display the processing waterfall chart
    fig = create_processing_waterfall_chart(cell_counts_waterfall, PROCESSING_STEPS)
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display the retention gauge
    final_retention = (cell_counts_waterfall["Single, Viable Cells"] / starting_cells) * 100
    gauge = create_retention_gauge(final_retention)
    st.plotly_chart(gauge, use_container_width=True)
    
    # Add explanation about the final cells
    st.info(f"""
    **Final Analysis Population:** The resulting {cell_counts_waterfall['Single, Viable Cells']:,} 
    Single, Viable Cells ({final_retention:.1f}% of starting cells) become the input for the Leukocytes population, 
    which is the root node for all subsequent analysis in the hierarchy.
    """)
    
    # Add a note about typical values
    st.write("""
    **Typical values:**
    - Post-Stain recovery: 30-40% of Pre-Stain
    - Events Acquired: 90-95% of Post-Stain
    - Single, Viable Cells: 70-80% of Events Acquired
    - Overall retention: 20-30% of starting cells
    """) 