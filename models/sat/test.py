from pysat.formula import *
from pysat.solvers import Solver
from pysat.card import CardEnc
import pysat 

vpool = IDPool(start_from=1, occupied=[])
print(pysat.__version__)
for i in range(5):
     print(vpool.id())