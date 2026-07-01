#un super code arrive soon

#on considère qu'on a D et W la 
from ortools.linear_solver import pywraplp
def opti():
    costs=W
    num_workers=len(D)
    num_tasks=len(D[0])
    solver= pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return
    x={}
    for i in range(num_workers):
        for j in range(num_tasks):
            x[i,j]=solver.IntVar(0,1,"")
    #chaque machiniste a au plus 1 tâche
    for i in range (num_workers):
        solver.Add(solver.Sum([x[i,j] for j in range(num_tasks)]) <=1)
    #chaque tache est assignée a exactement un machiniste
    for j in range(num_tasks):
        solver.Add(solver.Sum([x[i,j] for i in range(num_workers)]) == 1)
    #chaque machiniste ne peut que faire les tâches pour lesquelles il est accrédité
    for i in range(num_workers):
        for j in range(num_tasks):
            if D[i][j]==0:
                solver.Add(x[i,j]==0)
    objective_terms=[]
    for i in range(num_workers):
        for j in range(num_tasks):
            objective_terms.append(costs[i][j]*x[i,j])
    solver.Maximize(solver.Sum(objective_terms))

    status=solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        for i in range(num_workers):
            for j in range(num_tasks):
                # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
                if x[i, j].solution_value() > 0.5:
                    print(f"Worker {i} assigned to task {j}." + f" Cost: {costs[i][j]}")
    else:
        print("No solution found.")