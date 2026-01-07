"""
sudoku_solver.py

Implement the function `solve_sudoku(grid: List[List[int]]) -> List[List[int]]` using a SAT solver from PySAT.
"""

from pysat.formula import CNF # type: ignore
from pysat.solvers import Solver # pyright: ignore[reportMissingImports]
from typing import List

def solve_sudoku(grid: List[List[int]]) -> List[List[int]]:
    """Solves a Sudoku puzzle using a SAT solver. Input is a 2D grid with 0s for blanks."""

    sudocnf = CNF()

    for i in range(1,10):
        for j in range(1,10):
            L = []
            for k in range(1,10):
                L.append(i*100 + j*10 + k)
            sudocnf.append(L)
    for i in range(1,10):
        for k in range(1,10):
            L = []
            for j in range(1,10):
                L.append(i*100 + j*10 + k)
            sudocnf.append(L)
    for j in range(1,10):
        for k in range(1,10):
            L = []
            for i in range(1,10):
                L.append(i*100 + j*10 + k)
            sudocnf.append(L)
    for i in range(0,3):
        for j in range(0,3):
            for k in range(1,10):
                L = []
                for m in range(1,4):
                    for n in range(1,4):
                        L.append((i*3 + m)*100 + (j*3 + n)*10 + k)
                sudocnf.append(L)

    for i in range(1, 10):
        for j in range(1, 10):
            for k1 in range(1, 10):
                for k2 in range(k1 + 1, 10):
                    sudocnf.append([-(100*i+10*j+k1), -(100*i+10*j+k2)])

    for i in range(1,10):
        for j in range(1,10):
            L = []
            if grid[i-1][j-1] > 0:
                L.append(i*100 + j*10 + grid[i-1][j-1])
                sudocnf.append(L)


    model = []

    with Solver(name='glucose3') as solver:
        solver.append_formula(sudocnf.clauses)
        if solver.solve():
            model = solver.get_model()
        else:
            print(":(")
    
    mysol = grid

    for i in range(1,10):
        for j in range(1,10):
            for k in range(1,10):
                if (i*100 + j*10 + k) in model:
                    mysol[i-1][j-1] = k

    return mysol


   
        


    # TODO: implement encoding and solving using PySAT
    