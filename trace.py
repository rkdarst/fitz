import sys

import inspect
import os.path


# Set this variable to True if you want to print out every line, as it
# executes
traceLine = False
useColor = True

def color(s):
    if useColor:
        return '\x1B[1;34m'+s+'\x1B[0m'
    return s
def colorLine(s):
    if useColor:
        return '\x1B[1m'+s+'\x1B[0m'
    return s

def traceit(frame, event, arg):
    # inspect becomes None during final clean-up upon system exit.
    if inspect is None: return None

    f = inspect.stack()[1]
    #from fitz import interactnow
    #if f[4] is None: return traceit
    #filename = f[1]

    modname = modname = frame.f_globals.get('__name__', '__name__=unknown')
    funcname = frame.f_code.co_name  # f[3]
    filename = frame.f_globals.get('__file__', '__file__=unknown')
    lineno = frame.f_lineno #f[2]
    if f[4] is None:
        line = 'line=None'
    else:
        line = "\\n".join(f[4]).strip()
    if event == 'call':
        # Don't print stdlib func calls
        if filename.startswith('/usr/lib'):
            return None
        print color("(call)")+" %s:%s:%s"%(modname, lineno, funcname), \
              colorLine(line)

        #from fitz import interactnow
    if traceLine and event == "line":
        if '__name__' in frame.f_globals:
            modname = frame.f_globals['__name__']
            funcname = frame.f_code.co_name  # f[3]
            lineno = frame.f_lineno
            print color("    (line)")+" %s:%s"%(modname, lineno), \
                  colorLine(line)
    if event == "return":
        modname = modname = frame.f_globals.get('__name__', '__name__=unknown')
        funcname = frame.f_code.co_name  # f[3]
        lineno = frame.f_lineno
        print color("(return)")+" %s:%s:%s (val=%s)"%\
                          (modname, lineno, frame.f_code.co_name, arg), \
              colorLine(line)
    return traceit

def enable():
    sys.settrace(traceit)

def disable():
    sys.settrace(None)

def test():
    global traceLine
    traceLine = True
    def testfunc():
        print "in test function"
        testfunc2()
    def testfunc2():
        print "in test function 2"
        return '<ret value>'
    enable()
    testfunc()
    disable()

if __name__ == "__main__":
    #print sys.argv
    while True:
        # Disable color
        if sys.argv[1] == '-c':
            useColor = False
            del sys.argv[1]
        elif sys.argv[1] == '-a':
            traceLine = True
            del sys.argv[1]
        break
    if len(sys.argv) == 1:
        import code
        enable()
        code.interact()
        disable()
    elif sys.argv[1] == '-m':
        import runpy
        mod = sys.argv[2]
        del sys.argv[0:2]
        enable()
        runpy.run_module(mod, run_name='__main__', alter_sys=True)
        disable()
    else:
        del sys.argv[0]
        enable()
        execfile(sys.argv[0])
        disable()


