import inductor
import sentence
import formula

def main():
    b = sentence.Atom("the sky is blue")
    g = sentence.Atom("the sky is green")
    r = sentence.Atom("the world is round")

    b_or_g = sentence.Disjunction(b, g)
    if_g_then_r = sentence.Implication(g, r)

    def trading_algorithm_1():
        yield {
            b: formula.Constant(3.5),
            b_or_g: formula.Product(formula.Constant(2), formula.Price(if_g_then_r, 1)),
        }
        yield {
            b: formula.Constant(-1),
            b_or_g: formula.Max(formula.Price(b, 1), formula.Price(g, 1)),
        }

    def trading_algorithm_2():
        yield {
            b: formula.Constant(3.5),
            b_or_g: formula.Product(formula.Constant(2), formula.Price(if_g_then_r, 2)),
        }
        yield {
            b: formula.Constant(-1),
            if_g_then_r: formula.Max(formula.Price(b, 1), formula.Price(g, 2)),
        }

    li = inductor.LogicalInductor()

    # update 1
    credences = li.update(b, trading_algorithm_1())
    print("\nafter update 1:")
    for s, credence in credences.items():
        print("  {:40s} {:f}".format(str(s), float(credence)))

    # update 2
    credences = li.update(b, trading_algorithm_2())
    print("\nafter update 2:")
    for s, credence in credences.items():
        print("  {:40s} {:f}".format(str(s), float(credence)))


if __name__ == "__main__":
    main()
