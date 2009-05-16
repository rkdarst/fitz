

def cartesianproduct(*args):
    """Cartesian product of iteratables given as arguments.

    This implementation thanks to MrGreen.
    """
    if len(args) == 0:
        yield ()
    else:
        for x in args[0]:
            for xs in cartesian_product_mrgreen2(*args[1:]):
                yield (x,) + xs
