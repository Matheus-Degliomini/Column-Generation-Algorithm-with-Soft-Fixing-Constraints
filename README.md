# 🧩 Column Generation with Soft Fixing Constraints (CG-SF)

**Master Problem Solver for Cutting-Stock and Set-Covering Problems**

This repository implements a two-stage **Column Generation (CG)** algorithm combined with several **Soft Fixing (SF)** strategies for solving large-scale **cutting-stock / set-covering formulations**.  
It was developed as part of a **Master’s dissertation** in Systems and Computing Engineering (PESC/COPPE/UFRJ).

---

## 📚 Academic Context

**Author:** Matheus Degliomini Silva  
**Supervisors:** Prof. Abilio Pereira de Lucena Filho, Prof. Pedro Henrique González Silva  
**Institution:** Graduate Program in Systems and Computing Engineering (PESC),  
COPPE — Federal University of Rio de Janeiro (UFRJ)  
**Research Group:** Optimization Laboratory (Labotim)  
**Version:** 1.0 — October 2025  
**License:** Uses the *academic license* of the **Gurobi Optimizer**.  
This repository is intended **for research and educational purposes only**.

---

## Repository layout

- `src/`
  - `main.py` — main driver (CLI). Usage: `python main.py <instance> <soft_type>`.
  - `ColGenSF.py` — implementation of the `MP` (Master Problem) class with
    column generation and multiple soft-fixing routines.
  - `Instance.py` — small parser for instance files (format described below).
- `Examples/`
  - `instance_generator.py` — random instance generator (writes files to
    `Examples/1D-Cutting Stock Problem/`).
- `src/Execution Reports/` — runtime directory where `MP` writes
  `Report_<instance>.txt` files.

## Requirements

- Python 3.8+  
- NumPy (`numpy`)  
- Gurobi Optimizer and its Python interface (`gurobipy`) — a valid Gurobi
  academic license is required to run optimization routines.

Quick install example (PowerShell):

```powershell
python -m pip install --upgrade pip
pip install numpy
# If available for your platform, you can install the Python wheel for gurobipy:
# pip install gurobipy
# Otherwise follow Gurobi's installation guide to install the Python package
# and configure the license.
```

Note: `gurobipy` may not be available via public PyPI for all platforms. If
`pip install gurobipy` fails, follow Gurobi's documentation to install the
Python bindings and set the license file.

## Instance file format

The `Instance.py` parser expects a plain text file with the following layout:

1. First line: roll/bin capacity W (float or int).
2. Each subsequent line: two numbers `w_i d_i` (width, demand) separated by
   whitespace, one item type per line.

Example (`instance.txt`):

```
10000
250 10
500 5
750 8
```

The instance generator `Examples/instance_generator.py` produces compatible
instances under `Examples/1D-Cutting Stock Problem/` with filenames like
`Instance_size_<m>_d_<d_bar>_type_<type_dist>.txt`.

## How to run

Open PowerShell and run the `main.py` script providing the instance file path
and a soft-fixing type code (0–9):

```powershell
# Example: run with a generated instance using soft-fixing type 3
python .\src\main.py .\Examples\1D-Cutting Stock Problem\Instance_size_10_d_10_type_1.txt 3

# Example: run baseline without soft-fixing
python .\src\main.py .\Examples\1D-Cutting Stock Problem\Instance_size_10_d_10_type_1.txt 0
```

Soft-fixing type codes (as implemented in `main.py`):

- `0` — No soft fixing (baseline)
- `1` — Type-1
- `2` — Type-2 (per-item)
- `3` — Type-3 (with incremental CG variant)
- `4` — Type-4 (IP-active patterns, per-item)
- `5` — Type-5 (pattern-wise lower bounds from IP)
- `6` — Type-6 (aggregate LP-active patterns)
- `7` — Type-4 followed by Type-5
- `8` — Type-5 followed by Type-4
- `9` — Type-7 (penalize underused IP patterns)

For detailed help, run:

```powershell
python .\src\main.py --help
```

## Output and reports

- The program prints logs and iteration statistics to the console (columns
  added, LP/IP objectives, timing, etc.).
- A textual report is written to `src/Execution Reports/Report_<instance>.txt`.

## Notes and troubleshooting

- Ensure Gurobi is installed, the Python interface (`gurobipy`) is available
  to your interpreter, and the license is configured before running.
- If you get an "instance file not found" error, check the path and filename
  (the driver checks `os.path.isfile`).
- Use `Examples/instance_generator.py` to create randomized test instances.

## Author and license

Developed by Matheus Degliomini Silva as part of a Master's dissertation
(PESC/COPPE/UFRJ). The solver Gurobi is subject to its academic license; use
of this code requires compliance with Gurobi's licensing terms.

## Citation

If you use this code for research, please cite the author and the academic
context (M.Sc. dissertation of Matheus Degliomini Silva — Labotim, UFRJ).

---


