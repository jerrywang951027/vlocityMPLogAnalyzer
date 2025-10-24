"""
Log Parser Module
Parses performance log files with method entry/exit and nested calls
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd


class LogEntry:
    """Represents a single log entry"""
    
    def __init__(self, timestamp: float, method_name: str, event_type: str, 
                 level: int, line_number: int, raw_line: str):
        self.timestamp = timestamp
        self.method_name = method_name
        self.event_type = event_type  # 'ENTER' or 'EXIT'
        self.level = level
        self.line_number = line_number
        self.raw_line = raw_line
        self.duration = None
        self.parent_id = None
        self.id = None


class MethodCall:
    """Represents a complete method call with entry and exit"""
    
    def __init__(self, method_name: str, start_time: float, end_time: float,
                 level: int, call_id: int, parent_id: Optional[int] = None):
        self.method_name = method_name
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.level = level
        self.call_id = call_id
        self.parent_id = parent_id
        self.children = []
        self.self_time = None  # Time spent in this method excluding children
        
    def calculate_self_time(self):
        """Calculate time spent in this method excluding child calls"""
        child_time = sum(child.duration for child in self.children)
        self.self_time = self.duration - child_time
        
    def to_dict(self):
        """Convert to dictionary for DataFrame"""
        return {
            'call_id': self.call_id,
            'parent_id': self.parent_id,
            'method_name': self.method_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'self_time': self.self_time,
            'level': self.level,
            'num_children': len(self.children)
        }


class LogParser:
    """Parser for performance log files"""
    
    # Common log patterns - can be extended
    PATTERNS = [
        # Salesforce Apex Debug Log Pattern for CODE_UNIT (the true roots)
        # Format: 13:22:50.0 (2076453)|CODE_UNIT_STARTED|[EXTERNAL]|apex://vlocity_cmt.ComponentController/ACTION$handleData
        # Or:     13:22:50.0 (3919240262)|CODE_UNIT_FINISHED|vlocity_cmt.CpqApexCallable (no [EXTERNAL] on FINISHED)
        r'(\d{2}:\d{2}:\d{2}\.\d+)\s*\((\d+)\)\|CODE_UNIT_(STARTED|FINISHED)\|(?:[^\|]*\|)?(.+)$',
        
        # Salesforce Apex Debug Log Pattern for METHOD calls
        # Format: 13:22:50.0 (74727139)|METHOD_ENTRY|[1]|01p5j00000Js5fA|vlocity_cmt.ComponentController.ComponentController()
        # or:     13:22:50.0 (23803819397)|METHOD_EXIT|[9]||System.UserInfo.getOrganizationId()
        # Note: Number in parentheses is nanoseconds since log start, [N] is stack level
        r'(\d{2}:\d{2}:\d{2}\.\d+)\s*\((\d+)\)\|METHOD_(ENTRY|EXIT)\|\[(\d+)\]\|[^\|]*\|(.+)$',
        
        # Pattern 1: timestamp | ENTER/EXIT | MethodName
        r'(\d+(?:\.\d+)?)\s*\|\s*(ENTER|EXIT)\s*\|\s*(.+)',
        # Pattern 2: [timestamp] ENTER/EXIT MethodName
        r'\[(\d+(?:\.\d+)?)\]\s*(ENTER|EXIT)\s+(.+)',
        # Pattern 3: timestamp ENTER/EXIT: MethodName
        r'(\d+(?:\.\d+)?)\s+(ENTER|EXIT):\s*(.+)',
        # Pattern 4: timestamp - ENTER/EXIT - MethodName
        r'(\d+(?:\.\d+)?)\s*-\s*(ENTER|EXIT)\s*-\s*(.+)',
    ]
    
    def __init__(self):
        self.entries: List[LogEntry] = []
        self.method_calls: List[MethodCall] = []
        self.call_stack = []
        self.call_id_counter = 0
        self.code_unit_depth = 0  # Track nesting depth of CODE_UNIT events
        self.unclosed_methods: List[tuple] = []  # Track methods without EXIT
        self.exceptions_log = []  # Log of parsing exceptions
        
    def parse_file(self, file_path: str) -> pd.DataFrame:
        """
        Parse a log file and return a DataFrame with method calls
        
        Args:
            file_path: Path to the log file
            
        Returns:
            DataFrame with parsed method calls
        """
        self.entries = []
        self.method_calls = []
        self.call_stack = []
        self.call_id_counter = 0
        self.code_unit_depth = 0
        self.unclosed_methods = []
        self.exceptions_log = []
        
        # Read and parse log file
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                    
                entry = self._parse_line(line, line_num)
                if entry:
                    self.entries.append(entry)
        
        # Build method call tree
        self._build_call_tree()
        
        # Write exceptions log
        self._write_exceptions_log()
        
        # Convert to DataFrame
        if not self.method_calls:
            return pd.DataFrame()
            
        df = pd.DataFrame([call.to_dict() for call in self.method_calls])
        return df
    
    def _parse_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line"""
        for i, pattern in enumerate(self.PATTERNS):
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                
                # Handle Salesforce CODE_UNIT format (pattern 0)
                if i == 0 and len(groups) == 4:
                    time_str, nanoseconds_str, event_type, method_name = groups
                    timestamp = float(nanoseconds_str) / 1000000.0  # Convert nanoseconds to milliseconds
                    # CODE_UNIT level is based on nesting depth
                    if event_type == 'STARTED':
                        level = self.code_unit_depth
                        self.code_unit_depth += 1
                        event_type = 'ENTRY'
                    elif event_type == 'FINISHED':
                        self.code_unit_depth = max(0, self.code_unit_depth - 1)
                        level = self.code_unit_depth  # Use current depth after decrement
                        event_type = 'EXIT'
                    else:
                        level = self.code_unit_depth
                        event_type = event_type.upper()
                
                # Handle Salesforce METHOD format (pattern 1) - now with level
                elif i == 1 and len(groups) == 5:
                    time_str, nanoseconds_str, event_type, level_str, method_name = groups
                    timestamp = float(nanoseconds_str) / 1000000.0  # Convert nanoseconds to milliseconds
                    level = int(level_str)  # Use the actual stack level from log
                    event_type = event_type.upper()  # ENTRY or EXIT
                    
                # Handle other formats
                elif len(groups) == 3:
                    timestamp_str, event_type, method_name = groups
                    timestamp = float(timestamp_str)
                    event_type = event_type.upper()
                else:
                    continue
                
                # Level is now set in pattern matching above (from log's [N] indicator)
                # Default to 0 if not set
                if 'level' not in locals():
                    level = len(self.call_stack)
                
                # Clean method name: remove ID prefix like "01p5j00000Js5fA|"
                clean_method_name = method_name.strip()
                if '|' in clean_method_name and clean_method_name.split('|')[0].strip().startswith('01'):
                    # Remove the ID prefix
                    clean_method_name = '|'.join(clean_method_name.split('|')[1:])
                
                return LogEntry(
                    timestamp=timestamp,
                    method_name=clean_method_name,
                    event_type=event_type.upper(),
                    level=level,
                    line_number=line_number,
                    raw_line=line
                )
        
        return None
    
    def _build_call_tree(self):
        """Build the method call tree from log entries using level indicators"""
        # Stack at each level: level_stacks[N] = [(entry, call_id, method_call), ...]
        level_stacks = {}
        
        for entry in self.entries:
            if entry.event_type == 'ENTRY':
                # Reserve a call_id for this entry
                current_call_id = self.call_id_counter
                self.call_id_counter += 1
                
                # Don't assign parent yet - will do it after all methods are collected
                parent_id = None
                
                # Create a placeholder (will update end_time and duration on EXIT)
                method_call = MethodCall(
                    method_name=entry.method_name,
                    start_time=entry.timestamp,
                    end_time=entry.timestamp,
                    level=entry.level,
                    call_id=current_call_id,
                    parent_id=parent_id
                )
                
                # Push onto stack for this level
                if entry.level not in level_stacks:
                    level_stacks[entry.level] = []
                level_stacks[entry.level].append((entry, current_call_id, method_call))
                
            elif entry.event_type == 'EXIT':
                # Find matching ENTRY on stack at this level
                if entry.level in level_stacks and level_stacks[entry.level]:
                    for i in range(len(level_stacks[entry.level]) - 1, -1, -1):
                        enter_entry, call_id, method_call = level_stacks[entry.level][i]
                        if enter_entry.method_name == entry.method_name:
                            # Update the method call with exit time
                            method_call.end_time = entry.timestamp
                            method_call.duration = entry.timestamp - enter_entry.timestamp
                            
                            # Add to completed calls (properly closed)
                            self.method_calls.append(method_call)
                            
                            # Remove from stack
                            level_stacks[entry.level].pop(i)
                            break
        
        # Handle unclosed entries:
        # KEEP level-0 CODE_UNITs as roots (they're entry points), but remove others
        unclosed_parent_map = {}
        for level in sorted(level_stacks.keys()):
            for enter_entry, call_id, method_call in level_stacks[level]:
                # Keep CODE_UNIT (level 0) even if unclosed - it's the root
                if enter_entry.level == 0:
                    # Calculate end time from last timestamp in log
                    method_call.end_time = self.entries[-1].timestamp if self.entries else enter_entry.timestamp
                    method_call.duration = method_call.end_time - enter_entry.timestamp
                    self.method_calls.append(method_call)
                    
                    # Log this exception
                    self.exceptions_log.append({
                        'description': 'Missing closing line (METHOD_EXIT) - KEPT as root',
                        'example': enter_entry.raw_line,
                        'method_name': enter_entry.method_name,
                        'timestamp': enter_entry.timestamp,
                        'level': enter_entry.level,
                        'call_id': call_id,
                        'parent_id': method_call.parent_id,
                        'solution': 'Kept as root, duration calculated from log end'
                    })
                else:
                    # Remove non-root unclosed methods
                    # Log this exception
                    self.exceptions_log.append({
                        'description': 'Missing closing line (METHOD_EXIT)',
                        'example': enter_entry.raw_line,
                        'method_name': enter_entry.method_name,
                        'timestamp': enter_entry.timestamp,
                        'level': enter_entry.level,
                        'call_id': call_id,
                        'parent_id': method_call.parent_id,
                        'solution': 'Removed from tree, children reparented to nearest closed ancestor or root'
                    })
                    
                    # Track for reparenting
                    unclosed_parent_map[call_id] = method_call.parent_id
        
        # Now assign parents using OPTIMIZED TIME CONTAINMENT with stack-based algorithm
        # Complexity: O(N log N) instead of O(N²)
        # Strategy: Maintain a stack of active (not yet ended) calls
        sorted_calls = sorted(self.method_calls, key=lambda x: x.start_time)
        call_map = {c.call_id: c for c in sorted_calls}
        
        # Find level-0 root (CODE_UNIT)
        level_0_root = next((c for c in sorted_calls if c.level == 0), None)
        
        # Stack-based parent assignment - O(N log N)
        # Stack contains currently active calls (started but not yet ended)
        active_stack = []
        
        for call in sorted_calls:
            if call.level == 0:
                call.parent_id = None
                active_stack.append(call)
                continue
            
            # Remove calls from stack that have ended before this call starts
            # These can no longer be parents of future calls
            while active_stack and active_stack[-1].end_time <= call.start_time:
                active_stack.pop()
            
            # Find parent: the most recent active call that fully contains this call
            # Search from the end of the stack (most recent) backwards
            best_parent = None
            for i in range(len(active_stack) - 1, -1, -1):
                candidate = active_stack[i]
                # Parent must fully contain this call (start before or at, end after or at)
                if (candidate.start_time <= call.start_time and
                    call.end_time <= candidate.end_time and
                    candidate.call_id != call.call_id):
                    best_parent = candidate
                    break  # Found the immediate parent (most recent that contains this call)
            
            # If no parent found and we have a level-0 root, attach to it
            if best_parent is None and level_0_root and level_0_root.start_time <= call.start_time < level_0_root.end_time:
                best_parent = level_0_root
            
            call.parent_id = best_parent.call_id if best_parent else None
            
            # Add this call to the active stack
            active_stack.append(call)
        
        # Build parent-child relationships
        self._build_relationships()
        
        # Calculate self time for each method
        for call in self.method_calls:
            call.calculate_self_time()
        
    def _write_exceptions_log(self):
        """Write exceptions to logExceptionRules.txt"""
        if not self.exceptions_log:
            return
            
        with open('logExceptionRules.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LOG PARSING EXCEPTIONS\n")
            f.write("=" * 80 + "\n\n")
            
            for i, exc in enumerate(self.exceptions_log, 1):
                f.write(f"Exception #{i}:\n")
                f.write(f"  Description: {exc['description']}\n")
                f.write(f"  Method: {exc['method_name']}\n")
                f.write(f"  Level: {exc['level']}\n")
                f.write(f"  Timestamp: {exc['timestamp']:.2f}ms\n")
                f.write(f"  Example: {exc['example'][:120]}\n")
                f.write(f"  Solution: {exc['solution']}\n")
                f.write("\n")
            
            f.write(f"\nTotal exceptions: {len(self.exceptions_log)}\n")
    
    def _build_relationships(self):
        """Build parent-child relationships in method calls"""
        # Create a map of call_id to method call
        call_map = {call.call_id: call for call in self.method_calls}
        
        # Build children lists
        for call in self.method_calls:
            if call.parent_id is not None and call.parent_id in call_map:
                parent = call_map[call.parent_id]
                parent.children.append(call)
    
    def get_call_tree(self) -> List[MethodCall]:
        """Get the root method calls (top-level calls)"""
        # Find methods whose parent_id is None OR points to non-existent parent
        call_ids = {call.call_id for call in self.method_calls}
        roots = []
        for call in self.method_calls:
            if call.parent_id is None or call.parent_id not in call_ids:
                roots.append(call)
        return roots
    
    def get_critical_path(self) -> List[MethodCall]:
        """
        Identify the critical path - the sequence of method calls
        that took the longest time
        """
        if not self.method_calls:
            return []
        
        critical_path = []
        
        # Start with the longest top-level call
        roots = self.get_call_tree()
        if not roots:
            return []
        
        current = max(roots, key=lambda x: x.duration)
        critical_path.append(current)
        
        # Follow the longest child at each level
        while current.children:
            current = max(current.children, key=lambda x: x.duration)
            critical_path.append(current)
        
        return critical_path

