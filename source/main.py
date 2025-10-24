#!/usr/bin/env python3
"""
Performance Log Analyzer - Main Entry Point
Analyzes Salesforce Industries CPQ Quoting performance logs
"""

import sys
from ui.app import PerfLogAnalyzerApp

def main():
    """Main entry point for the application"""
    app = PerfLogAnalyzerApp()
    app.run()

if __name__ == "__main__":
    main()

