"""
CV Calculator Module

This module implements Keeney's formula for calculating coefficient of variation (CV)
based on cell counts in flow cytometry.

Reference: Keeney et al. "...for cell-based assays such as flow cytometry, a simple 
calculation can be used to determine the size of the database/sample that will 
provide a given precision: r = (100/CV)²; where r is the number of events meeting 
the required criterion, and CV is the coefficient of variation of a known positive control."
"""

import numpy as np
import pandas as pd

def calculate_cv(cell_count):
    """
    Calculate coefficient of variation (CV) using Keeney's formula: r = (100/CV)²
    
    Args:
        cell_count: Number of cells observed
        
    Returns:
        CV as a percentage
    """
    if cell_count <= 0:
        return float('inf')  # Return infinity for zero or negative cell counts
        
    # Calculate CV using Keeney's formula
    cv = 100 / np.sqrt(cell_count)
    
    return cv

def calculate_cells_needed_for_cv(desired_cv):
    """
    Calculate how many cells are needed to achieve a desired CV
    
    Args:
        desired_cv: Target CV as a percentage
        
    Returns:
        Number of cells needed
    """
    if desired_cv <= 0:
        return float('inf')
        
    cells_needed = (100 / desired_cv) ** 2
    return cells_needed

def categorize_cv(cv):
    """
    Categorize CV value into quality categories
    
    Args:
        cv: Coefficient of variation as a percentage
        
    Returns:
        String describing the CV quality
    """
    if cv <= 1:
        return "Excellent (≤1%)"
    elif cv <= 5:
        return "Good (1-5%)"
    elif cv <= 10:
        return "Fair (5-10%)"
    elif cv <= 20:
        return "Poor (10-20%)"
    else:
        return "Very Poor (>20%)"
    
def generate_keeney_table(desired_cvs=None, frequencies=None):
    """
    Generate a table similar to Keeney's table in the documentation
    
    Args:
        desired_cvs: List of desired CV percentages
        frequencies: List of cell frequencies as fractions (e.g., 0.1 for 10%)
        
    Returns:
        Pandas DataFrame with the Keeney table
    """
    if desired_cvs is None:
        desired_cvs = [1, 5, 10, 20]
        
    if frequencies is None:
        frequencies = [0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001]
    
    # Calculate required events for each CV
    required_events = {cv: calculate_cells_needed_for_cv(cv) for cv in desired_cvs}
    
    # Build the table
    data = []
    for freq in frequencies:
        row = {'Fraction': freq, '1:n': int(1/freq) if freq > 0 else float('inf')}
        
        for cv in desired_cvs:
            total_events = required_events[cv] / freq
            row[f'CV {cv}%'] = int(total_events)
        
        data.append(row)
    
    return pd.DataFrame(data)