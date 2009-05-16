# Richard Darst, October 2008

import glob
import os
import pprint as pprint_
import shelve
import time

def get(name, *keys):
    s = shelve.open(name, 'r')
    d = s
    for key in keys:
        d = d[key]
    return d
def getkeys(name, *keys):
    s = shelve.open(name, 'r')
    d = s
    for key in keys:
        d = d[key]
    return d.keys()
def pprint(name, *keys):
    d = get(name, *keys)
    pprint_.pprint(dict(d), indent=1)
def pprint2(name, *keys):
    print "{"
    d = get(name, *keys)
    _recr_print(d, indent=4)
    print "}"
def _recr_print(d, indent):
    #print " "*indent+"{"
    for key in sorted(d.keys()):
        value = d[key]
        if isinstance(value, (dict, shelve.Shelf)):
            print " "*indent+repr(key)+': {'
            _recr_print(value, indent=indent+4)
            print " "*indent+'},'
        else:
            print " "*indent+repr(key)+':',value,','
    #pprint_.pprint(dict(d), indent=1)
    #print " "*indent+"}"


def create(name):
    shelve.open(name, 'c', protocol=-1)
def set(name, value, *keys):
    s = shelve.open(name, 'w', writeback=True, protocol=-1)
    d = s
    newkey = keys[-1]
    for key in keys[:-1]:
        if not d.has_key(key):
            d[key] = { }
        d = d[key]
    d[newkey] = value
    s.close() ; del s
def delete(name, *keys):
    s = shelve.open(name, 'w', writeback=True, protocol=-1)
    d = s
    newkey = keys[-1]
    for key in keys[:-1]:
        d = d[key]
    print 'deleting', keys
    del d[newkey]
    s.close() ; del s
def update(oldname, newname):
    print oldname, '-->', newname
    old = shelve.open(oldname, 'r')
    new = shelve.open(newname, 'w', writeback=True, protocol=-1)
    _copy_recursive(old, new)
    old.close() ; new.close(); del old, new
def _copy_recursive(dold, dnew):
    for key in dold.keys():
        if dnew.has_key(key) and isinstance(dnew[key], (dict, shelve.Shelf)):
            _copy_recursive(dold[key], dnew[key])
        else:
            dnew[key] = dold[key]



def append(name, value, *keys):
    newname = name+'-'+time.strftime("%Y%m%d%H%M%S")+os.uname()[1]
    create(newname)
    set(newname, value, *keys)
def appendMulti(name, listToAppend):
    """listToAppend = (value0, (*keys0),
                       value1, (*keys1),
                       ..., )
    """
    newname = name+'-'+time.strftime("%Y%m%d%H%M%S")+os.uname()[1]
    create(newname)
    for value, keys in listToAppend:
        set(newname, value, *keys)
def merge(originalname):
    name = originalname + '-*'
    names = sorted(glob.glob(name))
    for newname in names:
        update(newname, originalname)
        os.unlink(newname)
def removeextra(originalname):
    name = originalname + '-*'
    names = sorted(glob.glob(name))
    for newname in names:
        os.unlink(newname)


class DB(object):
    def __init__(self, name):
        self.name = name
    def get(self, *keys):
        """Get the value of a certain key"""
        get(name, *keys)
    def getkeys(self, *keys):
        """Get all subkeys of a certain key"""
        getkeys(name, *keys)
    def pprint(self, *keys):
        pprint(self.name, *keys)
    def pprint2(self, *keys):
        pprint2(self.name, *keys)
    def create(self, ):
        """Create a new database.  Must be explicitely created"""
        create(self.name)
    def set(self, value, *keys):
        """Set a certain value at """
        set(self.name, value, *keys)
    def delete(self, *keys):
        """Delete a certain key (and all subkeys)"""
        delete(self.name, *keys)
    def update(self, sourcename):
        update(sourcename, self.name)
    def append(self, value, *keys):
        append(self.name, value, *keys)
    def appendMulti(self, listToAppend):
        appendMulti(self.name, listToAppend)
    def merge(self):
        merge(self.name)
    def removeextra(self,):
        removeextra(self.name)




    

if __name__ == "__main__":
    import sys
    if sys.argv[1] == 'get':
        name = sys.argv[2]
        keys = sys.argv[3:]
        print get(name, *keys)
    elif sys.argv[1] in ('getkeys', 'keys'):
        name = sys.argv[2]
        keys = sys.argv[3:]
        print getkeys(name, *keys)
    elif sys.argv[1] in ('pprint', 'print'):
        name = sys.argv[2]
        keys = sys.argv[3:]
        pprint2(name, *keys)

    elif sys.argv[1] == 'create':
        name = sys.argv[2]
        create(name)
    elif sys.argv[1] == 'set':
        name = sys.argv[2]
        value = eval(sys.argv[3])
        keys = sys.argv[4:]
        set(name, value, *keys)
    elif sys.argv[1] == 'delete':
        name = sys.argv[2]
        keys = sys.argv[3:]
        delete(name, *keys)
    elif sys.argv[1] == 'update':
        oldname = sys.argv[2]
        newname = sys.argv[3]
        update(oldname, newname)

    elif sys.argv[1] == 'append':
        name = sys.argv[2]
        value = eval(sys.argv[3])
        keys = sys.argv[4:]
        append(name, value, *keys)
    elif sys.argv[1] == 'merge':
        name = sys.argv[2]
        merge(name)
    else:
        print "command not found: %s"%sys.argv[1]


