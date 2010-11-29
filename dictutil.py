# Richard Darst, July 2010

import copy

def add(new, *rest):
    #new = new.copy()
    return iadd({}, new, *rest)
def iadd(new, *rest):
    for d in rest:
        #print d
        for key, value in d.iteritems():
            #print key, new
            if isinstance(value, dict):
                # dict:
                if key not in new:
                    #new[key] = value.copy()
                    #new[key] = copy.deepcopy(value)#.copy()
                    new[key] = { }
                    iadd(new[key], value)
                else:
                    iadd(new[key], value)
            else:
                # non-dict
                if key in new:
                    raise Exception("Key '%s' already exists"%key)
                new[key] = d[key]
    return new

if __name__ == "__main__":
    d1 = { 'a':1, 'c':{'e':4, 'g':{'h':6}} }
    d2 = { 'b':2, 'c':{'d':3, 'g':{'i':7}} }
    d3 = { 'c':{'f':5} }

    print d1, d2, d3
    add(d1, d2, d3)
    #print d1
    print d1, d2, d3
