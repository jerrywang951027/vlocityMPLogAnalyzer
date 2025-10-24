# Quick Start Guide

Get up and running with the Performance Log Analyzer in 5 minutes!

## Prerequisites

- **Python 3.10 or higher** installed on your system
  - Check: `python3 --version`
- **macOS** (tested on macOS, but should work on Linux/Windows)

## Option 1: Quick Start with Script (Recommended)

The easiest way to get started:

```bash
./run.sh
```

This script will:
1. Create a virtual environment (if needed)
2. Install all dependencies
3. Launch the application

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install packages
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
cd source
python main.py
```

## Using the Application

### 1. **Open a Log File**
   - Click the **"Browse..."** button
   - Navigate to `sample_logs/test_log.txt` (or your own log file)
   - Select the file

### 2. **Analyze**
   - Click the **"Analyze"** button
   - Wait for processing (usually < 1 second for small files)

### 3. **Explore Results**
   Navigate through the tabs:
   
   - **Timeline** 🕐: See when each method executed (Gantt chart)
   - **Duration Analysis** ⏱️: Find your slowest methods
   - **Call Hierarchy** 🌳: Understand method nesting
   - **Summary Stats** 📊: View comprehensive metrics
   - **Raw Data** 📋: Inspect parsed data table

### 4. **Identify Performance Issues**
   
   Look for:
   - **Red bars/nodes** = Critical path (longest execution sequence)
   - **Long horizontal bars** = Time-consuming methods
   - **Deep nesting** = Complex call hierarchies

## Try the Sample Logs

We've included two sample log files:

1. **`sample_logs/test_log.txt`** - Simple CPQ quote process
2. **`sample_logs/cpq_complex_log.txt`** - Complex quote with many nested calls

Try analyzing both to see different perspectives!

## Analyzing Your Own Logs

### Required Log Format

Your log file needs:
- One line per event (ENTER or EXIT)
- Unix timestamp with milliseconds
- Method name

### Supported Formats

```
# Format 1 (Recommended)
1698765432.123 | ENTER | MethodName
1698765432.234 | EXIT | MethodName

# Format 2
[1698765432.123] ENTER MethodName
[1698765432.234] EXIT MethodName

# Format 3
1698765432.123 ENTER: MethodName
1698765432.234 EXIT: MethodName

# Format 4
1698765432.123 - ENTER - MethodName
1698765432.234 - EXIT - MethodName
```

### Example: Generating Logs in Your Code

**Salesforce Apex Example:**
```apex
public static Long getCurrentTimestamp() {
    return System.currentTimeMillis();
}

public void logPerformance(String methodName, String eventType) {
    Long timestamp = getCurrentTimestamp();
    System.debug(timestamp + ' | ' + eventType + ' | ' + methodName);
}

public void myMethod() {
    logPerformance('MyClass.myMethod', 'ENTER');
    try {
        // Your code here
    } finally {
        logPerformance('MyClass.myMethod', 'EXIT');
    }
}
```

## Common Issues

### "No data could be parsed"
- ✅ Check your log format matches one of the supported patterns
- ✅ Ensure timestamps are in Unix format (milliseconds)
- ✅ Verify ENTER and EXIT pairs match

### Dependencies not installing
```bash
# Upgrade pip first
pip install --upgrade pip

# Then try again
pip install -r requirements.txt
```

### Application won't start
```bash
# Verify Python version
python3 --version  # Should be 3.10+

# Check if tkinter is available
python3 -c "import tkinter"  # Should have no errors
```

On macOS, if tkinter is missing:
```bash
# Install Python with tkinter support via Homebrew
brew install python-tk@3.10
```

## Tips for Best Results

1. **Filter Large Logs**: For logs > 10,000 lines, consider filtering to specific timeframes
2. **Use Meaningful Method Names**: Clear naming helps in visualization
3. **Balance Detail**: Too many method calls can clutter visualizations
4. **Critical Path Focus**: Pay attention to methods highlighted in red
5. **Export Charts**: Use the toolbar to save charts as images

## What's Next?

- Analyze your own performance logs
- Compare performance across different runs
- Identify optimization opportunities
- Share visualizations with your team

## Need Help?

- Check the full **README.md** for detailed documentation
- Review sample log files for format examples
- Ensure your logs have proper ENTER/EXIT pairing

## Keyboard Shortcuts

- **Ctrl+O** / **Cmd+O**: Open file (when implemented)
- **Mouse wheel**: Zoom in/out on charts
- **Click+Drag**: Pan around charts
- **Home button** (on toolbar): Reset zoom

---

**Happy Analyzing! 🚀**

Found a bottleneck? Now you can fix it!

