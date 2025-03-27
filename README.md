# Flow Cytometry Cell Population Calculator

An interactive web application for flow cytometry experiment planning and analysis. This tool helps drug developers facilities optimize their experimental design by providing real-time calculations of expected cell yields and measurement reliability.

## 🔬 Features

### Forward Analysis Mode
- Calculate expected cell counts for all populations in your hierarchy
- Visualize population distributions with interactive tree and sunburst diagrams
- Monitor CV (Coefficient of Variation) quality for each population
- Track cell losses through processing steps with an interactive waterfall diagram
- Adjust processing efficiencies to match your protocol

### Reverse Analysis Mode
- Start with your target population and desired CV
- Calculate required input cell numbers
- Account for processing losses at each step
- Based on Keeney's statistical framework (r = (100/CV)²)

## 📊 Key Visualizations
- Interactive hierarchical tree view
- Cell processing waterfall
- CV analysis by population
- Cell distribution treemap and sunburst charts

## 🧪 Use Cases

1. **Experiment Planning**
   - Determine required starting cell numbers
   - Identify potentially problematic rare populations
   - Optimize sample volumes

2. **Protocol Optimization**
   - Track cell losses through processing steps
   - Identify steps with high cell loss
   - Compare different processing protocols

3. **Quality Control**
   - Monitor CV values across populations
   - Ensure statistical reliability
   - Flag populations with potentially unreliable measurements

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Streamlit
- Plotly
- pandas
- numpy
- igraph (for tree visualization)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/flow-cytometry-calculator.git

# Navigate to the project directory
cd flow-cytometry-calculator

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 📖 How to Use

1. **Choose Analysis Mode**
   - Forward mode: Start with input cells, see population counts
   - Reverse mode: Start with target CV, calculate required cells

2. **Adjust Parameters**
   - Set starting cell numbers or target CV
   - Modify processing efficiencies
   - Select populations of interest

3. **Analyze Results**
   - View interactive visualizations
   - Export data as CSV
   - Check CV quality indicators

## 🔍 Technical Details

### Cell Processing Steps
1. Pre-Stain (Initial PBMCs)
2. Post-Stain (After antibody staining)
3. Events Acquired (Flow cytometer measurement)
4. Single, Viable Cells (Final analysis population)

### CV Quality Categories
- Excellent: ≤1%
- Good: 1-5%
- Fair: 5-10%
- Poor: 10-20%
- Very Poor: >20%

## 📚 References

- Keeney's Formula for CV calculation: r = (100/CV)²
- Based on standard PBMC processing protocols
- CV quality thresholds from cytometry best practices
