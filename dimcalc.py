# Richard Darst, April 2008

product = lambda l: reduce(lambda x,y: x*y, l, 1)

def coords(dims, index):
    """Given array dimensions and a (linear) position index, return the coordinates.
    """
    #coords = [ ]
    #for i in range(len(dims)):
    #    x = (pos // product(dims[i+1:])) % dims[i]
    #    coords.append(x)
    #return tuple(coords)

    # this does the same thing, but more concisely:
    return tuple( (index // product(dims[i+1:])) % dims[i] for i in range(len(dims)))

def index(dims, coords):
    """Given array dimensions and coordinates, return the (linear) index.
    """
    #index = 0
    #for i in range(len(dims)):
    #    index *= dims[i]
    #    index += coords[i]
    #return index

    # again, more concisely
    return reduce(lambda a, x:a*x[0]+x[1],
                  zip(dims, coords),
                  0)


if __name__ == "__main__":
    import numpy
    z = numpy.arange(36)
    z.shape = 2, 3, 2, 3
    print z

    for i in (0, 6, 17, 22, 27, 32, 35, 36):
        print i, index(z.shape, coords(z.shape, i)), coords(z.shape, i)

    x = numpy.asarray((0, 6, 17, 22, 27, 32, 35, 36))
    print x
    coords = coords(z.shape, x)
    coords = numpy.asarray(coords)

