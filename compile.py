import io
import collections
from typing import Any

import ppci.lang.python
import ppci.opt
from ppci.ir import Typ, SignedIntegerTyp

from sentence import Atom, Disjunction, Conjunction, Implication, Iff, Negation

src = """
def incr(x: int) -> int:
    return x + 1
"""

# def fib(n: int) -> int:
#     if n <= 1:
#         return n
#     else:
#         return fib(n-1) + fib(n-2)

# def a() -> int:
#     return 1

MAX_INT = 2  # ha ha ha


class SentenceBackend(object):
    def __init__(self):
        self.possible_values = {}  # map from var to list of values
        self.atoms = {}            # map from (var, value) to Atom
        self.sentences = []

    def create_var(self, var:str, possible_values:list[Any]) -> None:
        self.possible_values[var] = possible_values
        for value in possible_values:
            a = Atom("{}_{}".format(var, value))
            self.atoms[(var, value)] = a

    def create_int(self, var:str) -> None:
        self.create_var(var, range(-MAX_INT, MAX_INT+1))

    def assign_constant(self, var:str, value:Any) -> None:
        for v in self.possible_values[var]:
            a = self.atoms[var, v]
            if v == value:
                self.sentences.append(a)

    def assign(self, out:str, inp:str) -> None:
        for vout in self.possible_values[out]:
            for vin in self.possible_values[inp]:
                aout = self.atoms[(out, vout)]
                ain = self.atoms[(inp, vin)]
                if vout == vin:
                    self.sentences.append(Iff(aout, ain))

    def add(self, result:str, lhs:str, rhs:str) -> None:
        for vres in self.possible_values[result]:
            for vlhs in self.possible_values[lhs]:
                for vrhs in self.possible_values[rhs]:
                    ares = self.atoms[(result, vres)]
                    alhs = self.atoms[(lhs, vlhs)]
                    arhs = self.atoms[(rhs, vrhs)]
                    if vres == vlhs + vrhs:
                        self.sentences.append(Implication(Conjunction(alhs, arhs), ares))


def main():
    m = ppci.lang.python.python_to_ir(io.StringIO(src))

    passes = [
        ppci.opt.Mem2RegPromotor(),
        ppci.opt.LoadAfterStorePass(),
        ppci.opt.DeleteUnusedInstructionsPass(),
        ppci.opt.RemoveAddZeroPass(),
        ppci.opt.CommonSubexpressionEliminationPass(),
    ]

    for p in passes:
        p.run(m)

    f = m.functions[0]
    f.dump()

    be = SentenceBackend()

    if f.return_ty.is_integer:
        be.create_int(f.name)
    else:
        raise Exception("unsupported function type: {}".format(f.return_ty))

    for arg in f.arguments:
        if arg.ty.is_integer:
            be.create_int(arg.name)
        else:
            raise Exception("unsupported argument type: {}".format(i.ty))

    for i in f.blocks[0].instructions:
        if isinstance(i, ppci.ir.Return):
            be.assign(f.name, i.result.name)
            continue

        if i.ty.is_integer:
            be.create_int(i.name)
        else:
            raise Exception("unsupported type: {}".format(i.ty))

        if isinstance(i, ppci.ir.Const):
            be.assign_constant(i.name, i.value)
        elif isinstance(i, ppci.ir.Binop):
            if i.operation == "+":
                be.add(i.name, i.uses[0].name, i.uses[1].name)
            else:
                raise Exception("unsupported binop: {}".format(i.operation))
        else:
            raise Exception("unsupported instruction")

    for s in be.sentences:
        print(s)


if __name__ == "__main__":
    main()
