"""
Component for displaying Reverse Analysis settings and calculations in the sidebar.
"""

import streamlit as st
from cell_database import CellHierarchyDB
from st_ant_tree import st_ant_tree # Add new import
from config.settings import (
    DEFAULT_POST_STAIN_PCT,
    DEFAULT_EVENTS_ACQUIRED_PCT,
    DEFAULT_VIABLE_CELLS_PCT,
    MIN_STARTING_CELLS,
    DEFAULT_STARTING_CELLS # Added for default return
)

def build_tree_select_nodes(node_name, db):
    """Recursively build node structure for st-ant-tree.

    Note: st-ant-tree expects 'title' key for display text.
    """
    children_names = db.get_children(node_name)
    children_nodes = []
    if children_names:
        children_nodes = [build_tree_select_nodes(child, db) for child in children_names]
    # Use 'title' instead of 'label' for st-ant-tree
    node_dict = {"title": node_name, "value": node_name, "children": children_nodes}
    print(f"BUILDING NODE: {node_dict}") # DEBUG - Check value here
    return node_dict

def get_cumulative_proportion(population, db, hierarchy):
    """Calculate the cumulative proportion of a population relative to the root."""
    proportion = 1.0
    current = population
    parent = db.get_parent(current)
    # Traverse up the tree until the root's parent (None) is reached
    while parent is not None:
        if current in hierarchy:
            # Check if the node exists and has a proportion defined
            if "proportion" in hierarchy[current]:
                 proportion *= hierarchy[current]["proportion"]
            else:
                 st.error(f"Error: Node {current} missing 'proportion' in hierarchy definition.")
                 return 0.0
        else:
            # This case should ideally not happen if db methods are correct
            st.error(f"Error: Node {current} not found in hierarchy definition during proportion calculation.")
            return 0.0
        current = parent
        parent = db.get_parent(current) # Get the next parent

    # If the loop finishes, 'current' should be the root node.
    # Check if root itself has a proportion (usually 1.0, handled implicitly if traversal is correct)
    # No need to multiply by root proportion if it's 1.0 and traversal stops correctly.
    return proportion


def display_reverse_analysis_sidebar(db: CellHierarchyDB):
    """
    Displays the Target Population and CV settings using st-ant-tree,
    performs calculations, and returns a dictionary containing calculated values.
    """
    st.subheader("Target Population Settings")

    # Initialize session state for target population if it doesn't exist
    if 'reverse_target_population' not in st.session_state:
        # Set initial default (e.g., first leaf node)
        leaf_populations = [cell for cell in db.get_hierarchy() if not db.get_children(cell)]
        st.session_state.reverse_target_population = leaf_populations[0] if leaf_populations else db.get_root_node()
        print(f"INITIALIZED SESSION STATE: {st.session_state.reverse_target_population}") # Print to console/logs

    # Prepare data for tree select
    root_node_name = db.get_root_node()
    nodes_for_select = [build_tree_select_nodes(root_node_name, db)] if root_node_name else []

    # Use st_ant_tree
    print(f"BEFORE st_ant_tree: SESSION STATE = {st.session_state.reverse_target_population}") # Print to console/logs
    selected_values = st_ant_tree(
        treeData=nodes_for_select,
        showSearch=True,
        allowClear=False,
        placeholder="Select target population",
        defaultValue=[st.session_state.reverse_target_population],
        treeCheckable=False,
        key="ant_tree_select_reverse"
    )
    print(f"AFTER st_ant_tree: RETURNED = {selected_values}") # Print to console/logs

    # Determine the currently selected node
    new_selection = selected_values[0] if selected_values else None
    print(f"NEW SELECTION from component = {new_selection}") # Print to console/logs

    # Update session state only if a new, valid selection is made
    if new_selection and new_selection != st.session_state.reverse_target_population:
        print(f"UPDATING SESSION STATE from {st.session_state.reverse_target_population} to {new_selection}") # Print to console/logs
        st.session_state.reverse_target_population = new_selection
        # Clear the slider value when population changes
        cv_slider_key = f"target_cv_{st.session_state.reverse_target_population}"
        if cv_slider_key in st.session_state:
             del st.session_state[cv_slider_key]

    # Use the persisted target population from session state
    target_population = st.session_state.reverse_target_population
    # REMOVED: st.write(f"DEBUG Sidebar: target_population from state = '{target_population}'") # DEBUG
    print(f"FINAL target_population used for calc = {target_population}") # Print to console/logs

    # Initialize return dictionary - always use the target_population from session state
    results = {
        "target_population": target_population,
        "target_cv": 20.0, # Default CV
        "population_frequency": 0.0,
        "required_events": 0,
        "required_input_cells": MIN_STARTING_CELLS,
        "total_efficiency": 0.0,
        "starting_cells": MIN_STARTING_CELLS # Default starting cells
    }
    print(f"RESULTS Dict being returned = {results}") # Print to console/logs

    # --- Calculations Section (Now uses reliable target_population from session state) ---
    hierarchy = db.get_hierarchy()

    # Use a consistent key for the slider, value resets if key changes
    cv_slider_key = f"target_cv_{target_population}"
    target_cv = st.slider(
        f"Target CV (%) for {target_population}", # Dynamic label
        min_value=0.1,
        max_value=100.0,
        value=st.session_state.get(cv_slider_key, 20.0), # Default to 20 if key not set
        step=0.1,
        help="Desired coefficient of variation for the target population",
        key=cv_slider_key # Unique key per population
    )
    results["target_cv"] = target_cv # Store selected CV

    population_frequency = get_cumulative_proportion(target_population, db, hierarchy)
    results["population_frequency"] = population_frequency

    if population_frequency is not None and population_frequency >= 0:
        # st.info(...) # Display info if needed, maybe redundant with success message
        pass # Info is implicitly shown in success message now
    else:
        st.error("Could not determine population frequency.")
        return results # Return current results (likely defaults)

    # Calculate required events
    required_events = float('inf')
    if population_frequency > 0:
        required_events = int((100/target_cv)**2 / population_frequency)
        results["required_events"] = required_events
    else:
        st.error(f"Cannot calculate required events for {target_population} with zero or invalid frequency.")
        results["required_events"] = 0

    # Get current processing efficiencies
    post_stain_pct_rev = st.session_state.get("post_stain_pct", DEFAULT_POST_STAIN_PCT)
    events_acquired_pct_rev = st.session_state.get("events_acquired_pct", DEFAULT_EVENTS_ACQUIRED_PCT)
    viable_cells_pct_rev = st.session_state.get("viable_cells_pct", DEFAULT_VIABLE_CELLS_PCT)
    total_efficiency = (post_stain_pct_rev/100) * (events_acquired_pct_rev/100) * (viable_cells_pct_rev/100)
    results["total_efficiency"] = total_efficiency

    # Calculate required input cells
    required_input_cells = float('inf')
    if required_events != float('inf') and total_efficiency > 0 :
        required_input_cells = int(required_events / total_efficiency)
        # Display success message here, as all inputs are now stable
        st.success(f"""
        **Results for {target_population} (Target CV: {target_cv:.1f}%)**
        - Population Frequency: {population_frequency:.4%}
        - Required Events: {required_events:,}
        - Required Input Cells (Pre-Stain): {required_input_cells:,}
        - Overall Efficiency Used: {total_efficiency:.1%}
        """)
    elif total_efficiency <= 0:
        st.error("Cannot calculate required input cells with zero processing efficiency.")
    elif required_events == float('inf'):
        pass # Error already shown for frequency
    else:
         st.error("An error occurred during input cell calculation.")

    # Store final calculated values
    results["required_input_cells"] = required_input_cells if required_input_cells != float('inf') else 0
    results["starting_cells"] = required_input_cells if required_input_cells != float('inf') else MIN_STARTING_CELLS

    return results 