import logicalinduction as li


def main():
    b = li.Atom("the sky is blue")
    g = li.Atom("the sky is green")
    r = li.Atom("the world is round")

    b_or_g = li.Disjunction(b, g)
    if_g_then_r = li.Implication(g, r)

    def trading_algorithm_1():
        yield {
            b: li.Constant(3.5),
            b_or_g: li.Product(li.Constant(2), li.Price(if_g_then_r, 1)),
        }
        yield {
            b: li.Constant(-1),
            b_or_g: li.Max(li.Price(b, 1), li.Price(g, 1)),
        }

    def trading_algorithm_2():
        yield {
            b: li.Constant(3.5),
            b_or_g: li.Product(li.Constant(2), li.Price(if_g_then_r, 2)),
        }
        yield {
            b: li.Constant(-1),
            if_g_then_r: li.Max(li.Price(b, 1), li.Price(g, 2)),
        }

    inductor = li.LogicalInductor()

    # update 1
    credences = inductor.update(b, trading_algorithm_1())
    print("\nafter update 1:")
    for s, credence in credences.items():
        print("  {:40s} {:f}".format(str(s), float(credence)))

    # update 2
    credences = inductor.update(b, trading_algorithm_2())
    print("\nafter update 2:")
    for s, credence in credences.items():
        print("  {:40s} {:f}".format(str(s), float(credence)))


if __name__ == "__main__":
    main()
