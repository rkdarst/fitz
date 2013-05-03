# Richard Darst, November 2011
# Based on something from at least before December 2010

def main(argv=None):
    """Simulate 'python -m <modname>'

    This simulates 'python -m <modname> <args> ...', handling a '-m'
    additionally.

    argv: if given, use this as argv instead of sys.argv

    Some notes:
    'python -m somemodule' =>
        argv[0]=the module calling this
    'python -m somemodule' arg =>
        argv[0]=module calling this
        argv[1]=arg
    """
    if argv is None:
        import sys
        argv = sys.argv

    del argv[0] # The script calling this.

    if len(argv) > 0 and argv[0] == '-m':
        import runpy
        modname = argv[1]
        del argv[0:1]
        runpy.run_module(modname, run_name='__main__', alter_sys=True)
    elif len(argv) > 0:
        # Extend PYTHONPATH.  Python up until version XX (FIXME: when
        # does this break compatibility) always inserts the dirname of
        # the module being run first on sys.path.  We need to emulate
        # that in our new thing.
        import sys
        import os
        del sys.path[0] # The old path to the script (usually '') if
                        # run with -m ??
        sys.path.insert(0, os.path.dirname(os.path.abspath(argv[0])))
        new_globals = {'__name__':'__main__',
                       '__file__':argv[0],
                       }
        execfile(argv[0], new_globals)
    else:
        from code import interact
        interact(local={'__name__':'__main__'})

if __name__ == "__main__":
    # Silly function.  This ignores each "-m runpy2"
    main()
