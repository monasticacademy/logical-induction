from dis import Instruction
import io
import collections
import operator
from typing import Any, Callable, Optional

import ppci.lang.python
import ppci.opt
from ppci import ir

from sentence import Atom, Disjunction, Conjunction, Implication, Iff, Negation, Sentence

src = """
def make_pi_recursive(digits_left: int, q: int, r: int, t: int, k: int, m: int, x: int) -> int:
    # q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    if 4 * q + r - t < m * t:
        if digits_left == 0:
          return m
        q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
        return make_pi_recursive(digits_left - 1, q, r, t, k, m, x)
    else:
        q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2
        return make_pi_recursive(digits_left, q, r, t, k, m, x)
"""

# def fib(n: int) -> int:
#     if n <= 1:
#         return n
#     else:
#         return fib(n-1) + fib(n-2)

# def a() -> int:
#     return 1

MAX_INT = 2  # ha ha ha


def binary_operator(s: str) -> Callable:
    """Get a function from a string such as "+" or "*". """
    if s == "+":
        return operator.add
    elif s == "-":
        return operator.sub
    elif s == "*":
        return operator.mul
    elif s == "/":
        return operator.truediv
    elif s == "//":
        return operator.floordiv
    else:
        raise Exception("unknown binary operator: {}".format(s))


def comparison_operator(s: str) -> Callable[[int, int], bool]:
    if s == "==":
        return operator.eq
    elif s == "<":
        return operator.lt
    elif s == ">":
        return operator.gt
    elif s == ">=":
        return operator.ge
    elif s == "<=":
        return operator.le
    elif s == "!=":
        return operator.ne
    else:
        raise Exception("unknown comparison operator: {}".format(s))


class SentenceBackend(object):
    def __init__(self):
        self.possible_values = {}  # map from var to list of values
        self.atoms = {}            # map from (var, value) to Atom
        self.branch_atoms = {}
        self.sentences = []

    def create_branch(self, branch: str) -> None:
        self.branch_atoms[branch] = Atom(branch)

    def create_var(self, var: str, possible_values: list[Any]) -> None:
        self.possible_values[var] = possible_values
        for value in possible_values:
            a = Atom("{}_{}".format(var, value))
            self.atoms[(var, value)] = a

    def create_int(self, var:str) -> None:
        self.create_var(var, range(-MAX_INT, MAX_INT+1))

    def assign_constant(self, var: str, value: Any) -> None:
        for v in self.possible_values[var]:
            a = self.atoms[var, v]
            if v == value:
                self.sentences.append(a)

    def assign(self, out: str, inp: str, branch: Optional[str] = None) -> None:
        for vout in self.possible_values[out]:
            aout = self.atoms[(out, vout)]
            for vin in self.possible_values[inp]:
                ain = self.atoms[(inp, vin)]
                if vout == vin:
                    sentence = Iff(aout, ain)
                    if branch is None:
                        self.sentences.append(sentence)
                    else:
                        self.sentences.append(Implication(branch, sentence))
    

    def conditional_jump(self, lhs: str, rhs: str, condition: Callable[[int, int], bool], yesbranch: str, nobranch: str) -> None:
        """
        Creates sentences to represent the fact that if the condition holds then we go to
        "yesbranch", otherwise we go to "nobranch"
        """
        ayes = self.branch_atoms[yesbranch]
        ano = self.branch_atoms[nobranch]
        for vlhs in self.possible_values[lhs]:
            alhs = self.atoms[(lhs, vlhs)]
            for vrhs in self.possible_values[rhs]:
                arhs = self.atoms[(rhs, vrhs)]
                if condition(vlhs, vrhs):
                    self.sentences.append(Implication(Conjunction(alhs, arhs), ayes))
                else:
                    self.sentences.append(Implication(Conjunction(alhs, arhs), ano))

    def binop(self, result: str, lhs: str, rhs: str, op: Callable) -> None:
        for vres in self.possible_values[result]:
            ares = self.atoms[(result, vres)]
            for vlhs in self.possible_values[lhs]:
                alhs = self.atoms[(lhs, vlhs)]
                for vrhs in self.possible_values[rhs]:
                    arhs = self.atoms[(rhs, vrhs)]
                    try:
                        if vres == op(vlhs, vrhs):
                            self.sentences.append(Implication(Conjunction(alhs, arhs), ares))
                    except ZeroDivisionError as e:
                        pass


def mod_name(mod: ir.Module) -> str:
    if mod == None:
        return "unknown_module"
    return mod.name

def func_name(func: ir.Function) -> str:
    if func == None:
        return "unknown_function"
    return mod_name(func.module) + "__" + func.name

def output_name(func: ir.Function):
    return func_name(func) + "__return"

def block_name(block: ir.Block) -> str:
    if block == None:
        return "unknown_block"
    return func_name(block.function) + "__" + block.name

def branch_name(block: ir.Block) -> str:
    return block_name(block) + "__branch"

def instr_name(instr: ir.Instruction) -> str:
    return block_name(instr.block) + "__" + instr.name


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

    func = m.functions[0]
    func.dump()

    be = SentenceBackend()

    def value_name(v: ir.LocalValue) -> str:
        if isinstance(v, ir.Parameter):
            return func_name(func) + "__arg__" + v.name
        elif isinstance(v, ir.LocalValue):
            return instr_name(v)
        else:
            raise Exception("unable to compute value name for {}".format(type(v)))


    if func.return_ty.is_integer:
        be.create_int(output_name(func))
    else:
        raise Exception("unsupported function type: {}".format(func.return_ty))

    for block in func.blocks:
        be.create_branch(branch_name(block))

    for arg in func.arguments:
        if arg.ty.is_integer:
            be.create_int(value_name(arg))
        else:
            raise Exception("unsupported argument type: {}".format(instr.ty))

    for block in func.blocks:
        for instr in block.instructions:
            # name of the output of this instruction
            if isinstance(instr, ir.Return):
                be.assign(output_name(func), value_name(instr.result))

            if isinstance(instr, ir.CJump):
                be.conditional_jump(
                    lhs=value_name(instr.a),
                    rhs=value_name(instr.b),
                    condition=comparison_operator(instr.cond),
                    yesbranch=branch_name(instr.lab_yes),
                    nobranch=branch_name(instr.lab_no))

            elif isinstance(instr, ir.LocalValue):
                # this is an instruction that has a type
                if instr.ty.is_integer:
                    be.create_int(instr_name(instr))
                else:
                    raise Exception("unsupported type: {}".format(instr.ty))

                if isinstance(instr, ir.Const):
                    be.assign_constant(value_name(instr), instr.value)

                elif isinstance(instr, ir.Binop):
                    print("performing binop on {} and {} -> {}")
                    be.binop(
                        instr_name(instr),
                        value_name(instr.a),
                        value_name(instr.b),
                        binary_operator(instr.operation))

                elif isinstance(instr, ir.Phi):
                    # a phi is a map from blocks to the values used if that block was executed
                    for block, value in instr.inputs.items():
                        be.assign(
                            instr_name(instr),
                            value_name(value),
                            branch=branch_name(block)
                        )

                else:
                    raise Exception("unsupported instruction: {}".format(type(instr)))

    # TODO: simple if statement

    for s in be.sentences:
        print(s)


if __name__ == "__main__":
    main()
