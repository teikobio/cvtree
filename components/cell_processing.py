"""
Cell processing component for displaying processing steps and efficiency metrics
"""

import streamlit as st
import pandas as pd
from visualizations.charts import create_processing_waterfall_chart, create_retention_gauge
from config.settings import PROCESSING_STEPS

def display_cell_processing(cell_counts_waterfall, starting_cells, target_population=None, db=None):
    """Display the cell processing view
    
    Args:
        cell_counts_waterfall: Dictionary of cell counts at each processing step
        starting_cells: Initial number of cells
        target_population: Optional target population for reverse analysis mode
        db: Optional database instance for hierarchy information
    """
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
    
    # Get the path to target population if in reverse mode
    target_path = []
    if target_population and db:
        current = target_population
        while current:
            target_path.insert(0, current)
            current = db.get_parent(current)
    
    # Create extended waterfall data including target population path
    waterfall_data = []
    
    # Add processing steps first
    for step, count in cell_counts_waterfall.items():
        percent_of_start = (count / starting_cells) * 100
        percent_of_previous = 100
        if step != "Pre-Stain":
            prev_step = list(cell_counts_waterfall.keys())[list(cell_counts_waterfall.keys()).index(step)-1]
            percent_of_previous = (count / cell_counts_waterfall[prev_step]) * 100
            
        waterfall_data.append({
            "Processing Step": step,
            "Cell Count": f"{count:,}",
            "% of Starting": f"{percent_of_start:.2f}%",
            "% of Previous Step": f"{percent_of_previous:.2f}%",
            "Description": PROCESSING_STEPS[step]["description"]
        })
    
    # Add target population path if in reverse mode
    if target_path:
        current_count = cell_counts_waterfall["Single, Viable Cells"]
        for i, pop in enumerate(target_path):
            if i == 0:  # Skip Leukocytes as it's same as Single, Viable Cells
                continue
                
            # Get frequency from parent
            parent = target_path[i-1]
            parent_count = current_count
            frequency = db.get_hierarchy()[pop]["proportion"]
            current_count = int(parent_count * frequency)
            
            waterfall_data.append({
                "Processing Step": pop,
                "Cell Count": f"{current_count:,}",
                "% of Starting": f"{(current_count / starting_cells * 100):.2f}%",
                "% of Previous Step": f"{(frequency * 100):.2f}%",
                "Description": f"Population frequency: {frequency:.2%}"
            })
    
    # Display the waterfall as a table
    st.write("**Cell Processing Waterfall:**")
    waterfall_df = pd.DataFrame(waterfall_data)
    st.dataframe(waterfall_df, use_container_width=True, hide_index=True)
    
    # Create and display the processing waterfall chart with target population path
    fig = create_processing_waterfall_chart(
        {step["Processing Step"]: int(step["Cell Count"].replace(",", "")) 
         for step in waterfall_data}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display the retention gauge
    final_retention = (cell_counts_waterfall["Single, Viable Cells"] / starting_cells) * 100
    gauge = create_retention_gauge(final_retention)
    st.plotly_chart(gauge, use_container_width=True)
    
    # Add explanation about the final cells
    if target_population:
        st.info(f"""
        **Final Analysis Population:** Starting with {cell_counts_waterfall['Single, Viable Cells']:,} 
        Single, Viable Cells ({final_retention:.1f}% of starting cells) as input for Leukocytes,
        we follow the hierarchy path to reach {target_population} with {waterfall_data[-1]['Cell Count']} cells
        ({float(waterfall_data[-1]['% of Starting'].rstrip('%')):.1f}% of starting cells).
        """)
    else:
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