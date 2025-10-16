"""
Column Generation with Soft Fixing — Main driver script.

This script orchestrates a two-stage workflow for a cutting-stock / set-covering
formulation solved via Column Generation (CG) and optional Soft Fixing (SF)
stabilization strategies. It:
    • builds the initial Master Problem (MP) and runs CG to obtain an LP solution,
    • solves the Integer MP,
    • repeatedly applies the chosen soft fixing variant to guide further CG rounds,
    • updates the soft fixing intensity (alpha) until termination, and
    • prints and logs timing and solution statistics.

-------------------------------------------------------------------------------
Authors and Academic Context:
    Developed as part of the Master's dissertation of
        Matheus Degliomini Silva
    under the supervision of
        Prof. Abilio Pereira de Lucena Filho
        and Prof. Pedro Henrique González Silva
    at the Graduate Program in Systems and Computing Engineering (PESC),
    COPPE — Federal University of Rio de Janeiro (UFRJ).

    Research conducted within the Optimization Laboratory (Labotim).

Version:
    1.0 — October 2025

License:
    This code uses the academic license of the Gurobi Optimizer.
    Intended for research and educational purposes only.
-------------------------------------------------------------------------------

Command-line interface:
    python main.py <instance_path> <soft_type>

Arguments:
    instance_path (str): Path or identifier used by Instance.Instance to load
        model data (number of item types, widths, demands, capacity, name, etc.).
    soft_type (str): Soft fixing strategy selector:
        '0' — No soft fixing (baseline)
        '1' — Type-1 soft fixing
        '2' — Type-2 soft fixing (per-item constraints)
        '3' — Type-3 soft fixing + incremental CG variant
        '4' — Type-4 soft fixing (IP-active patterns, per-item)
        '5' — Type-5 soft fixing (pattern-wise lower bounds from IP)
        '6' — Type-6 soft fixing (aggregate LP-active patterns)
        '7' — Type-4 followed by Type-5 in sequence
        '8' — Type-5 followed by Type-4 in sequence
        '9' — Type-7 soft fixing (penalize underused IP patterns)
      Any other value triggers an immediate exit with an error.

Workflow summary:
    • Build model and run initial Column Generation (LP relaxation).
    • Solve the integer MP once to initialize IP baselines.
    • Enter a loop: apply the selected soft fixing, run CG again, remove the
      soft fixing constraints added in this round, solve the integer MP, update
      alpha (and internal flags), report iteration statistics, and stop when
      alpha update returns "End".
    • After finishing, report bounds and total times.

Outputs / side effects:
    • Console prints with iteration logs and timing.
    • A report text file bound to the instance name (e.g., "Report_<name>.txt")
      written via the MP object.
    • Number of newly added columns at key stages; final bounds via bounds_return().

Performance & reproducibility:
    • Column generation and IP solves are done with Gurobi via ColGenSF.MP.
    • Random seeds for any randomized parts are set inside the MP class.
    • Timings: reports separate durations for CG and CG+SF and their sum.

Error handling:
    • Exits with a descriptive message if an unknown soft_type is provided.
    • Assumes the instance file/path can be loaded by Instance.Instance.

See also:
    • ColGenSF.MP for the Master Problem implementation, soft fixing variants,
      and reporting utilities.
"""


import sys
import os
import Instance 
import ColGenSF 
from time import time
import copy


def print_help() -> None:
    """
    Display usage information and soft fixing options for the Column Generation driver.
    """

    print("=" * 75)
    print("Column Generation with Soft Fixing — Master Problem")
    print("---------------------------------------------------")
    print("This program solves a cutting-stock / set-covering formulation using")
    print("Column Generation (CG) combined with optional Soft Fixing (SF) strategies.\n")

    print("USAGE:")
    print("    python main.py <instance_path> <soft_type>\n")
    print("ARGUMENTS:")
    print("    <instance_path> : Path to the instance file (e.g., './instances/test.txt')")
    print("    <soft_type>     : Integer code for the soft fixing strategy (0–9)\n")

    print("SOFT FIXING TYPES:")
    print("    0 — No soft fixing (baseline)")
    print("    1 — Type-1 soft fixing")
    print("    2 — Type-2 soft fixing (per-item constraints)")
    print("    3 — Type-3 soft fixing + incremental CG variant")
    print("    4 — Type-4 soft fixing (IP-active patterns, per-item)")
    print("    5 — Type-5 soft fixing (pattern-wise lower bounds from IP)")
    print("    6 — Type-6 soft fixing (aggregate LP-active patterns)")
    print("    7 — Type-4 followed by Type-5 in sequence")
    print("    8 — Type-5 followed by Type-4 in sequence")
    print("    9 — Type-7 soft fixing (penalize underused IP patterns)\n")

    print("EXAMPLES:")
    print("    python main.py ./instances/CSP_10_50_1.txt 3")
    print("    python main.py ./instances/sample.txt 0\n")

    print("AUTHORS AND CONTEXT:")
    print("    Developed by Matheus Degliomini Silva")
    print("    Supervisors: Abilio P. de Lucena Filho, Pedro H. González Silva")
    print("    PESC/COPPE/UFRJ — Optimization Laboratory (Labotim)")
    print("    Using the academic license of the Gurobi Optimizer\n")

    print("Version: 1.0 — October 2025")
    print("=" * 75)





columns_before = 0
columns_after = 0
new_columns = 0
k = 0
argv = sys.argv


if '--help' in argv or '-h' in argv:
    print_help()
    sys.exit(0)


if len(argv) < 3:
    print("❌ Error: Some arguments are missing. Try again.\n\n")
    print("Usage: python main.py <instance_path> <soft_type>\n\n")
    sys.exit(1)


if not os.path.isfile(argv[1]):
    print(f"❌ Error: Instance file '{argv[1]}' not found.\n")
    print("Please check the file path or name and try again.\n\n")
    print("Usage: python main.py <instance_path> <soft_type>\n\n")
    sys.exit(1)

if argv[2] not in ['0','1','2','3','4','5','6','7','8','9']:
    sys.exit('❌ Error: Soft Fixing type not found.\n soft_type parameter must be an integer between 0 and 9.\n\n usage: python main.py <instance_path> <soft_type>\n\n')

inst = Instance.Instance(argv[1])
print(f"Loading instance: {os.path.abspath(argv[1])}")
print(inst)
soft_type = argv[2]
model = ColGenSF.MP(inst)
print(f'K = {k}')
begin_1 = time()
print('\nBuilding model...\n')
model.build_model()
columns_before = copy.copy(columns_after)
columns_after = len(model.pattern[0])
new_columns = columns_after - columns_before

print("Model built.\n")
print(f'Initial number of columns: {new_columns}')
model.file.write(f'Initial number of columns: {new_columns}\n')


print('Starting column generation...\n')
model.column_generation()
print('Column generation step finished.\n')
print('Solving Integer Master Problem ...\n')
model.solve_IP()
columns_before = copy.copy(columns_after)
columns_after = len(model.pattern[0])
new_columns = columns_after - columns_before
print(f'Number of columns after column generation: {new_columns}')
model.file.write(f'Number of columns after column generation: {new_columns}\n')


end_1 = time()
time_1 = end_1 - begin_1
model.print_solution()
model.report_solution(k)



print('Starting Column Generation with Soft Fixing ...\n')
begin_2 = time()
while True:
    
    k += 1
    print(f'K = {k}')
    if soft_type == '0':
        pass
    elif soft_type == '1':
        model.soft_fixing()
        model.column_generation()
        model.remove_soft_fixing()
    elif soft_type == '2':
        model.soft_fixing_type2()
        model.column_generation()
        model.remove_soft_fixing_type2()
    elif soft_type == '3':
        model.soft_fixing_type3()
        model.column_generation_2()
        while model.column_found == True:
            model.remove_soft_fixing()
            model.soft_fixing_type3()
            model.column_generation_2()
        
        model.remove_soft_fixing()
        
    elif soft_type == '4':
        model.soft_fixing_type4()
        model.column_generation()
        model.remove_soft_fixing_type2()
    elif soft_type == '5':
        model.soft_fixing_type5()
        model.column_generation()
        model.remove_soft_fixing_type5()
    elif soft_type == '6':
        model.soft_fixing_type6()
        model.column_generation()
        model.remove_soft_fixing()
    elif soft_type == '7':
        model.soft_fixing_type4()
        model.column_generation()
        model.remove_soft_fixing_type2()
        
        model.soft_fixing_type5()
        model.column_generation()
        model.remove_soft_fixing_type5()
    elif soft_type == '8':
        model.soft_fixing_type5()
        model.column_generation()
        model.remove_soft_fixing_type5()

        model.soft_fixing_type4()
        model.column_generation()
        model.remove_soft_fixing_type2()

    elif soft_type == '9':
        model.soft_fixing_type7()
        model.column_generation()
        model.remove_soft_fixing_type2()
    else:
        sys.exit('❌ Error: Soft Fixing type not found.\n soft_type parameter must be an integer between 0 and 9.\n usage: python main.py <instance_path> <soft_type>\n')
        
    model.solve_IP()
    alpha = model.update_alpha()
    model.report_solution(k)
    if alpha == "End":
        end_2 = time()
        time_2 = end_2 - begin_2
        model.print_solution()
        columns_before = copy.copy(columns_after)
        columns_after = len(model.pattern[0])
        new_columns = columns_after - columns_before
        print(f'Number of columns after Soft Fixing stage: {new_columns}')
        model.file.write(f'Number of columns after Soft Fixing stage: {new_columns}\n')
        #input()
        break
    
print('Column Generation with Soft Fixing finished.\n')

model.bounds_return()


print('='*50)
model.file.write('='*50 + '\n')
print(f'Column Generation time: {time_1:.4f} seconds.\nColumn Generation with Soft Fixing time: {time_2:.4f} seconds.\nTotal time: {time_1 + time_2:.4f} seconds.')
model.file.write(f'Column Generation time: {time_1:.4f} seconds.\nColumn Generation with Soft Fixing time: {time_2:.4f} seconds.\nTotal time: {time_1 + time_2:.4f} seconds.\n')

