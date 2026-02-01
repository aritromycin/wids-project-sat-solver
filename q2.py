"""
Sokoban Solver using SAT (Boilerplate)
--------------------------------------
Instructions:
- Implement encoding of Sokoban into CNF.
- Use PySAT to solve the CNF and extract moves.
- Ensure constraints for player movement, box pushes, and goal conditions.

Grid Encoding:
- 'P' = Player
- 'B' = Box
- 'G' = Goal
- '#' = Wall
- '.' = Empty space
"""

from pysat.formula import CNF
from pysat.solvers import Solver

# Directions for movement
DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


class SokobanEncoder:
    def __init__(self, grid, T):
        """
        Initialize encoder with grid and time limit.

        Args:
            grid (list[list[str]]): Sokoban grid.
            T (int): Max number of steps allowed.
        """
        self.grid = grid
        self.T = T
        self.N = len(grid)
        self.M = len(grid[0])

        self.goals = []
        self.boxes = []
        self.walls = []
        self.player_start = None
        self.var_count = 0

        # TODO: Parse grid to fill self.goals, self.boxes, self.player_start
        self._parse_grid()

        self.num_boxes = len(self.boxes)
        self.cnf = CNF()

    def _parse_grid(self):
        """Parse grid to find player, boxes, and goals."""
        for i in range(0,self.N):
            for j in range(0,self.M):
                if self.grid[i][j] == 'G':
                    self.goals.append((j,i))
                elif self.grid[i][j] == 'B':
                    self.boxes.append((j,i))
                elif self.grid[i][j] == 'P':
                    self.player_start = (j,i)
                if self.grid[i][j] == '#':
                    self.walls.append((j,i))
        

    # ---------------- Variable Encoding ----------------
      # in __init__

    
    def var_player(self, x, y, t):
        """
        Variable ID for player at (x, y) at time t.
        """
        return (t*self.N*self.M + y*self.M + (x+1))
        

    def var_box(self, b, x, y, t):
        """
        Variable ID for box b at (x, y) at time t.
        """
        return (self.N*self.M*(self.T+1)*b + t*self.N*self.M + y*self.M + (x+1))
    
    def var_move(self, x, y, s, t):
        """
        Variable ID for player moving in direction s from (x,y) at time t
        """
        base = self.N*self.M*(self.T+1)*(self.num_boxes+1)
        dir_offset = {'U':1, 'D':2, 'L':3, 'R':4}[s]
        return (base + t*4*self.N*self.M + y*self.M + x + dir_offset)

    
    def new_var(self):
        self.var_count += 1
        return(self.N*self.M*(self.T+1)*(self.num_boxes+1)+self.T*4+1+self.var_count)
        


    # ---------------- Encoding Logic ----------------
    def encode(self):
        """
        Build CNF constraints for Sokoban:
        - Initial state
        - Valid moves (player + box pushes)
        - Non-overlapping boxes
        - Goal condition at final timestep
        """

        #player at start
        self.cnf.append([self.var_player(self.player_start[0], self.player_start[1], 0)])

        #boxes at start
        for b in range(1,self.num_boxes+1):
            self.cnf.append([self.var_box(b,self.boxes[b-1][0], self.boxes[b-1][1], 0)])



        #box constraint
        for t in range(self.T+1):
            for y in range(0,self.N):
                for x in range(0,self.M):
                    for b in range(1,self.num_boxes+1):
                        for c in range(1,self.num_boxes+1):
                            if b == c:
                                continue
                            else:
                                self.cnf.append([-self.var_box(b,x,y,t),-self.var_box(c,x,y,t)])
                        self.cnf.append([-self.var_box(b,x,y,t),-self.var_player(x,y,t)])

        #goal condition
        for g in self.goals:
            L = []
            for b in range(1,self.num_boxes+1):
                L.append(self.var_box(b,g[0],g[1],self.T))
            self.cnf.append(L)

        #all moves
        for x in range(self.M):
            for y in range(self.N):
                for t in range(self.T):
                    if (x,y) in self.walls:
                        continue
                    if y > 0:
                        self.cnf.append([-self.var_player(x,y,t), -self.var_move(x,y,'U',t), self.var_player(x,y-1,t+1)])
                    if y < self.N-1:
                        self.cnf.append([-self.var_player(x,y,t), -self.var_move(x,y,'D',t), self.var_player(x,y+1,t+1)])
                    if x > 0:
                        self.cnf.append([-self.var_player(x,y,t), -self.var_move(x,y,'L',t), self.var_player(x-1,y,t+1)])
                    if x < self.M-1:
                        self.cnf.append([-self.var_player(x,y,t), -self.var_move(x,y,'R',t), self.var_player(x+1,y,t+1)])


        #valid positions to be in
        for t in range(0,self.T+1):
            for i in self.walls:
                self.cnf.append([-self.var_player(i[0],i[1],t)])
                for b in range(1,self.num_boxes+1):
                    self.cnf.append([-self.var_box(b,i[0],i[1],t)])
            

        #at least one position at a time
        for t in range(0,self.T+1):
            L = []
            for x in range(0,self.M):
                for y in range(0,self.N):
                    if (x,y) in self.walls:
                        continue
                    L.append(self.var_player(x,y,t))
            self.cnf.append(L)

        #same for boxes
        for b in range(1,self.num_boxes+1):
            for t in range(0,self.T+1):
                L = []
                for x in range(self.M):
                    for y in range(self.N):
                        if (x,y) in self.walls:
                            continue
                        L.append(self.var_box(b,x,y,t))
                self.cnf.append(L)

        #only one position at a time
        for t in range(0,self.T+1):
            for x in range(self.M):
                for y in range(self.N):
                    for otherx in range(self.M):
                        for othery in range(self.N):
                            if x == otherx and y == othery:
                                continue
                            else:
                                self.cnf.append([-self.var_player(x,y,t),-self.var_player(otherx,othery,t)])

        #same for boxes
        for b in range(1,self.num_boxes+1):
            for t in range(self.T+1):
                for x in range(self.M):
                    for y in range(self.N):
                        for otherx in range(self.M):
                            for othery in range(self.N):
                                if x == otherx and y == othery:
                                    continue
                                else:
                                    self.cnf.append([-self.var_box(b,x,y,t),-self.var_box(b,otherx,othery,t)])
                
        #player inertia
        for x in range(self.M):
            for y in range(self.N):
                for t in range(0, self.T):
                    self.cnf.append([
                        -self.var_player(x, y, t),   
                        self.var_move(x,y,'U', t),       
                        self.var_move(x,y,'D', t),       
                        self.var_move(x,y,'L', t),       
                        self.var_move(x,y,'R', t),       
                        self.var_player(x, y, t+1)   
                    ])


                    
                        
                        


        #at most one move at a time
        for t in range(0,self.T):
            self.cnf.append([-self.var_move(x,y,'U',t),-self.var_move(x,y,'D',t)])
            self.cnf.append([-self.var_move(x,y,'U',t),-self.var_move(x,y,'L',t)])
            self.cnf.append([-self.var_move(x,y,'U',t),-self.var_move(x,y,'R',t)])
            self.cnf.append([-self.var_move(x,y,'D',t),-self.var_move(x,y,'L',t)])
            self.cnf.append([-self.var_move(x,y,'D',t),-self.var_move(x,y,'R',t)])
            self.cnf.append([-self.var_move(x,y,'L',t),-self.var_move(x,y,'R',t)])



        #box pushing
        for x in range(self.M):
            for y in range(self.N):
                for t in range(self.T):
                    for b in range(1,self.num_boxes+1):
                        if y >= 2 and self.grid[y-2][x]!='#':
                            #destination empty
                            for c in range(1,self.num_boxes+1):
                                if c == b:
                                    continue
                                self.cnf.append([-self.var_player(x,y,t),-self.var_move(x,y,'U',t),-self.var_box(b,x,y-1,t),-self.var_box(c,x,y-2,t)])
                            #push effect
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x,y-1,t),-self.var_move(x,y,'U',t),self.var_player(x,y-1,t+1)]))
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x,y-1,t),-self.var_move(x,y,'U',t),self.var_box(b,x,y-2,t+1)]))
                        if y <= self.N-3 and self.grid[y+2][x]!='#':
                            #destination empty
                            for c in range(1,self.num_boxes+1):
                                if c == b:
                                    continue
                                self.cnf.append([-self.var_player(x,y,t),-self.var_move(x,y,'D',t),-self.var_box(b,x,y+1,t),-self.var_box(c,x,y+2,t)])
                            #push effect
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x,y+1,t),-self.var_move(x,y,'D',t),self.var_player(x,y+1,t+1)]))
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x,y+1,t),-self.var_move(x,y,'D',t),self.var_box(b,x,y+2,t+1)]))
                        if x >= 2 and self.grid[y][x-2]!='#':
                            #destination empty
                            for c in range(1,self.num_boxes+1):
                                if c == b:
                                    continue
                                self.cnf.append([-self.var_player(x,y,t),-self.var_move(x,y,'L',t),-self.var_box(b,x-1,y,t),-self.var_box(c,x-2,y,t)])
                            #push effect
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x-1,y,t),-self.var_move(x,y,'L',t),self.var_player(x-1,y,t+1)]))
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x-1,y,t),-self.var_move(x,y,'L',t),self.var_box(b,x-2,y,t+1)]))
                        if x <= self.M-3 and self.grid[y][x+2]!='#':
                            #destination empty
                            for c in range(1,self.num_boxes+1):
                                if c == b:
                                    continue
                                self.cnf.append([-self.var_player(x,y,t),-self.var_move(x,y,'R',t),-self.var_box(b,x+1,y,t),-self.var_box(c,x+2,y,t)])
                            #push effect
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x+1,y,t),-self.var_move(x,y,'R',t),self.var_player(x+1,y,t+1)]))
                            self.cnf.append(([-self.var_player(x,y,t),-self.var_box(b,x+1,y,t),-self.var_move(x,y,'R',t),self.var_box(b,x+2,y,t+1)]))






                            
        

        #box inertia
        for b in range(1, self.num_boxes + 1):
            for t in range(self.T):
                for x in range(self.M):
                    for y in range(self.N):

                        active_vars = []

                        if y < self.N-1:  # can be pushed from below (U)
                            pu = self.new_var()
                            active_vars.append(pu)
                            self.cnf.append([-pu, self.var_player(x, y+1, t)])
                            self.cnf.append([-pu, self.var_move(x,y,'U', t)])
                            self.cnf.append([pu, -self.var_player(x, y+1, t), -self.var_move(x,y,'U', t)])

                        if y > 0:  # can be pushed from above (D)
                            pd = self.new_var()
                            active_vars.append(pd)
                            self.cnf.append([-pd, self.var_player(x, y-1, t)])
                            self.cnf.append([-pd, self.var_move(x,y,'D', t)])
                            self.cnf.append([pd, -self.var_player(x, y-1, t), -self.var_move(x,y,'D', t)])

                        if x < self.M-1:  # can be pushed from right (L)
                            pl = self.new_var()
                            active_vars.append(pl)
                            self.cnf.append([-pl, self.var_player(x+1, y, t)])
                            self.cnf.append([-pl, self.var_move(x,y,'L', t)])
                            self.cnf.append([pl, -self.var_player(x+1, y, t), -self.var_move(x,y,'L', t)])

                        if x > 0:  # can be pushed from left (R)
                            pr = self.new_var()
                            active_vars.append(pr)
                            self.cnf.append([-pr, self.var_player(x-1, y, t)])
                            self.cnf.append([-pr, self.var_move(x,y,'R', t)])
                            self.cnf.append([pr, -self.var_player(x-1, y, t), -self.var_move(x,y,'R', t)])

                        self.cnf.append([-self.var_box(b, x, y, t), *active_vars, self.var_box(b, x, y, t+1)])

        
        return self.cnf



                    
        

        




        


def decode(model, encoder):
    """
    Decode SAT model into list of moves ('U', 'D', 'L', 'R').

    Args:
        model (list[int]): Satisfying assignment from SAT solver.
        encoder (SokobanEncoder): Encoder object with grid info.

    Returns:
        list[str]: Sequence of moves.
    """
    N, M, T = encoder.N, encoder.M, encoder.T

    movelist = []
    for t in range(0,T):
        # find move at timestep t that is True and where player was
        for x in range(encoder.M):
            for y in range(encoder.N):
                for s in 'UDLR':
                    if encoder.var_move(x,y,s,t) in model:
                        movelist.append(s)
                        break


    # TODO: Map player positions at each timestep to movement directions
    return movelist


def solve_sokoban(grid, T):
    """
    DO NOT MODIFY THIS FUNCTION.

    Solve Sokoban using SAT encoding.

    Args:
        grid (list[list[str]]): Sokoban grid.
        T (int): Max number of steps allowed.

    Returns:
        list[str] or "unsat": Move sequence or unsatisfiable.
    """
    encoder = SokobanEncoder(grid, T)
    cnf = encoder.encode()

    with Solver(name='g3') as solver:
        solver.append_formula(cnf)
        if not solver.solve():
            return -1

        model = solver.get_model()
        if not model:
            return -1

        return decode(model, encoder)