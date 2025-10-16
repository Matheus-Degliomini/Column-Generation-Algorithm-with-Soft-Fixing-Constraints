"""
Random instance generator for the cutting-stock / set-covering problem family.

This script produces synthetic data files compatible with the Instance parser
and the Column Generation + Soft Fixing algorithm. It systematically varies
the number of item types, average demand levels, and width distributions to
create multiple randomized test cases.

Purpose:
• Automate generation of benchmark datasets with controlled variability.
• Produce .txt files readable by Instance.py for algorithm testing.

Core parameters:
• L (int): Stock roll (bin) capacity; constant for all generated files.
• m (list[int]): Candidate values for the number of item types (e.g., 10, 20, 30, 40, 50).
• d_bar (list[int]): Average demand multipliers (e.g., 10, 20, 30, 40, 50).
• type_dist (list[int]): Distribution selector controlling item width range:
1 — widths uniformly drawn from [1, 2500]
2 — widths uniformly drawn from [1, 5000]
3 — widths uniformly drawn from [1, 7500]
4 — widths uniformly drawn from [1, 10000]

Workflow summary:
1. Iterate over all combinations of (m, d_bar, type_dist).
2. For each combination:
• Draw random item widths according to the selected range.
• Generate random proportions and scale them to obtain integer demands
that sum to the total demand T = m * d_bar.
• Adjust zero-demand entries by adding 1 to guarantee feasibility.
• Write the instance to a text file.

Output format:
• Each file named Instance_size_<m>_d_<d_bar>_type_<type_dist>.txt
• First line: roll capacity (L).
• Following lines: pairs of <width>\t<demand> for each item type.

File contents are directly compatible with Instance.py, which reads them
into attributes W, w, and d.

Randomness:
• Uses numpy.random.randint for reproducibility within NumPy’s RNG state.
• Each call produces different instances unless a seed is fixed externally.

Notes:
• No explicit seed is set in this script (use np.random.seed() manually).
• The generated demands are floored and adjusted to ensure total demand T.
• Designed for experimental evaluation of CG and soft fixing behavior.
"""

import numpy as np
import os

L = 10000
m = [10, 20, 30, 40, 50]
d_bar = [10, 20, 30, 40, 50]
type_dist = [1,2,3,4]

for l in m:
    for j in d_bar:
        for k in type_dist:
            randnum = []
            w = []
            d = []
            T = l * j

            for i in range(l):
                if k == 1:
                    w.append(np.random.randint(1,2501))
                elif k== 2:
                    w.append(np.random.randint(1,5001))
                elif k == 3:
                    w.append(np.random.randint(1,7501))
                elif k == 4:
                    w.append(np.random.randint(1,10001))
                else:
                    print('Error: distribution type not specified.')

            for i in range(l):
                randnum.append(np.random.randint(T + 1))
                
            for i in range(l-1):
                d.append(np.floor(randnum[i]/sum(randnum) * T)  )

            for q in range(l-1):
                if d[q] == 0.0:
                    d[q] += 1


            d.append(T - sum(d))

            # generate txt file

            out_dir = os.path.join(os.path.dirname(__file__), '1D-Cutting Stock Problem')
            os.makedirs(out_dir, exist_ok=True)
            file_path = os.path.join(out_dir, f'Instance_size_{l}_d_{j}_type_{k}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'{L}')
                for i in range(l):
                    f.write(f'\n{w[i]}\t{int(d[i])}')