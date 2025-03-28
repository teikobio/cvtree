"""
Main Streamlit application for Flow Cytometry Cell Population Calculator

This app allows users to select an input cell count and calculates expected 
cell numbers and CV values for each population in the hierarchy.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Try to import optional dependencies
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Add the current directory to the path to import custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from cell_database import CellHierarchyDB
from cv_calculator import calculate_cv, categorize_cv, generate_keeney_table
from config.settings import (
    DEFAULT_POST_STAIN_PCT,
    DEFAULT_EVENTS_ACQUIRED_PCT,
    DEFAULT_VIABLE_CELLS_PCT,
    PROCESSING_STEPS,
    DEFAULT_DESIRED_CVS,
    DEFAULT_FREQUENCIES,
    DEFAULT_STARTING_CELLS,
    MIN_STARTING_CELLS,
    STEP_STARTING_CELLS
)
from components.table_view import display_table_view
from components.cv_analysis import display_cv_analysis
from components.cell_distribution import display_cell_distribution
from components.cell_processing import display_cell_processing
from visualizations.tree_view import create_interactive_tree, create_text_tree, display_cv_legend

# Initialize the cell database
db = CellHierarchyDB()

def calculate_cell_counts(input_cells, hierarchy=None):
    """
    Calculate cell counts for each population based on input cells and hierarchy
    
    Args:
        input_cells: Number of input cells
        hierarchy: Optional custom hierarchy (uses database if None)
        
    Returns:
        Dictionary with cell counts for each population
    """
    if hierarchy is None:
        hierarchy = db.get_hierarchy()
    
    cell_counts = {}
    
    # First, calculate cell count for the root node (Leukocytes)
    # The input cells represent Single, Viable Cells that feed into Leukocytes
    root_node = db.get_root_node()
    cell_counts[root_node] = input_cells
    
    # Helper function to recursively calculate cell counts
    def calculate_children(node):
        if node in hierarchy:
            parent_count = cell_counts[node]
            
            for child in hierarchy[node]["children"]:
                # Calculate cell count based on proportion of parent
                child_proportion = hierarchy[child]["proportion"]
                cell_counts[child] = parent_count * child_proportion
                
                # Recursively calculate for this child's children
                calculate_children(child)
    
    # Start calculation from the root
    calculate_children(root_node)
    
    return cell_counts

def main():
    # Define default processing efficiency values
    post_stain_pct = DEFAULT_POST_STAIN_PCT
    events_acquired_pct = DEFAULT_EVENTS_ACQUIRED_PCT
    viable_cells_pct = DEFAULT_VIABLE_CELLS_PCT

    st.set_page_config(
        page_title="Flow Cytometry Cell Population Calculator",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("Flow Cytometry Cell Population Calculator")
    
    with st.expander("About this app", expanded=False):
        st.markdown("""
        This app estimates the number of cells in each population based on the initial input cell count
        and calculates the expected coefficient of variation (CV) using Keeney's formula: r = (100/CV)².
        
        **Key features:**
        - Enter any input cell count (starting from 10K)
        - View estimated cell counts for each population in the hierarchy
        - Analyze expected CV for each population
        - Identify populations with potentially unreliable measurements (high CV)
        
        **References:**
        - Keeney et al. formula for CV calculation: r = (100/CV)²
        - Hierarchy based on Peripheral Blood Mononuclear Cell (PBMC) standard
        """)
    
    # Sidebar controls
    with st.sidebar:
        st.header("Input Settings")
        
        # Add mode selector as first control
        analysis_mode = st.radio(
            "Analysis Mode",
            ["Forward: Calculate population counts from input cell amounts",
             "Reverse: Determine required input cells for a target population and CV"],
            help="Choose whether to calculate population counts from input cells, or determine required input cells for a target CV"
        )
        
        # Processing Efficiency section
        st.subheader("Processing Efficiency")
        st.write("Adjust the percentage of cells that survive each processing step:")
        
        post_stain_pct = st.slider(
            "Post-Stain (% of Pre-Stain):", 
            min_value=10, 
            max_value=100, 
            value=post_stain_pct,
            key="post_stain_pct",
            help="Typically 30-40% of cells survive staining and permeabilization"
        )
        
        events_acquired_pct = st.slider(
            "Events Acquired (% of Post-Stain):", 
            min_value=50, 
            max_value=100, 
            value=events_acquired_pct,
            key="events_acquired_pct",
            help="Typically 90-95% of stained cells are successfully acquired by the instrument"
        )
        
        viable_cells_pct = st.slider(
            "Single, Viable Cells (% of Events Acquired):", 
            min_value=50, 
            max_value=100, 
            value=viable_cells_pct,
            key="viable_cells_pct",
            help="Typically 70-80% of acquired events are single, viable cells after gating"
        )
        
        # Conditionally show sections based on analysis mode
        if analysis_mode.startswith("Forward"):
            # Show Sample Processing before Processing Efficiency in Forward mode
            st.subheader("Sample Processing")
            starting_cells = st.number_input(
                "Absolute number of cells in blood (per ml):",
                min_value=MIN_STARTING_CELLS,
                value=DEFAULT_STARTING_CELLS,
                step=STEP_STARTING_CELLS,
                format="%d",
                help="Typical value: 4-6 million cells/ml from healthy donor"
            )
        else:
            # Show Target Settings before Processing Efficiency in Reverse mode
            st.subheader("Target Settings")
            
            # Get all leaf populations for selection
            leaf_populations = [cell for cell in db.get_hierarchy() if not db.get_children(cell)]
            target_population = st.selectbox(
                "Target Population",
                options=leaf_populations,
                help="Select the population you want to analyze"
            )
            
            target_cv = st.slider(
                "Target CV (%)", 
                min_value=1, 
                max_value=20, 
                value=10,
                help="Select your desired CV target"
            )
            
            # Calculate the frequency of the selected population
            hierarchy = db.get_hierarchy()
            def get_cumulative_proportion(population):
                proportion = 1.0
                current = population
                while current in hierarchy:
                    proportion *= hierarchy[current]["proportion"]
                    current = db.get_parent(current)
                return proportion
            
            population_frequency = get_cumulative_proportion(target_population)
            
            st.info(f"""
            Based on the hierarchy, {target_population} represents approximately 
            {population_frequency:.4%} of total leukocytes
            """)
            
            # Calculate required events using Keeney's formula
            required_events = int((100/target_cv)**2 / population_frequency)
            
            # Calculate required input cells based on processing efficiencies
            total_efficiency = (post_stain_pct/100) * (events_acquired_pct/100) * (viable_cells_pct/100)
            required_input_cells = int(required_events / total_efficiency)
            
            st.success(f"""
            To achieve {target_cv}% CV for {target_population}:
            - Required events: {required_events:,}
            - Required input cells: {required_input_cells:,}
            
            (Using current processing efficiencies: {total_efficiency:.1%} overall)
            """)
            
            # Set starting cells for the rest of the calculations
            starting_cells = required_input_cells
        
        # Update processing steps with current values
        processing_steps = {
            "Pre-Stain": {"percent_of_previous": 1.0, "description": "Isolated PBMCs"}, 
            "Post-Stain": {"percent_of_previous": post_stain_pct/100, "description": "After staining, antibody binding, and permeabilization"},
            "Events Acquired": {"percent_of_previous": events_acquired_pct/100, "description": "Cells successfully measured by the flow cytometer"},
            "Single, Viable Cells": {"percent_of_previous": viable_cells_pct/100, "description": "Final cells after excluding doublets and dead cells"} 
        }
        
        # Add Keeney's table reference
        st.subheader("Keeney's Reference Table")
        st.markdown("""
        This table shows the total number of events needed to achieve specific CV percentages
        for populations occurring at different frequencies.
        """)
        
        # Generate and display Keeney's table
        keeney_df = generate_keeney_table(
            desired_cvs=DEFAULT_DESIRED_CVS,
            frequencies=DEFAULT_FREQUENCIES
        )
        
        # Format the table for display
        keeney_display = keeney_df.copy()
        keeney_display['Fraction'] = keeney_display['Fraction'].apply(lambda x: f"{x:.4f}")
        keeney_display = keeney_display.rename(columns={
            'Fraction': 'Frequency',
            '1:n': 'Ratio',
            'CV 1%': 'For 1% CV',
            'CV 5%': 'For 5% CV',
            'CV 10%': 'For 10% CV',
            'CV 20%': 'For 20% CV'
        })
        
        st.dataframe(keeney_display, use_container_width=True)
        
        # Calculate waterfall of cell counts (common to both modes)
        current_count = starting_cells
        cell_counts_waterfall = {}
        
        for step, info in processing_steps.items():
            current_count = int(current_count * info["percent_of_previous"])
            cell_counts_waterfall[step] = current_count
        
        # Use the Single, Viable Cells as the input for Leukocytes
        input_cells = cell_counts_waterfall["Single, Viable Cells"]
        st.success(f"Analysis using {input_cells:,} Single, Viable Cells as input for Leukocytes")
    
    # Calculate results
    cell_counts = calculate_cell_counts(input_cells)
    
    # Create dataframe with results
    results = []
    for cell_type, count in cell_counts.items():
        parent = db.get_parent(cell_type)
        parent_count = cell_counts[parent] if parent else None
        
        cv = calculate_cv(count)
        frequency = (count / parent_count if parent_count else 1.0) * 100
        
        results.append({
            "Population": cell_type,
            "Parent": parent if parent else "None",
            "Cell Count": int(count),
            "% of Parent": f"{frequency:.2f}%",
            "CV (%)": f"{cv:.2f}%", 
            "CV Value": cv,  # Raw value for sorting
            "CV Quality": categorize_cv(cv)
        })
    
    df = pd.DataFrame(results)
    
    # Create tabs based on analysis mode
    if analysis_mode.startswith("Forward"):
        # Show all tabs for forward mode
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Table View", 
            "Tree View", 
            "CV Analysis",
            "Cell Distribution",
            "Cell Processing"
        ])
    else:
        # Show focused tabs for reverse mode
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Required Cells Summary",
            "Tree View",  # Keep the tab but hide content if in reverse mode
            "CV Analysis",
            "Cell Distribution",  # Keep the tab but hide content if in reverse mode
            "Cell Processing"
        ])
    
    if analysis_mode.startswith("Forward"):
        with tab1:
            display_table_view(df, input_cells)
    else:
        with tab1:
            st.subheader(f"Required Cells for {target_population}")
            
            # Create a summary card
            st.markdown(f"""
            ### Target Settings
            - **Population:** {target_population}
            - **Target CV:** {target_cv}%
            - **Population Frequency:** {population_frequency:.4%}
            
            ### Required Numbers
            - **Events Needed:** {required_events:,}
            - **Input Cells Needed:** {required_input_cells:,}
            
            ### Processing Assumptions
            - Post-Stain Recovery: {post_stain_pct}%
            - Events Acquired: {events_acquired_pct}%
            - Single, Viable Cells: {viable_cells_pct}%
            - Overall Processing Efficiency: {total_efficiency:.1%}
            """)
            
            st.info("""
            💡 **Note:** These calculations use Keeney's formula (r = (100/CV)²) and account for 
            cell losses during processing. Adjust processing efficiencies in the sidebar 
            to see how they affect the required input cells.
            """)
    
    with tab2:
        if analysis_mode.startswith("Forward"):
            st.subheader("Cell Population Hierarchy")
            
            # Add view type selection
            view_type = st.radio(
                "Select visualization type:",
                ["Interactive Tree", "Text Tree"],
                horizontal=True
            )
            
            if view_type == "Interactive Tree":
                fig = create_interactive_tree(cell_counts, db)
                st.plotly_chart(fig, use_container_width=True, config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': [
                        'pan2d',
                        'zoomIn2d',
                        'zoomOut2d',
                        'resetScale2d'
                    ]
                })
            else:
                html = create_text_tree(cell_counts, db)
                st.markdown(html, unsafe_allow_html=True)
            
            display_cv_legend()
        else:
            st.info("Tree view is only available in Forward Analysis mode")
    
    with tab3:
        display_cv_analysis(df, db)
    
    with tab4:
        if analysis_mode.startswith("Forward"):
            display_cell_distribution(df, input_cells)
        else:
            st.info("Cell distribution view is only available in Forward Analysis mode")
    
    with tab5:
        display_cell_processing(cell_counts_waterfall, starting_cells)

if __name__ == "__main__":
    main()