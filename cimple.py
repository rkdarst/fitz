'''cimple - declare C functions that are compiled and loaded them at runtime
'''
import distutils.ccompiler
import ctypes
import os, os.path
import tempfile
import random

# TODO:
# - structs should be detected and defined exactly ONCE, probably just after the header and before the function prototype
# - implement passing function pointers
#
# WISHLIST:
# - sometime someone should try to get the #line pragma working:
#   http://gcc.gnu.org/onlinedocs/cpp/Line-Control.html

class Cimple:
    'cimple base class'

    _cimple_header = ''
    _cimple_footer = ''

    def __init__(self, libname=None, tmpdir=None):
        self.funcs = []
        # find all c functions that need to be compiled
        for attrname in self.__class__.__dict__.keys():
            value = getattr(self, attrname)
            if isinstance(value, CimpleFunc):
                self.funcs.append(value)

        # assemble the c source code file
        source_code = [self._cimple_header]
        for func in self.funcs:
            source_code.append(func.get_function_prototype()+';')
        for func in self.funcs:
            source_code.append(func.get_function_definition())
        source_code.append(self._cimple_footer)

        # get a compiler; arrange the build environment; figure out filenames
        cc = distutils.ccompiler.new_compiler()
        dir = tempfile.mkdtemp()
        name = random_name(8)
        srcfile = name+'.c'
        srcpath = os.path.join(dir, srcfile)
        objfile = cc.object_filenames([srcfile])[0]
        objpath = os.path.join(dir, objfile)
        libname = name
        libfilename = cc.library_filename(libname, lib_type='shared')
        libpath = os.path.join(dir, libfilename)

        # compile and link the library
        try:
            original_cwd = os.getcwd()
            os.chdir(dir)
            f = open(srcpath,'w')
            f.write('\n\n'.join(source_code))
            f.close()
            cc.compile([srcfile], extra_postargs=['-fPIC'])
            cc.link_shared_lib([objfile], libname)

            self.library = ctypes.CDLL(libpath)

        finally:
            os.chdir(original_cwd)
            # clean up the build environment
            for p in (srcpath, objpath, libpath):
                if os.path.exists(p):
                    os.unlink(p)
            if os.path.exists(dir):
                os.rmdir(dir)

        # propogate the specified restype and argtypes
        for func in self.funcs:
            foreign_func = getattr(self.library, func.name)
            foreign_func.restype = func.restype
            foreign_func.argtypes = func.argtypes
            setattr(self, func.name, foreign_func)

def random_name(length):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join([random.choice(alphabet) for _ in xrange(length)])

class DefinitionError(Exception): pass

def ctypes_obj_to_raw_c_code(type):
    try:
        return {ctypes.c_byte:      'signed char',
                ctypes.c_char:      'char',
                ctypes.c_char_p:    'char*',
                ctypes.c_double:    'double',
                ctypes.c_float:     'float',
                ctypes.c_int:       'signed int',
                ctypes.c_long:      'signed long',
                ctypes.c_longlong:  'signed long long',
                ctypes.c_short:     'signed short',
                ctypes.c_size_t:    'size_t',
                ctypes.c_ubyte:     'unsigned char',
                ctypes.c_uint:      'unsigned int',
                ctypes.c_ulong:     'unsigned long',
                ctypes.c_ulonglong: 'unsigned long long',
                ctypes.c_ushort:    'unsigned short',
                ctypes.c_void_p:    'void*',
                ctypes.c_wchar:     'wchar_t',
                ctypes.c_wchar_p:   'wchar_t*',
                ctypes.py_object:   'PyObject*',
                }[type]
    except KeyError:
        pass
    if type is None:
        return 'void'
    if isinstance(type, ctypes.Structure): # XXX this is wrong. type won't be an instance of Structure, it will be a class
        return 'struct '+type.__name__
    #if isinstance(type, ctypes._Pointer): # XXX untested
    #print type.__name__
    if type.__name__[:3] == 'LP_':
        inner_type = ctypes_obj_to_raw_c_code(type._type_)
        if inner_type[-1] == '*': return '%s*'  %inner_type
        else:                     return '(%s*)'%inner_type
    raise Exception('Type not known: %r'%type)

class CimpleFunc:
    def __init__(self, func, restype=None):
        self.name = func.func_name
        self.source_code = func.__doc__
        self.restype = restype

        if func.func_defaults is None:
            self.argtypes = []
            self.argnames = []
        else:
            if len(func.func_defaults) != func.func_code.co_argcount:
                raise DefinitionError('all function arguments must have '
                                      'a type specified')
            self.argtypes = func.func_defaults
            self.argnames = func.func_code.co_varnames[:len(self.argtypes)]

    def get_function_prototype(self):
        args = [ctypes_obj_to_raw_c_code(t) + ' ' + n
                for t,n in zip(self.argtypes, self.argnames)]
        return '%s %s(%s)'%(ctypes_obj_to_raw_c_code(self.restype),
                            self.name, ', '.join(args))

    def get_function_definition(self):
        return '%s\n{\n%s\n}\n' % (self.get_function_prototype(),
                                   self.source_code)

cimple_func = lambda *args, **kwargs: lambda func: CimpleFunc(func,
                                                              *args,**kwargs)


def minimal_example():

    class example(Cimple):

        _cimple_header = '#include <stdlib.h> \n#include <stdio.h>'

        @cimple_func(restype=ctypes.c_uint)
        def fib(n=ctypes.c_uint):
            r'''
            unsigned int a,b,c;
            a = b = 1;
            while (n > 0)
            {
              b += a;
              c = a;
              a = b;
              b = c;
              --n;
            }
            return a;
            '''

        @cimple_func()
        def go():
            r'''
            unsigned int X[] = {2, 5, 13, 40};
            register int i;
            for(i=0; i < 4 ; i++)
              printf("The %ith fibonaci number is %i.\n", X[i], fib(X[i]));
            '''

    examplelib = example()
    print 'type(examplelib.fib) is %r'%type(examplelib.fib)
    examplelib.go()

if __name__ == '__main__':
    minimal_example()

