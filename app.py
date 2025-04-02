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
from components.reverse_analysis import display_reverse_analysis_sidebar
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
    st.set_page_config(
        page_title="Flow Cytometry Cell Population Calculator",
        page_icon="🔬",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    # Initialize session state for mode selection if not exists
    if 'mode_selected' not in st.session_state:
        st.session_state.mode_selected = False
        st.session_state.analysis_mode = None

    # Initialize variables that might be set in Reverse mode
    reverse_results = None

    # Show splash screen if mode not selected
    if not st.session_state.mode_selected:
        st.title("Flow Cytometry Cell Population Calculator")
        
        # Create a container for the mode selection and button
        mode_container = st.container()
        
        st.write("Choose your analysis mode:")
        
        # Create columns for radio button and help text
        col1, col2 = st.columns([10, 1])
        
        # Radio selection with simple vertical layout
        with col1:
            mode_choice = st.radio(
                "",  # Empty label since we put it above
                options=["Forward", "Reverse"],
                format_func=lambda x: "I want to calculate population counts from input cell amounts" if x == "Forward" 
                                else "I want to determine required input cells for a target population and CV",
                horizontal=False,  # Stack vertically
                label_visibility="collapsed"  # Hide the empty label
            )
        
        with col2:
            st.write("")  # Add spacing to align with first radio button
            st.help("Start with your input cells and calculate expected cell counts, CV values, and processing efficiency impact")
            st.write("")  # Add spacing to align with second radio button
            st.help("Start with your target population and specify desired CV, calculate required input cells, and optimize processing parameters")
        
        # Add some spacing
        st.write("")
        
        # Simple button below
        if st.button("Start Analysis", type="primary", use_container_width=False):
            st.session_state.mode_selected = True
            st.session_state.analysis_mode = mode_choice
            st.rerun()
        
        # Add about section at the bottom of splash screen as regular text
        st.markdown("""
        ### About this app
        
        This app estimates the number of cells in each population based on the initial input cell count
        and calculates the expected coefficient of variation (CV) using Keeney's formula: r = (100/CV)².
        
        **Key features:**
        - Enter any input cell count (starting from 10K)
        - View estimated cell counts for each population in the hierarchy
        - Analyze expected CV for each population
        - Identify populations with potentially unreliable measurements (high CV)
        
        **Implementation Notes:**
        - Population hierarchy and frequencies are based on [Teiko's 25-marker PBMC spectral flow panel](https://teiko.bio/pbmc-spectral-flow/)
        - CV calculations are theoretical estimates using Keeney's formula and may differ from actual experimental values
        - The app is intended as a planning tool and should be validated against your specific experimental conditions
        
        **References:**
        - Keeney et al. ["Technical issues: flow cytometry and rare event analysis"](https://onlinelibrary.wiley.com/doi/10.1111/ijlh.12068)
        - [Teiko PBMC Spectral Flow Panel](https://teiko.bio/pbmc-spectral-flow/)
        """)
        
        # Add feedback button
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("""
            **Have feedback or found a bug?**  
            We're constantly improving this tool and would love to hear from you!
            """)
        with col2:
            st.link_button("📧 Send Feedback", "mailto:info@teiko.bio?subject=Feedback%20on%20Cytometry%20CV%2FPopulation%20counter", help="Send us an email with your feedback or bug report")
        
        return  # Exit here if mode not selected

    # Define default processing efficiency values
    post_stain_pct = DEFAULT_POST_STAIN_PCT
    events_acquired_pct = DEFAULT_EVENTS_ACQUIRED_PCT
    viable_cells_pct = DEFAULT_VIABLE_CELLS_PCT

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
        
        **Implementation Notes:**
        - Population hierarchy and frequencies are based on [Teiko's 25-marker PBMC spectral flow panel](https://teiko.bio/pbmc-spectral-flow/)
        - CV calculations are theoretical estimates using Keeney's formula and may differ from actual experimental values
        - The app is intended as a planning tool and should be validated against your specific experimental conditions
        
        **References:**
        - Keeney et al. ["Technical issues: flow cytometry and rare event analysis"](https://onlinelibrary.wiley.com/doi/10.1111/ijlh.12068)
        - [Teiko PBMC Spectral Flow Panel](https://teiko.bio/pbmc-spectral-flow/)
        """)
        
        # Add feedback button in expander too
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("""
            **Have feedback or found a bug?**  
            We're constantly improving this tool and would love to hear from you!
            """)
        with col2:
            st.link_button("📧 Send Feedback", "mailto:info@teiko.bio?subject=Feedback%20on%20Cytometry%20CV%2FPopulation%20counter", help="Send us an email with your feedback or bug report")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Input Settings")
        
        # Replace mode display and reset button with radio buttons
        st.session_state.analysis_mode = st.radio(
            "Analysis Mode",
            ["Forward", "Reverse"],
            index=0 if st.session_state.analysis_mode == "Forward" else 1,
            format_func=lambda x: f"{x} Analysis",
            help="Choose whether to calculate population counts from input cells, or determine required input cells for a target CV"
        )
        
        # Conditionally show sections based on analysis mode
        if st.session_state.analysis_mode == "Forward":
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
        elif st.session_state.analysis_mode == "Reverse":
            # Call the dedicated component function for Reverse Analysis settings
            reverse_results = display_reverse_analysis_sidebar(db)
            starting_cells = reverse_results['starting_cells']

        # Processing Efficiency section
        st.subheader("Processing Efficiency")
        st.write("Adjust the percentage of cells that survive each processing step:")
        
        # Add Reset to Defaults button before the sliders
        if st.button("Reset Processing Steps to Defaults"):
            # Use a different key to trigger the reset
            st.session_state.reset_processing = True
            st.rerun()
            
        # Initialize reset flag if not present
        if 'reset_processing' not in st.session_state:
            st.session_state.reset_processing = False
            
        # Use the reset flag to determine slider values
        post_stain_value = DEFAULT_POST_STAIN_PCT if st.session_state.reset_processing else st.session_state.get("post_stain_pct", DEFAULT_POST_STAIN_PCT)
        events_acquired_value = DEFAULT_EVENTS_ACQUIRED_PCT if st.session_state.reset_processing else st.session_state.get("events_acquired_pct", DEFAULT_EVENTS_ACQUIRED_PCT)
        viable_cells_value = DEFAULT_VIABLE_CELLS_PCT if st.session_state.reset_processing else st.session_state.get("viable_cells_pct", DEFAULT_VIABLE_CELLS_PCT)
        
        # Reset the flag after getting values
        if st.session_state.reset_processing:
            st.session_state.reset_processing = False
        
        post_stain_pct = st.slider(
            "Post-Stain (% of Pre-Stain):", 
            min_value=10, 
            max_value=100, 
            value=post_stain_value,
            key="post_stain_pct",
            help="Typically 30-40% of cells survive staining and permeabilization"
        )
        
        events_acquired_pct = st.slider(
            "Events Acquired (% of Post-Stain):", 
            min_value=50, 
            max_value=100, 
            value=events_acquired_value,
            key="events_acquired_pct",
            help="Typically 90-95% of stained cells are successfully acquired by the instrument"
        )
        
        viable_cells_pct = st.slider(
            "Single, Viable Cells (% of Events Acquired):", 
            min_value=50, 
            max_value=100, 
            value=viable_cells_value,
            key="viable_cells_pct",
            help="Typically 70-80% of acquired events are single, viable cells after gating"
        )

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
        # Ensure starting_cells is valid before calculation
        if starting_cells is None or not isinstance(starting_cells, (int, float)) or starting_cells < 0:
            st.error("Invalid starting cell count determined. Please check settings.")
            # Set a safe default or stop execution?
            starting_cells = DEFAULT_STARTING_CELLS

        current_count = starting_cells
        cell_counts_waterfall = {}
        
        for step, info in processing_steps.items():
            current_count = int(current_count * info["percent_of_previous"])
            cell_counts_waterfall[step] = current_count
        
        # Use the Single, Viable Cells as the input for Leukocytes
        input_cells = cell_counts_waterfall["Single, Viable Cells"]

        # Show success message only if starting_cells was valid
        if starting_cells > 0:
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
    if st.session_state.analysis_mode == "Forward":
        # Show all tabs for forward mode
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Table View", 
            "Tree View", 
            "CV Analysis",
            "Cell Distribution",
            "Cell Processing"
        ])

        with tab1:
            display_table_view(df, input_cells)
        
        with tab2:
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
                # Create a container with scrollable content
                st.markdown("""
                <style>
                .tree-container {
                    max-height: 800px;
                    overflow-y: auto;
                    font-family: monospace;
                    white-space: nowrap;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-radius: 5px;
                    color: #000000;  /* Set text color to black for visibility */
                }
                </style>
                """, unsafe_allow_html=True)
                
                html = create_text_tree(cell_counts, db)
                st.markdown(html, unsafe_allow_html=True)
            
            display_cv_legend()
        
        with tab3:
            display_cv_analysis(df, db)
        
        with tab4:
            display_cell_distribution(df, input_cells)
        
        with tab5:
            display_cell_processing(cell_counts_waterfall, starting_cells)

    else:
        # Show only relevant tabs for reverse mode
        tab1, tab5 = st.tabs([
            "Required Cells Summary",
            "Cell Processing"
        ])

        with tab1:
            # Check if reverse_results dictionary is available and has the needed keys
            if reverse_results and reverse_results.get("target_population"):
                # Access values safely from the dictionary
                target_pop = reverse_results.get("target_population", "N/A")
                target_cv_val = reverse_results.get("target_cv", "N/A")
                pop_freq = reverse_results.get("population_frequency", 0)
                req_events = reverse_results.get("required_events", 0)
                req_input = reverse_results.get("required_input_cells", 0)
                total_eff = reverse_results.get("total_efficiency", 0)
                # Read current processing values directly from session state for display
                current_post_stain_disp = st.session_state.get("post_stain_pct", DEFAULT_POST_STAIN_PCT)
                current_events_acquired_disp = st.session_state.get("events_acquired_pct", DEFAULT_EVENTS_ACQUIRED_PCT)
                current_viable_cells_disp = st.session_state.get("viable_cells_pct", DEFAULT_VIABLE_CELLS_PCT)

                # Use the correctly scoped variable 'target_pop' here
                st.subheader(f"Required Cells for {target_pop}")

                # Create a summary card using values from reverse_results
                st.markdown(f"""
                ### Target Settings
                - **Population:** {target_pop}
                - **Target CV:** {target_cv_val}%
                - **Population Frequency:** {pop_freq:.4%}

                ### Required Numbers
                - **Events Needed:** {req_events:,}
                - **Input Cells Needed (Pre-Stain):** {req_input:,}
                """)

                st.markdown("### Processing Assumptions")
                # Use consistently named variables holding current slider values
                st.markdown(
                    f"- Post-Stain Recovery: {current_post_stain_disp}%",
                    help="Percentage of cells that survive staining, antibody binding, and permeabilization steps"
                )
                st.markdown(
                    f"- Events Acquired: {current_events_acquired_disp}%",
                    help="Percentage of stained cells successfully measured by the flow cytometer"
                )
                st.markdown(
                    f"- Single, Viable Cells: {current_viable_cells_disp}%",
                    help="Percentage of acquired events that are single, viable cells after excluding doublets and dead cells"
                )
                st.markdown(
                    f"- Overall Processing Efficiency: {total_eff:.1%}",
                    help="Combined effect of all processing steps - multiply all percentages to get this value"
                )

                st.info("""
                💡 **Note:** These calculations use Keeney's formula (r = (100/CV)²) and account for
                cell losses during processing. Adjust processing efficiencies in the sidebar
                to see how they affect the required input cells.
                """)
            else:
                # Handle case where reverse_results might not be ready (e.g., initial load)
                st.info("Select target population and CV in the sidebar to see the summary.")
        
        with tab5:
            if reverse_results:
                display_cell_processing(
                    cell_counts_waterfall,
                    starting_cells,
                    target_population=reverse_results.get("target_population"),
                    db=db
                )
            else:
                display_cell_processing(cell_counts_waterfall, starting_cells)

if __name__ == "__main__":
    main()