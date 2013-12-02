
"""
Shell utilities.

This automatically imports all of the following modules:
shutil, os, glob, re

Following is imported into the main namespace:
os.path.join as join, os.path.exists as exists

glob.glob_single defined.

j operator:   'aa' |j| 'bb' -> os.path.join('aa', 'bb') -> 'aa/bb'
"""

import glob
import os
from os.path import join, exists
import re
import shutil
import sys

def glob_single(path):
    """Like glob.glob, but only returns a single result.

    If more than one result matches, raise ValueError.  """
    files = glob.glob(path)
    if len(files) != 1:
        raise ValueError("Detected more than one file at %s"%path)
    return files[0]
# My first name was glob1, but that is already used in the module!
glob.glob_single = glob_single
del glob_single


class Infix:
    def __init__(self, function):
        self.function = function
    def __ror__(self, other):
        return Infix(lambda x, self=self, other=other: self.function(other, x))
    def __or__(self, other):
        return self.function(other)

j = Infix(os.path.join)

#print '' |j| 'aa' |j| 'bb'
