"""
Component for displaying Reverse Analysis settings and calculations in the sidebar.
"""

import streamlit as st
from cell_database import CellHierarchyDB
from config.settings import (
    DEFAULT_POST_STAIN_PCT,
    DEFAULT_EVENTS_ACQUIRED_PCT,
    DEFAULT_VIABLE_CELLS_PCT,
    MIN_STARTING_CELLS,
    DEFAULT_STARTING_CELLS
)

def display_reverse_analysis_sidebar(db: CellHierarchyDB):
    """
    Displays the Target Population (using st.selectbox) and CV settings,
    performs calculations, and returns a dictionary containing calculated values.
    """
    st.sidebar.subheader("Target Population Settings")

    # Get all cell types and sort them for the dropdown
    all_cell_types = sorted(db.get_all_cell_types())

    # Initialize session state for target population if it doesn't exist
    if 'reverse_target_population' not in st.session_state:
        # Default to first leaf node, or first node if no leaves
        leaf_populations = [cell for cell in db.get_hierarchy() if not db.get_children(cell)]
        default_pop = leaf_populations[0] if leaf_populations else (all_cell_types[0] if all_cell_types else None)
        st.session_state.reverse_target_population = default_pop

    # Get the *current* value from session state before rendering the selectbox
    current_selection_in_state = st.session_state.reverse_target_population
    current_selection_index = all_cell_types.index(current_selection_in_state) if current_selection_in_state in all_cell_types else 0

    # Use st.selectbox with all cell types
    new_selection = st.sidebar.selectbox(
        "Target Population",
        options=all_cell_types,
        index=current_selection_index, # Set index based on current session state
        help="Select the population you want to analyze (leaves and intermediate nodes)"
    )

    # Update session state if the selection changed
    if new_selection and new_selection != st.session_state.reverse_target_population:
        st.session_state.reverse_target_population = new_selection
        # Clear the slider value when population changes
        cv_slider_key = f"target_cv_{st.session_state.reverse_target_population}"
        if cv_slider_key in st.session_state:
             del st.session_state[cv_slider_key]
        st.rerun()

    # Use the persisted target population from session state for all subsequent logic
    target_population = st.session_state.reverse_target_population

    # Ensure target_population is valid before proceeding (basic check is still useful)
    if not target_population or target_population not in db.get_all_cell_types():
         st.error("Invalid target population selected. Please refresh.") # Simplified error
         # Return default results dictionary
         return {
             "target_population": None, "target_cv": 20.0, "population_frequency": 0.0,
             "required_events": 0, "required_input_cells": MIN_STARTING_CELLS,
             "total_efficiency": 0.0, "starting_cells": MIN_STARTING_CELLS
         }

    # Initialize return dictionary
    results = {
        "target_population": target_population,
        "target_cv": 20.0, # Default CV
        "population_frequency": 0.0,
        "required_events": 0,
        "required_input_cells": MIN_STARTING_CELLS,
        "total_efficiency": 0.0,
        "starting_cells": MIN_STARTING_CELLS # Default starting cells
    }

    # --- Calculations Section ---
    hierarchy = db.get_hierarchy()
    cv_slider_key = f"target_cv_{target_population}"
    target_cv = st.sidebar.number_input(
        f"Target CV (%) for {target_population}", # Dynamic label
        min_value=0.1,
        max_value=100.0,
        value=st.session_state.get(cv_slider_key, 20.0),
        step=0.1,
        help="Desired coefficient of variation for the target population",
        key=cv_slider_key # Unique key per population
    )
    results["target_cv"] = target_cv

    # --- Direct lookup for population frequency (assuming valid target_population) ---
    population_frequency = hierarchy[target_population]["proportion"]
    
    results["population_frequency"] = population_frequency

    # Calculate required events
    required_events = 0 
    target_events_required = 0
    total_events_needed = 0

    if population_frequency > 0:
        if target_cv > 0:
            target_events_required = int((100/target_cv)**2)
            total_events_needed = int(target_events_required / population_frequency)
        else:
            st.warning("Target CV cannot be zero.") 
            target_events_required = float('inf')
            total_events_needed = float('inf')

        results["target_events_required"] = target_events_required if target_events_required != float('inf') else 'N/A'
        results["total_events_needed"] = total_events_needed if total_events_needed != float('inf') else 'N/A'
    else:
        # Handle zero frequency case - no events required
        st.info(f"Population frequency for {target_population} is zero. No events required.")
        results["target_events_required"] = 0
        results["total_events_needed"] = 0

    # Get current processing efficiencies
    post_stain_pct_rev = st.session_state.get("post_stain_pct", DEFAULT_POST_STAIN_PCT)
    events_acquired_pct_rev = st.session_state.get("events_acquired_pct", DEFAULT_EVENTS_ACQUIRED_PCT)
    viable_cells_pct_rev = st.session_state.get("viable_cells_pct", DEFAULT_VIABLE_CELLS_PCT)
    total_efficiency = (post_stain_pct_rev/100) * (events_acquired_pct_rev/100) * (viable_cells_pct_rev/100)
    results["total_efficiency"] = total_efficiency

    # Calculate required input cells based on total events needed
    required_input_cells = 0 
    if isinstance(results["total_events_needed"], (int, float)) and results["total_events_needed"] > 0 and total_efficiency > 0:
        required_input_cells = int(results["total_events_needed"] / total_efficiency)
        
        # Display success message 
        req_events_disp = f'{results["target_events_required"]:,}' if isinstance(results["target_events_required"], int) else results["target_events_required"]
        total_events_disp = f'{results["total_events_needed"]:,}' if isinstance(results["total_events_needed"], int) else results["total_events_needed"]

        st.sidebar.success(f"""
        **Results for {target_population} (Target CV: {target_cv:.1f}%)**
        - Population Frequency: {population_frequency:.4%}
        - {target_population} Events Required (r = (100/CV)²): {req_events_disp}
        - Total Leukocyte Events Needed: {total_events_disp}
        - Required Input Cells (Pre-Stain): {required_input_cells:,}
        - Overall Efficiency Used: {total_efficiency:.1%}
        """)
    elif total_efficiency <= 0:
        st.error("Cannot calculate required input cells with zero processing efficiency.")
        required_input_cells = 'N/A'
    elif results["total_events_needed"] == 'N/A':
        st.warning("Required input cells cannot be calculated due to zero Target CV.")
        required_input_cells = 'N/A'
    elif results["total_events_needed"] == 0:
        # This case now covers zero frequency explicitly
        st.info(f"No input cells required for {target_population} with zero frequency or zero events needed.")
        required_input_cells = 0
    else:
         st.error("An error occurred during input cell calculation.")
         required_input_cells = 'N/A'

    # Store final calculated values
    results["required_input_cells"] = required_input_cells
    if isinstance(required_input_cells, int) and required_input_cells > 0:
        results["starting_cells"] = required_input_cells
    else:
        results["starting_cells"] = MIN_STARTING_CELLS 

    return results 