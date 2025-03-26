"""
Cell population hierarchy database

This module provides the cell hierarchy structure for PBMC samples
based on the flow cytometry standard 25 hierarchy.
"""

import json
import os

# Default cell hierarchy with proportions (% of parent population)
DEFAULT_HIERARCHY = {
    "Leukocytes": {
        "proportion": 1.0,  # 100% of input
        "parent": None,
        "children": ["non-Granulocytes", "Basophil"]
    },
    "non-Granulocytes": {
        "proportion": 0.75,  # 75% of Leukocytes are non-granulocytes
        "parent": "Leukocytes",
        "children": ["T cell", "B cell", "non-T non-B"]
    },
    "Basophil": {
        "proportion": 0.25,  # 25% of Leukocytes (simplified)
        "parent": "Leukocytes",
        "children": []
    },
    "T cell": {
        "proportion": 0.7,  # 70% of non-Granulocytes (from document: 37.28% of non-granulocytes)
        "parent": "non-Granulocytes",
        "children": ["Gamma Delta T cell", "Natural Killer T cell", "non-Gamma Delta non-Natural Killer T cell"]
    },
    "B cell": {
        "proportion": 0.15,  # 15% of non-Granulocytes
        "parent": "non-Granulocytes",
        "children": ["Naive B cell", "Memory B cell", "Marginal Zone-like B cell", "Plasmablast"]
    },
    "non-T non-B": {
        "proportion": 0.15,  # 15% of non-Granulocytes
        "parent": "non-Granulocytes",
        "children": ["Natural Killer", "non-Natural Killer"]
    },
    # T cell subtypes
    "Gamma Delta T cell": {
        "proportion": 0.05,  # 5% of T cells
        "parent": "T cell",
        "children": []
    },
    "Natural Killer T cell": {
        "proportion": 0.03,  # 3% of T cells
        "parent": "T cell",
        "children": []
    },
    "non-Gamma Delta non-Natural Killer T cell": {
        "proportion": 0.92,  # 92% of T cells
        "parent": "T cell",
        "children": ["OTHER_T", "CD4 T cell", "CD8 T cell", "Double Positive T cell", "Double Negative T cell"]
    },
    "OTHER_T": {
        "proportion": 0.03,  # 3% of non-Gamma Delta non-NKT cells
        "parent": "non-Gamma Delta non-Natural Killer T cell",
        "children": []
    },
    "CD4 T cell": {
        "proportion": 0.65,  # 65% of non-Gamma Delta non-NKT cells
        "parent": "non-Gamma Delta non-Natural Killer T cell",
        "children": ["Treg", "CD4+ non-Treg"]
    },
    "CD8 T cell": {
        "proportion": 0.25,  # 25% of non-Gamma Delta non-NKT cells
        "parent": "non-Gamma Delta non-Natural Killer T cell",
        "children": ["CD8 T Naive", "CD8 T Central Memory", "CD8 T Effector Memory", "CD8 TEMRA"]
    },
    "Double Positive T cell": {
        "proportion": 0.02,  # 2% of non-Gamma Delta non-NKT cells
        "parent": "non-Gamma Delta non-Natural Killer T cell",
        "children": []
    },
    "Double Negative T cell": {
        "proportion": 0.05,  # 5% of non-Gamma Delta non-NKT cells
        "parent": "non-Gamma Delta non-Natural Killer T cell",
        "children": []
    },
    "Treg": {
        "proportion": 0.08,  # 8% of CD4 T cells
        "parent": "CD4 T cell",
        "children": []
    },
    "CD4+ non-Treg": {
        "proportion": 0.92,  # 92% of CD4 T cells
        "parent": "CD4 T cell",
        "children": ["CD4 T Naive", "CD4 T Central Memory", "CD4 T Effector Memory", "CD4 TEMRA"]
    },
    "CD4 T Naive": {
        "proportion": 0.35,  # 35% of CD4+ non-Treg cells
        "parent": "CD4+ non-Treg",
        "children": []
    },
    "CD4 T Central Memory": {
        "proportion": 0.35,  # 35% of CD4+ non-Treg cells
        "parent": "CD4+ non-Treg",
        "children": []
    },
    "CD4 T Effector Memory": {
        "proportion": 0.25,  # 25% of CD4+ non-Treg cells
        "parent": "CD4+ non-Treg",
        "children": []
    },
    "CD4 TEMRA": {
        "proportion": 0.05,  # 5% of CD4+ non-Treg cells
        "parent": "CD4+ non-Treg",
        "children": []
    },
    "CD8 T Naive": {
        "proportion": 0.40,  # 40% of CD8 T cells
        "parent": "CD8 T cell",
        "children": []
    },
    "CD8 T Central Memory": {
        "proportion": 0.20,  # 20% of CD8 T cells
        "parent": "CD8 T cell",
        "children": []
    },
    "CD8 T Effector Memory": {
        "proportion": 0.30,  # 30% of CD8 T cells
        "parent": "CD8 T cell",
        "children": []
    },
    "CD8 TEMRA": {
        "proportion": 0.10,  # 10% of CD8 T cells
        "parent": "CD8 T cell",
        "children": []
    },
    
    # B cell subtypes
    "Naive B cell": {
        "proportion": 0.60,  # 60% of B cells
        "parent": "B cell",
        "children": []
    },
    "Memory B cell": {
        "proportion": 0.30,  # 30% of B cells
        "parent": "B cell",
        "children": []
    },
    "Marginal Zone-like B cell": {
        "proportion": 0.08,  # 8% of B cells
        "parent": "B cell",
        "children": []
    },
    "Plasmablast": {
        "proportion": 0.02,  # 2% of B cells
        "parent": "B cell",
        "children": []
    },
    
    # NK and non-NK cell types
    "Natural Killer": {
        "proportion": 0.70,  # 70% of non-T non-B cells
        "parent": "non-T non-B",
        "children": ["Cytolytic Natural Killer", "Cytokine-producing Natural Killer", "Non-cytolytic Natural Killer"]
    },
    "non-Natural Killer": {
        "proportion": 0.30,  # 30% of non-T non-B cells
        "parent": "non-T non-B",
        "children": ["Monocyte", "non-Monocyte"]
    },
    "Cytolytic Natural Killer": {
        "proportion": 0.50,  # 50% of NK cells
        "parent": "Natural Killer",
        "children": []
    },
    "Cytokine-producing Natural Killer": {
        "proportion": 0.30,  # 30% of NK cells
        "parent": "Natural Killer",
        "children": []
    },
    "Non-cytolytic Natural Killer": {
        "proportion": 0.20,  # 20% of NK cells
        "parent": "Natural Killer",
        "children": []
    },
    
    # Monocyte subtypes
    "Monocyte": {
        "proportion": 0.80,  # 80% of non-NK cells
        "parent": "non-Natural Killer",
        "children": ["Classical monocyte", "Non-classical monocyte", "Intermediate monocyte"]
    },
    "non-Monocyte": {
        "proportion": 0.20,  # 20% of non-NK cells
        "parent": "non-Natural Killer",
        "children": ["Dendritic Cell"]
    },
    "Classical monocyte": {
        "proportion": 0.80,  # 80% of monocytes
        "parent": "Monocyte",
        "children": []
    },
    "Non-classical monocyte": {
        "proportion": 0.12,  # 12% of monocytes
        "parent": "Monocyte",
        "children": []
    },
    "Intermediate monocyte": {
        "proportion": 0.08,  # 8% of monocytes (from document: inMono 0.47% of non-granulocytes)
        "parent": "Monocyte",
        "children": []
    },
    
    # Dendritic cell subtypes
    "Dendritic Cell": {
        "proportion": 1.0,  # 100% of non-monocyte cells
        "parent": "non-Monocyte",
        "children": ["Plasmacytoid dendritic cell", "Transitional dendritic cell", "Conventional dendritic cell"]
    },
    "Plasmacytoid dendritic cell": {
        "proportion": 0.30,  # 30% of dendritic cells
        "parent": "Dendritic Cell",
        "children": []
    },
    "Transitional dendritic cell": {
        "proportion": 0.20,  # 20% of dendritic cells
        "parent": "Dendritic Cell",
        "children": []
    },
    "Conventional dendritic cell": {
        "proportion": 0.50,  # 50% of dendritic cells
        "parent": "Dendritic Cell",
        "children": ["Type 1 conventional dendritic cell", "Type 2 conventional dendritic cell"]
    },
    "Type 1 conventional dendritic cell": {
        "proportion": 0.50,  # 50% of conventional dendritic cells
        "parent": "Conventional dendritic cell",
        "children": []
    },
    "Type 2 conventional dendritic cell": {
        "proportion": 0.50,  # 50% of conventional dendritic cells
        "parent": "Conventional dendritic cell",
        "children": []
    }
}

class CellHierarchyDB:
    """Database class for cell hierarchy and proportions"""
    
    def __init__(self, filepath=None):
        """
        Initialize the cell hierarchy database
        
        Args:
            filepath: Optional path to JSON file with cell hierarchy data
        """
        self.hierarchy = DEFAULT_HIERARCHY
        
        if filepath and os.path.exists(filepath):
            self.load_from_file(filepath)
    
    def load_from_file(self, filepath):
        """Load cell hierarchy from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.hierarchy = json.load(f)
            print(f"Loaded cell hierarchy from {filepath}")
        except Exception as e:
            print(f"Error loading from {filepath}: {e}")
            print("Using default hierarchy instead")
    
    def save_to_file(self, filepath):
        """Save current hierarchy to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.hierarchy, f, indent=2)
            print(f"Saved cell hierarchy to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")
            return False
    
    def get_hierarchy(self):
        """Return the full cell hierarchy"""
        return self.hierarchy
    
    def get_cell_info(self, cell_type):
        """Get information for a specific cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]
        return None
    
    def update_proportion(self, cell_type, proportion):
        """Update the proportion for a specific cell type"""
        if cell_type in self.hierarchy:
            self.hierarchy[cell_type]["proportion"] = proportion
            return True
        return False
    
    def get_all_cell_types(self):
        """Return a list of all cell types in the hierarchy"""
        return list(self.hierarchy.keys())
    
    def get_root_node(self):
        """Return the root node of the hierarchy"""
        for cell_type, info in self.hierarchy.items():
            if info["parent"] is None:
                return cell_type
        return None
    
    def get_children(self, cell_type):
        """Get direct children of a cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]["children"]
        return []
    
    def get_parent(self, cell_type):
        """Get the parent of a cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]["parent"]
        return None