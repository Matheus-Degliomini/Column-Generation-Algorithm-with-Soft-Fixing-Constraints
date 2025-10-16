from gurobipy import *
import numpy as np
import time
import os

class MP:
    """
    Master Problem (MP) class implementing a Column Generation algorithm 
    with Soft Fixing constraints for a cutting stock or set-covering problem.

    This class builds and solves the master problem iteratively using Gurobi, 
    invokes a knapsack-type subproblem to generate new columns (patterns), 
    applies soft fixing strategies to guide the integer solution search, and 
    maintains statistics and reports about the process.

    Attributes:
        ins: Problem instance containing data such as number of items (I), 
            roll capacity (W), item widths (w), and demands (d).
        set_cover: Gurobi model for the master problem.
        x: List of Gurobi decision variables for each pattern.
        cons: List of Gurobi constraints ensuring demand satisfaction.
        pattern: Matrix of item–pattern relationships (list of lists of ints).
        P: Current number of patterns (columns).
        alpha: Soft fixing parameter (default = 0.9).
        beta: Secondary soft fixing parameter (default = 20).
        lb, best_lb: Current and best lower bounds.
        Z_IP, best_IP: Current and best integer program (IP) objective values.
        x_rel, x_IP: Relaxed and integer solutions of variable x.
        column_flag, column_found: Flags for column generation status.
        total_column, columns_added: Counters for column generation iterations.
        rounded: Number of rolls used in the rounded solution.
        """
 
    def __init__(self, ins: object) -> None:
        """
        Initialize the master problem for column generation with soft fixing.

        Args:
            ins (object): Problem instance containing item data, demands, 
                          and capacity information.
        """

        self.ins = ins
        self.alpha = 0.9
        self.Z_IP = np.inf
        self.best_IP = np.inf
        self.column_flag = False
        self.x_rel = []
        self.x_IP = []


        # ensure reports directory exists and open report file inside it
        reports_dir = os.path.join(os.path.dirname(__file__), 'Execution Reports')
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f'Report_{self.ins.name}.txt')
        self.file = open(report_path, 'w', encoding='utf-8')
        # ...existing code...

        self.file.write(f"Instance: {self.ins.name}\n")
        self.total_column = ins.I
        self.columns_added = 0
        self.rounded = 0
        self.best_lb = -np.inf
        self.lb = -np.inf
        self.column_found = False
        np.random.seed(123)
        self.psb_flag = False
        self.beta = 20


    def initial(self) -> list[list[float]]:
        """
        Build initial feasible patterns using single-item fills.

        Returns:
            List[List[float]]: Initial matrix of patterns, where each sublist 
            represents a feasible combination of items filling the roll.
        """
       
        self.M = []
        p = []
        for i in range(0,self.ins.I):
            aux = []
            for j in range(0, self.ins.I):
                aux.append(0)
            aux[i] = np.floor(min(self.ins.W /self.ins.w[i], self.ins.W ))
            p.append(aux)
    
        for i in range(self.ins.I):
            self.M.append(np.floor(min(self.ins.W /self.ins.w[i], self.ins.W )))

        
        return p



    def build_model(self) -> None:
        """
        Construct the initial master problem (set-cover model) in Gurobi.

        Defines variables, objective (minimize number of rolls), and 
        constraints ensuring that all demands are met by available patterns.
        """
        ins = self.ins
        self.pattern = self.initial()
        self.P = len(self.pattern)

        self.set_cover = Model("Master Problem")
       
        self.x = []
        for i in range(0, ins.I):
            self.x.append(self.set_cover.addVar(vtype = GRB.INTEGER, lb = 0, name = f'x_{i}'))
            

        obj = LinExpr()
        for i in range(0,ins.I):
            obj.addTerms(1, self.x[i])
        self.set_cover.setObjective(obj, GRB.MINIMIZE)

        self.cons = []
        for i in range(0,ins.I):
            restr = LinExpr()
            for j in range(0,self.P):
                restr.addTerms(self.pattern[i][j], self.x[j])
            self.cons.append(self.set_cover.addConstr(restr >= ins.d[i], f'Demand_{i}'))

    
    def knapsack(self, pi: list[float]) -> list[int] | str:
        """
        Solve the subproblem (integer knapsack) to generate a new column.

        Args:
            pi (List[float]): Dual prices of the master problem constraints.

        Returns:
            List[int]: New column (pattern) to add if the reduced cost is negative.
            str: 'End' if no improving column exists.
        """
        ins = self.ins 
        ks = Model("Subproblem")
        
        y = []
        for i in range(ins.I):
            y.append(ks.addVar(vtype = GRB.INTEGER, lb = 0, name = f'y_{i}'))
        
        #epsilon = np.random.rand(len(pi)) * 10e-3
        obj = LinExpr()
        for i in range(ins.I):
            obj.addTerms(pi[i], y[i])

        ks.setObjective(obj, GRB.MAXIMIZE)
        
        rest = LinExpr()
        for i in range(ins.I):
            rest.addTerms(ins.w[i], y[i])

        ks.addConstr(rest <= ins.W, 'Capacity')
        ks.setParam('OutputFlag', 0)
        ks.Params.LogToConsole = 0
        ks.optimize()
        Objetivo = ks.getObjective()
         
        c = []
        for i in range(ins.I):
            c.append(y[i].X)

        if Objetivo.getValue() > 1+10e-5:
            return c
        else: 
            return 'End'
        
    
    def column_generation(self) -> None:
        """
        Perform the standard column generation loop.

        Iteratively solves the LP relaxation of the master problem, 
        retrieves dual values, generates new columns via the knapsack 
        subproblem, and adds them to the model until no more columns 
        with negative reduced cost are found.
        """
        while True:
        
            self.relax_lp()
            self.set_cover.setParam("OutputFlag", 0)
            self.set_cover.Params.LogToConsole = 0
            self.set_cover.optimize()
            Objetivo = self.set_cover.getObjective()
            self.lb = Objetivo.getValue()
            if self.lb > self.best_lb:
                self.best_lb = self.lb

            

            pi = []
            for i in self.cons:
                pi.append(i.Pi)
                
            coluna = self.knapsack(pi)
            if self.psb_flag == True:
                for o in range(len(coluna)):
                    self.psb_report.write(f' {coluna[o]} ')
                self.psb_report.write('\n')

            if coluna == 'End':
                print("="*20 + " Result "+ '='*20)
                total = 0
                self.x_rel = np.zeros(len(self.x))
                for i in range(0, len(self.x)):
                    if self.x[i].X > 0:
                        self.x_rel[i] = self.x[i].X
                        v = int(np.ceil(self.x[i].X))
                        print(f'{v:>3} rolls of pattern {i}.')
                        total += v
                        for j in range(self.P):
                            if self.pattern[j][i] > 0:
                                print(f'\t {self.pattern[j][i]} pieces of size {self.ins.w[j]}.')
                print('='*51)
                Objetivo = self.set_cover.getObjective()
                print(f'\nObjective Function Relaxation: {Objetivo.getValue()}')
                print('Rounding Solution ...')
                print(f'Total Rolls Used: {total}')
                self.rounded = total
                self.sol_rel = Objetivo.getValue()
                break
            else:
                self.add_column(coluna)



    def column_generation_2(self) -> None:
        """
        Variant of the column generation loop with different stopping logic.

        Similar to `column_generation`, but designed for testing or 
        adaptive strategies where the process may stop early once 
        a column is successfully generated.
        """
        self.column_found = False
        while True:
        
            self.relax_lp()
            self.set_cover.setParam("OutputFlag", 0)
            self.set_cover.Params.LogToConsole = 0
            self.set_cover.optimize()
            Objetivo = self.set_cover.getObjective()
            self.lb = Objetivo.getValue()
            if self.lb > self.best_lb:
                self.best_lb = self.lb
               
            pi = []
            for i in self.cons:
                pi.append(i.Pi)
                
            coluna = self.knapsack(pi)
            if self.psb_flag:
                self.psb_report.write(f'{coluna}\n')

            if coluna == 'End':
                print("="*20 + " Result "+ '='*20)
                total = 0
                self.x_rel = np.zeros(len(self.x))
                for i in range(0, len(self.x)):
                    if self.x[i].X > 0:
                        self.x_rel[i] = self.x[i].X
                        v = int(np.ceil(self.x[i].X))
                        print(f'{v:>3} rolls of pattern {i}.')
                        total += v
                        for j in range(self.P):
                            if self.pattern[j][i] > 0:
                                print(f'\t {self.pattern[j][i]} pieces of size {self.ins.w[j]}.')
                print('='*51)
                Objetivo = self.set_cover.getObjective()
                print(f'\nObjective Function Relaxation: {Objetivo.getValue()}')
                print('Rounding Solution ...')
                print(f'Total Rolls Used: {total}')
                self.rounded = total
                break
            else:
                self.column_found = True
                self.add_column(coluna)
                break

            


    def add_column(self, coluna: list[int]) -> None:
        """
        Add a new column (pattern) to the master problem.

        Args:
            coluna (List[int]): The column vector representing a new cutting pattern.
        """
        self.column_flag = True
        I = len(coluna)
        col = Column()
        col.addTerms(coluna, self.cons)
        self.x.append(self.set_cover.addVar(vtype = GRB.CONTINUOUS, lb = 0, obj = 1 ,column = col, name = f'x_{len(self.x)}'))
        self.set_cover.update()
        
        for i in range(I):
            self.pattern[i].append(coluna[i])

        self.columns_added += 1
        self.total_column = len(self.pattern[0])
        

    def relax_lp(self) -> None:
        """
        Relax all integer decision variables in the master problem to continuous type.
        """

        for i in range(len(self.x)):
            self.x[i].vtype =  GRB.CONTINUOUS
        self.set_cover.update()
        
 
    def solve_IP(self) -> None:
        """
        Solve the integer version of the master problem (IP).

        Stores the integer solution and its objective value for reporting.
        """
        self.x_IP = np.zeros(len(self.x))
        for i in range(len(self.x)):
            self.x[i].vtype =  GRB.INTEGER

        self.set_cover.setParam("OutputFlag", 0)
        self.set_cover.Params.LogToConsole = 0

        self.set_cover.update()
        self.set_cover.optimize()
        Z_IP = self.set_cover.getObjective()
        print(f'IP Objective Function: {Z_IP.getValue()}')  
        self.file.write(f'IP Objective Function: {Z_IP.getValue()}\n')
        self.Z_IP = Z_IP.getValue()

        for i in range(len(self.x)):
            if self.x[i].X > 0:
                self.x_IP[i] = self.x[i].X



    def soft_fixing(self) -> None:
        """
        Apply the Type-1 soft fixing constraint.

        Fixes a fraction (alpha) of the variables with x > 0.5 to remain active,
        encouraging partial stability between successive IPs.
        """
        fixed = LinExpr()
        right_side = 0
        for i in range(len(self.x)):
            if self.x[i].X > 0.5:
                fixed.addTerms(1, self.x[i])
                right_side += self.x[i].X
                print(f'x_{i} = {self.x[i].X}')
          
        

        self.set_cover.addConstr(fixed >= np.ceil(self.alpha * right_side), 'Soft Fixing')
      




    def remove_soft_fixing(self) -> None:
        """
        Remove the most recently added soft fixing constraint 
        from the master problem.
        """
        self.set_cover.remove(self.set_cover.getConstrs()[-1])
        self.set_cover.update()



    def soft_fixing_type3(self) -> None:
        """
        Apply the Type-3 soft fixing constraint.

        Uses beta = 1 - alpha to fix variables with x < 0.3, 
        effectively penalizing underused patterns.
        """
        fixed = LinExpr()
        right_side = 0
        for i in range(len(self.x)):
            if self.x[i].X < 0.3:
                fixed.addTerms(1, self.x[i])
                right_side += self.x[i].X
                print(f'x_{i} = {self.x[i].X}')
          
        beta = 1 - self.alpha
        self.set_cover.addConstr(fixed >= np.ceil(beta * right_side), 'Soft Fixing')
      


    def soft_fixing_type2(self) -> None:
        """
        Apply the Type-2 soft fixing constraint.

        Adds item-level constraints based on demand proportions and 
        the soft fixing parameter alpha.
        """
        for i in range(self.ins.I):
            fixed = LinExpr()
            for j in range(len(self.x)):
                if self.x[j].X > 0.5:
                    fixed.addTerms(1,self.x[j])
            self.set_cover.addConstr(fixed >= np.ceil(self.alpha * self.ins.d[i]), f'Soft_Fixing_piece_{i}')


    def remove_soft_fixing_type2(self) -> None:
        """
        Remove the Type-2 soft fixing constraints from the master problem.

        Iterates over each item-level constraint added by `soft_fixing_type2` 
        and removes it from the Gurobi model.

        Returns:
            None
        """
        for i in range(self.ins.I):
            self.set_cover.remove(self.set_cover.getConstrs()[-1])
            self.set_cover.update()



    def soft_fixing_type4(self) -> None:
        """
        Apply the Type-4 soft fixing constraint.

        For each item, adds a constraint requiring that the weighted sum of 
        variables corresponding to patterns active in the previous IP solution 
        (x_IP[j] > 0.5) remains above an α-fraction of their total contribution.

        Returns:
            None
        """
        for i in range(self.ins.I):
            fixed = LinExpr()
            rightside = 0
            for j in range(len(self.x_IP)):
                if self.x_IP[j] > 0.5:
                    fixed.addTerms(self.pattern[i][j], self.x[j])
                    rightside += self.pattern[i][j] * self.x_IP[j]
            
            self.set_cover.addConstr(fixed >= np.ceil(self.alpha * rightside), f'Soft_fixing_{i}')

    def soft_fixing_type5(self) -> None:
        """
        Apply the Type-5 soft fixing constraint.

        For each variable x[j] active in the previous IP solution (x_IP[j] > 0.5), 
        adds a constraint ensuring that x[j] stays above an α-fraction of its IP value.

        Attributes:
            cont (int): Number of constraints added for later removal.

        Returns:
            None
        """
        self.cont = 0
        for j in range(len(self.x_IP)):
            if self.x_IP[j] > 0.5: 
                self.cont += 1
                self.set_cover.addConstr(self.x[j] >= np.ceil(self.alpha * self.x_IP[j]), f'soft_fixing_{self.cont}')

    def remove_soft_fixing_type5(self) -> None:
        """
        Remove the Type-5 soft fixing constraints added in the last iteration.

        Uses `self.cont` to remove exactly the number of constraints created 
        by `soft_fixing_type5`.

        Returns:
            None
        """
        for i in range(self.cont):
            self.set_cover.remove(self.set_cover.getConstrs()[-1])
            self.set_cover.update()
                

    def soft_fixing_type6(self) -> None:
        """
        Apply the Type-6 soft fixing constraint.

        Aggregates all patterns with LP values greater than 0.3 and constrains 
        the total contribution to remain above an α-fraction of the LP-weighted sum.

        Returns:
            None
        """
        fixed = LinExpr()
        rightside = 0
        for j in range(len(self.x)):
            if self.x[j].X > 0.3:
                for i in range(self.ins.I):
                    fixed.addTerms(self.pattern[i][j], self.x[j])
                    rightside += self.pattern[i][j] * self.x[j].X
        
        self.set_cover.addConstr(fixed >= np.ceil(self.alpha * rightside))



    def soft_fixing_type7(self) -> None:
        """
        Apply the Type-7 soft fixing constraint.

        For each item, adds a constraint on patterns that were underused 
        in the previous IP solution (x_IP[j] < 0.2), enforcing a β-fraction 
        (β = 1 - α) of their previous contribution.

        Returns:
            None
        """
        for i in range(self.ins.I):
            fixed = LinExpr()
            rightside = 0
            for j in range(len(self.x_IP)):
                if self.x_IP[j] < 0.2:
                    fixed.addTerms(self.pattern[i][j], self.x[j])
                    rightside += self.pattern[i][j] * self.x_IP[j]
            
            beta = 1 - self.alpha
            self.set_cover.addConstr(fixed >= np.ceil(beta * rightside), f'Soft_fixing_{i}')
            

    def update_alpha(self) -> float | str | None:
        """
        Adaptively update the α parameter controlling soft fixing intensity.

        Logic:
            - If the current IP solution improves the best known one, reset α to 0.9.
            - If a new column was generated, reset α to 0.9 and clear the flag.
            - Otherwise, decrease α by 0.1 until reaching 0.1, then stop.

        Returns:
            float | str | None: The updated α value, "End" if α cannot decrease further, 
                                or None if no update is made.
        """
        print(f'Z_IP = {self.Z_IP}\nBest Z_IP = {self.best_IP}\nalpha = {self.alpha}')
        if self.Z_IP < self.best_IP:
            self.best_IP = self.Z_IP
            self.alpha = 0.9
            print(" Improved integer solution! ")
            return self.alpha
        elif self.column_flag == True:
            self.alpha = 0.9
            self.column_flag = False
            print(" Found column! ")
            return self.alpha
        elif self.alpha > 0.1+10e-4:
            self.alpha = self.alpha - 0.1
            print(f" Decremented alpha to {self.alpha} ")
            return self.alpha
        else:
            return "End"
            
    def update_beta(self) -> float | str:
        """
        Adaptively update the β parameter used in alternative soft fixing strategies.

        Logic:
            - If the current IP solution improves the best one, reset β to 20.
            - Otherwise, decrease β by 1 until it reaches 2, then stop.

        Returns:
            float | str: The updated β value or "End" if β cannot decrease further.
        """
        print(f'Z_IP = {self.Z_IP}\nBest Z_IP = {self.best_IP}\nbeta = {self.beta}')
        if self.Z_IP < self.best_IP:
            self.best_IP = self.Z_IP
            self.beta = 20
            print(" Improved integer solution! ")
            return self.beta
        elif self.beta > 2:
            self.beta = self.beta - 1
            print(f" Updated beta to {self.beta} ")
            return self.beta
        else:
            return "End"


    def print_solution(self):
        print("=-="*20)
        print(f"Instance Problem Solution: {self.ins.name}")
        print(f'Relaxation Solution: Z = {sum(self.x_rel)}')
        print(f'Integer Solution: Z = {self.best_IP}')
        


    def report_solution(self, k):
        self.file.write(f'\n\nIteration {k}\n')
        self.file.write(f'Relaxation Solution: Z = {sum(self.x_rel)}\n')
        self.file.write(f'Best lower bound = {self.best_lb}\n')
        self.file.write(f'Rounding Solution: Z = {self.rounded}\n')
        self.file.write(f'Integer Solution: Z = {sum(self.x_IP)}\n')
        self.file.write(f'Added {self.columns_added} columns.\n')
        self.file.write(f'Total columns = {self.total_column}\n')
        self.columns_added = 0



            
    def bounds_return(self) -> tuple[float, float]:
        """
        Return the current lower and upper bounds of the master problem.

        Retrieves and returns:
            - The best lower bound obtained from the LP relaxation (best_lb).
            - The best integer (upper bound) solution value found so far (best_IP).

        Returns:
            Tuple[float, float]: A pair (best_lb, best_IP) representing the 
            current lower and upper bounds of the optimization process.
        """
        print('Calculating final bounds ...\n')
        self.relax_lp()    
        self.set_cover.setParam("OutputFlag", 0)
        self.set_cover.Params.LogToConsole = 0
        self.set_cover.optimize()
        lb = self.set_cover.getObjective()
        self.last_rel = lb.getValue()
        print('=' * 50)
        self.file.write('='*50 + '\n')
        print(f'Relaxation objective function: {lb.getValue()}')
        self.file.write(f'Relaxation objective function: {lb.getValue()}\n')
    
        self.solve_IP()

       
