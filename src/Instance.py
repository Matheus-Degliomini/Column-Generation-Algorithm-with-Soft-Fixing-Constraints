"""
Instance file parser for cutting-stock / set-covering datasets.

This module defines the Instance class, a lightweight loader that parses a
plain-text data file into structured attributes consumed by the Column
Generation + Soft Fixing workflow.

Purpose:
• Read a problem file from disk, parse numeric data, and expose fields that
describe the instance (capacity, item sizes, demands, counts, and name).

Expected file format (whitespace-separated, one instance per file):
1) First line: a single number W (float) — the roll/bin capacity.
2) Lines 2..N: pairs of numbers w_i d_i (floats) — item size and demand.

Parsing behavior:
• self.W is set from the first line.
• self.w and self.d are lists built from subsequent lines (sizes, demands).
• All numeric entries are parsed as float.
• self.I is the number of item types, i.e., len(self.w).
• self.name is derived from the input filename’s basename without extension.
• The file is opened in read mode, fully read, and closed immediately.

Assumptions / limitations:
• The input file must contain at least two lines (one header + ≥1 item).
• Lines must be whitespace-separated numbers; no headers or comments are expected.
• No explicit validation against negative or non-numeric values is performed.
• The module relies on OS filesystem access and a valid path.

Object representation:
• __repr__ returns a human-readable multi-line summary containing:
- instance name,
- “Larger piece” (capacity W),
- each item with index, w[i] (size), and d[i] (demand).

Exposed attributes:
• file_name: str — full path passed to the constructor.
• W: float — capacity from the first line.
• w: list[float] — item sizes.
• d: list[float] — item demands.
• I: int — number of item types (len(w)).
• name: str — basename of the instance file without extension.

Usage:
• Instantiate with the file path to load and make the fields available to
model builders (e.g., ColGenSF.MP) and driver scripts (main.py).
"""

import os

class Instance:
    def __init__(self, filename):
        self.file_name = filename
        file = open(f'{self.file_name}','r')
        data =  [[float(num) for num in line.split()] for line in file]
        file.close()
        self.W = data[0][0]
        self.w = []
        self.d = []

        for i in range(1, len(data)):
            self.w.append(data[i][0])
            self.d.append(data[i][1])

        self.I = len(self.w)
        self.name = os.path.basename(self.file_name)
        self.name = self.name[0:-4]

    def __repr__(self):
        result = '='*50
        result += f"\nName: {self.name}\n"
        result += f"Larger piece: {self.W}\n"
        for i in range(len(self.w)):
            result += f"Piece: {i+1}\tSize : {self.w[i]}\tDemand: {self.d[i]}\n"
        
        return result
    
    
    
