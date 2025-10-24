# Performance Log Analyzer

A desktop application for analyzing Salesforce Industries CPQ Quoting performance logs. This tool parses nested method call logs, visualizes execution timelines, and identifies critical performance paths.

## Features

### Desktop Application
- 📊 **Interactive Call Tree**: Chrome DevTools-style hierarchical view of method calls
- ⏱️ **Timeline Visualization**: Gantt-style chart showing method execution over time
- 📈 **Duration Analysis**: Bar charts highlighting the longest-running methods
- 🎯 **Critical Path Detection**: Automatically identifies the longest execution path
- 📋 **Raw Data View**: Tabular view of all parsed method calls
- 🔍 **Smart Filtering**: Hide short methods, vlocity methods, expand/collapse tree
- 🖱️ **User-Friendly GUI**: Point-and-click interface built with Tkinter

### Jupyter Notebook Mode (NEW!)
- 🔬 **Interactive Exploration**: Run custom queries and filters on-the-fly
- 📊 **Unlimited Visualizations**: Create any chart using matplotlib, seaborn, plotly
- 🧪 **Advanced Analytics**: Full pandas/numpy power for statistical analysis
- 📝 **Reproducible Analysis**: Document your findings alongside code
- 🤝 **Share Results**: Export notebooks as HTML/PDF, share with colleagues
- 📈 **Machine Learning Ready**: Can integrate sklearn, scipy for predictive analytics

## Requirements

- Python 3.10 or higher
- macOS (tested), but should work on Linux and Windows
- Dependencies listed in `requirements.txt`

## Installation

1. **Clone or download this project**

2. **Create a virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Two Ways to Analyze Logs

#### Option 1: Desktop Application (GUI)
Best for quick analysis and standard reports:

```bash
./run.sh
```

Or manually:
```bash
cd source
python main.py
```

#### Option 2: Jupyter Notebook (Interactive)
Best for custom analysis, exploration, and advanced queries:

```bash
./run_jupyter.sh
```

Or manually:
```bash
source venv/bin/activate
jupyter notebook
```

📖 **See [JUPYTER_QUICKSTART.md](JUPYTER_QUICKSTART.md) for detailed Jupyter guide**

**When to use which:**
- **Desktop App**: Non-technical users, quick checks, standard reports, polished UI
- **Jupyter**: Data scientists, custom analysis, advanced statistics, reproducible research

### Using the Application

1. **Open a Log File**: Click "Browse..." to select your performance log file
2. **Analyze**: Click the "Analyze" button to parse and visualize the data
3. **Explore Tabs**: Navigate through different visualization tabs:
   - **Timeline**: See method execution in chronological order
   - **Duration Analysis**: View top methods by execution time
   - **Call Hierarchy**: Understand method nesting structure
   - **Summary Stats**: Review overall performance metrics
   - **Raw Data**: Examine parsed data in table format

### Log File Format

#### Primary Format: Salesforce Apex Debug Logs

The application is **optimized for Salesforce Apex debug logs** with `METHOD_ENTRY` and `METHOD_EXIT` events:

```
13:22:50.0 (4975796)|METHOD_ENTRY|[1]|01p5j00000Js5fA|vlocity_cmt.ComponentController.ComponentController()
13:22:50.0 (21080019)|METHOD_EXIT|[9]||System.UserInfo.getOrganizationId()
```

**Format Structure:**
- `HH:MM:SS.ms (microseconds)` - Timestamp with microsecond precision in parentheses
- `METHOD_ENTRY` or `METHOD_EXIT` - Event type
- Additional Salesforce metadata fields
- Method name (fully qualified)

#### Alternative Supported Formats

The application also supports simpler log formats for testing:

```
# Format 1: Pipe-separated
1698765432.123 | ENTER | QuoteCalculationService.calculateTotal
1698765432.234 | EXIT | QuoteCalculationService.calculateTotal

# Format 2: Bracket notation
[1698765432.123] ENTER QuoteCalculationService.calculateTotal
[1698765432.234] EXIT QuoteCalculationService.calculateTotal

# Format 3: Colon separator
1698765432.123 ENTER: QuoteCalculationService.calculateTotal
1698765432.234 EXIT: QuoteCalculationService.calculateTotal

# Format 4: Dash separator
1698765432.123 - ENTER - QuoteCalculationService.calculateTotal
1698765432.234 - EXIT - QuoteCalculationService.calculateTotal
```

#### Sample Log File

A sample log file for testing:

```
1698765432.100 | ENTER | CPQQuoteProcessor.processQuote
1698765432.110 | ENTER | ProductCatalogService.loadProducts
1698765432.150 | EXIT | ProductCatalogService.loadProducts
1698765432.160 | ENTER | PricingEngine.calculatePrices
1698765432.165 | ENTER | DiscountCalculator.applyDiscounts
1698765432.200 | EXIT | DiscountCalculator.applyDiscounts
1698765432.210 | ENTER | TaxCalculator.calculateTax
1698765432.250 | EXIT | TaxCalculator.calculateTax
1698765432.260 | EXIT | PricingEngine.calculatePrices
1698765432.270 | ENTER | QuoteGenerator.generateDocument
1698765432.320 | EXIT | QuoteGenerator.generateDocument
1698765432.330 | EXIT | CPQQuoteProcessor.processQuote
```

## Project Structure

```
perfLogAnalyzer1/
├── source/
│   ├── main.py                    # Application entry point
│   ├── __init__.py
│   ├── parser/
│   │   ├── __init__.py
│   │   └── log_parser.py         # Log parsing logic
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── chart_generator.py    # Chart generation
│   └── ui/
│       ├── __init__.py
│       └── app.py                # Tkinter desktop UI
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── sample_logs/                   # Sample log files (if any)
```

## How to Obtain Salesforce Apex Debug Logs

### Step 1: Enable Debug Logging

In Salesforce Setup:
1. Navigate to **Debug** → **Debug Logs**
2. Click **New** to create a trace flag
3. Select the **Traced Entity Type** (User, Apex Class, or Apex Trigger)
4. Choose the entity to trace
5. Set **Debug Level** to use:
   - `APEX_CODE = FINEST`
   - `APEX_PROFILING = FINEST`
   - `DB = INFO` (optional, for database operations)
6. Set start and expiration times

### Step 2: Execute Your CPQ Quote Process

Run the Salesforce Industries CPQ quoting process or any Apex transaction you want to analyze.

### Step 3: Download the Debug Log

1. Return to **Debug** → **Debug Logs**
2. Find your log entry (sorted by timestamp)
3. Click **View** or **Download** to get the `.log` file
4. Save it to your local machine

### Step 4: Analyze with this Tool

1. Launch the Performance Log Analyzer: `./run.sh`
2. Click **Browse** and select your downloaded `.log` file  
3. Click **Analyze**
4. Explore the visualizations!

**Note:** Salesforce debug logs with `FINEST` level automatically include `METHOD_ENTRY` and `METHOD_EXIT` events for all method calls. No custom instrumentation needed!

## How It Works

### 1. Log Parsing
The `LogParser` class:
- Reads log files line by line
- Identifies timestamps, event types, and method names
- Builds a call stack to track nested method execution
- Calculates durations by matching ENTER and EXIT events
- Creates a hierarchical tree of method calls

### 2. Data Processing
- Computes execution times for each method
- Calculates "self time" (time excluding child calls)
- Identifies parent-child relationships
- Detects the critical path (longest execution sequence)

### 3. Visualization
The `ChartGenerator` creates multiple views:
- **Timeline Chart**: Horizontal bars showing when each method executed
- **Duration Chart**: Sorted bar chart of longest methods
- **Hierarchy Chart**: Tree visualization of method call structure
- **Summary Statistics**: Histograms, distributions, and key metrics

### 4. Desktop UI
Built with Tkinter:
- File selection dialog
- Tabbed interface for different views
- Interactive charts with zoom/pan capabilities
- Data table for detailed inspection

## Critical Path Highlighting

The application automatically identifies and highlights the **critical path** in red:
- Starts with the longest top-level method
- Follows the longest child at each nesting level
- This represents the execution sequence that takes the most time

## Future Enhancements

- 🌐 Web application version using Next.js and JavaScript
- 📊 Additional chart types and filtering options
- 💾 Export functionality for reports
- 🔍 Search and filter capabilities
- 📱 Responsive design for mobile devices

## Troubleshooting

### Issue: "No data could be parsed"
- Check that your log file matches one of the supported formats
- Ensure timestamps are in Unix format with milliseconds
- Verify that ENTER/EXIT pairs are properly matched

### Issue: Charts not displaying
- Ensure matplotlib and seaborn are properly installed
- Check that you have a display available (GUI environment)

### Issue: Application won't start
- Verify Python version is 3.10 or higher: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check for any error messages in the terminal

## Contributing

This is a work in progress. Feel free to:
- Report bugs
- Suggest features
- Submit improvements

## License

This project is for internal use analyzing Salesforce Industries CPQ performance.

## Contact

For questions or support, please reach out to the development team.

