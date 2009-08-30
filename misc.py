'''fitz.misc - various useful (but unrelated) one-off functions and classes
'''
import os
import os.path
import logging


log = logging.getLogger('fitz')


def assert_directory_exists(path):
    '''create the directory if it does not exist

    designed for *nix, but might be cross-platform. I haven\'t tested.
    '''
    if path == '' or path == '/':
        return
    if not os.path.exists(path):
        assert_directory_exists(os.path.dirname(path))
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise AssertionError, '%r is not a directory, but it should be' % path


def findall(pattern, data):
    '''finds all non-overlapping occurances of "pattern" in the string "data"

    return value is a list of re.Match objects
    '''
    matches = []
    pos = 0
    while True:
        match = pattern.search(data, pos=pos)
        if match is None:
            return matches
        matches.append(match)
        pos = match.end(0)


class ShortCircuitCallbacks(Exception): pass

class Callbacks:
    '''Base class for objects that support registering and triggering callbacks

    a bit like the signals on gobjects from glib, but written in python
    '''

    def __init__(self):
        self._callbacks = {}
        self._suppressed_callbacks = []

    def register_callback(self, signal, callback, *args):
        '''register a function to be called when signal is triggered

        callback should be a callable object. It will be called with
        the *args given here followed by the *args given by trigger_callback()
        The **kwargs given to trigger_callback() are also passed.

        The return value is a callable object that may be used to unregister
        the callback. There is no other way to unregister a callback.

        A callbacks may raise a ShortCircuitCallbacks instance to prevent
        further callbacks from getting called. The return value of
        .trigger_callback() will be the first arg passed to
        ShortCircuitCallbacks.
        '''
        callback_list = self._callbacks.setdefault(signal, [])
        entry = (callback, args)
        callback_list.append(entry)
        return lambda : callback_list.remove(entry)

    def trigger_callback(self, signal, *args, **kwargs):
        'trigger the signal'
        if self.callback_suppressed(signal):
            return
        log.debug('callback triggered: %s %r %r'%(signal, args, kwargs))
        try:
            callbacks = self._callbacks.get(signal,())
            if len(callbacks) == 0:
                log.warn('%r was triggered, but it has no handlers! '
                         'maybe it\'s misspelled?'%signal)
            for callback,curried_args in callbacks:
                callback(*(curried_args+args), **kwargs)
        except ShortCircuitCallbacks, e:
            if len(e.args) > 0:
                return e.args[0]

    def suppress_callback(self, signal):
        'any calls to trigger_callback() using signal will be ignored'
        self._suppressed_callbacks.append(signal)

    def callback_suppressed(self, signal):
        'query whether signal is being suppressed'
        return signal in self._suppressed_callbacks

    def resume_callback(self, signal):
        'opposite of suppress_callback: trigger_callback() will work again'
        if self.callback_suppressed(signal):
            self._suppressed_callbacks.remove(signal)


def cached_property(producer_func):
    '''decorator for caching the results of (mostly) static calculations

    If the calculations are not actually static, you can force a
    recalculation on next attribute access by using del on the attribute
    to clear the cache. See usage below for more.

    Usage:

    from fitz.misc import cached_property
    class k:
        @cached_property
        def blerg(self):
            [time-consuming calculation]
            return value
    i = k()
    i.blerg     # does the calculation and returns the value
    i.blerg     # retrieves value from cache without running the code
    i.blerg     # still in the cache, so no calculation
    del i.blerg # clears the cached value
    i.blerg     # does the calculation again since the cache was cleared

    implementation detail: the attribute "_property_cache" will be added to
                           the instance
    '''
    def cached_property_getter(self):
        try:
            cache = self._property_cache
        except AttributeError:
            cache = self._property_cache = {}
        try:
            return cache[producer_func.__name__]
        except KeyError:
            rval = producer_func(self)
            cache[producer_func.__name__] = rval
            return rval
    def cached_property_deleter(self):
        try:
            cache = self._property_cache
        except AttributeError:
            cache = self._property_cache = {}
        try:
            del cache[producer_func.__name__]
        except KeyError:
            pass
    return property(cached_property_getter, None, cached_property_deleter)


class AtomicFileWriter(file):
    '''subclass of file that makes overwriting files an atomic operation

    That is, either the whole file is committed to disk, or else the old
    version of the file is still in place. This is accomplished by writing
    the data to x.tmp, and then renaming x.tmp to x when .close() is called.
    On many filesystems (eg ext3 with the default data=ordered option) this
    ensures that when the file x already exists, it is "overwritten"
    atomically.

    This is very useful for program state and config files.
    '''

    def __init__(self, path, mode='w'):
        assert 'w' in mode
        self.final_path = path
        self.initial_path = path+'.tmp'
        file.__init__(self, self.initial_path, mode)
        self._close_has_been_called = False

    def __del__(self):
        self.close()

    def close(self):
        file.close(self)
        if not self._close_has_been_called:
            os.rename(self.initial_path, self.final_path)
            self._close_has_been_called = True


def dependency(target, *prereqs):
    """decorator for creating makefile-like lazily-evaluated rules

    Typical usage might be something like this:

    from fitz.misc import dependency
    @dependency('index.html', 'blog-entries.xml', 'blog-entries-index.xsl',
                'blog-entries-template.xsl')
    def _(outfile, xmlfile, xsltfile, *rest):
        spawn_process('xsltproc', '--xinclude', '--output', outfile,
                      xsltfile, xmlfile)

    The first argument to dependency() is a filename that the rule is
    responsible for creating or updating, called the target. The *rest of
    the arguments are files that the target depends upon. If any of them
    are newer than the target (according to mtime) or if the target doesn't
    even exist yet, then the decorated function is called. Otherwise,
    everything is assumed to be up-to-date and the decorated function is
    never called.
    """
    def check_dependency(creator_func):
        if os.path.exists(target):
            target_mtime = os.stat(target).st_mtime
            for prereq in prereqs:
                if target_mtime < os.stat(prereq).st_mtime:
                    break
            else:
                log.debug('target is up-to-date: %s' % target)
                return
        log.info('creating target %s' % target)
        creator_func(target, *prereqs)
    return check_dependency
