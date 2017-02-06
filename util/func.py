"""General utility functions."""
import contextlib
import random
import inspect
from asyncio import ensure_future
from functools import partial
import datetime
from util.commands.errors import PassException
def bdel(s, r): return (s[len(r):] if s.startswith(r) else s)

class DiscordFuncs():
    def __init__(self, bot):
        self.bot = bot
    def __getattr__(self, name):
        new_func = None
        coro = getattr(self.bot, name)
        if not callable(coro):
            raise AttributeError('Class can only access client functions')
        def async_wrap(coro, *args, **kwargs):
            ensure_future(coro(*args, **kwargs))
        new_func = partial(async_wrap, coro)
        new_func.__name__ = coro.__name__
        new_func.__qualname__ = coro.__qualname__
        return new_func

def _import(mod_name: str, var_name=None, attr_name=''):
    ret = "globals()['{}'] = imp('{}')"
    if var_name:
        if attr_name:
            attr_name = '.' + attr_name
        ret = ret.format(var_name, mod_name) + attr_name
    else:
        ret = ret.format(mod_name, mod_name)
    return ret


def _set_var(var_name: str, expr: str):
    return "globals()['{}'] = {}".format(var_name, expr)

def _del_var(var_name: str):
    return "del globals()['{}']".format(var_name)

snowtime = lambda i: datetime.datetime.fromtimestamp(((float(int(i)) / 4194304.0) + 1420070400000.0 + 18000000.0) / 1000.0).strftime('%a %b %d, %Y %I:%M:%S %p')

class PrintException(Exception):
    """An exception that prints the error."""
    def __init__(self, err):
        print(str(err))
        self.err = err
        super().__init__()

@contextlib.contextmanager
def assert_msg(ctx, msg: str):
    """Assert. If error, send msg."""
    try:
        yield
    except AssertionError:
        ensure_future(ctx.bot.send_message(ctx.message.channel, msg))
        raise PassException()

def check(in_bool: bool):
    """Replacement for assert statement."""
    if not in_bool:
        raise AssertionError('Assertion failed from check()!')

def encode(content: str) -> str:
    """Goldcode encoder."""
    orig_ords = [ord(c) for c in list(content)]
    aift = round(random.uniform(1, 145), random.randint(3, 6))
    aift_aift = random.randint(1, 14)
    aifted_ords = [float(o) + aift for o in orig_ords]
    join_chars = list('@!($)_*#%"}?\'=-`\\][')
    join_char = random.choice(join_chars)
    ords_str = join_char.join([str(s) for s in aifted_ords]) + '~' + join_char.join([str(float(ord(c)) + aift) for c in list('3MainShiftCorrect')])
    fn_head_join = random.choice(list('|^&'))
    _g = random.uniform(1, 51)
    head_keys = {
        'd': aift + aift_aift, # encoded (aift_aifted) aift
        'g': _g, # aift for join char index
        'l': (float(join_chars.index(join_char)) - 4.4689257) + _g
    }
    head_str = ';'.join([k + str(head_keys[k]) for k in head_keys])
    final = head_str + fn_head_join + ords_str
    return final

def decode(content: str) -> str:
    """Goldcode decoder."""
    try:
        expected_key = '3MainShiftCorrect'
        join_chars = list('@!($)_*#%"}?\'=-`\\][')
        aift_key = content.split('~')[1]
        content = content.replace('~' + aift_key, '') # discard aift key
        head_keys = {}
        for try_decode_head in list('|^&'):
            if try_decode_head in content:
                dec_head_1 = content.split(try_decode_head)[0]
                head_r_keys = dec_head_1.split(';')
                for rkey in head_r_keys:
                    head_keys[rkey[0]] = rkey[1:]
                no_head_content = content.replace(dec_head_1 + try_decode_head, '')
        head_keys['d'] = float(head_keys['d'])
        head_keys['g'] = float(head_keys['g'])
        head_keys['l'] = float(head_keys['l'])
        j = join_chars[int((head_keys['l'] + 4.4689257) - head_keys['g'])]
        for try_aift_aift in range(1, 14):
            aift_to_try = head_keys['d'] - float(try_aift_aift)
            if ''.join([chr(int(cn - aift_to_try)) for cn in [float(sf) for sf in aift_key.split(j)]]) == expected_key:
                aift = aift_to_try
                break
        content = no_head_content
        dec = ''.join([chr(int(cn - aift)) for cn in [float(sf) for sf in content.split(j)]])
        return dec
    except Exception:
        return '⚠ Couldn\'t decode. Maybe your content is corrupted?'

async def async_encode(content: str) -> str:
    """Coroutine version of encode()."""
    orig_ords = [ord(c) for c in list(content)]
    aift = round(random.uniform(1, 145), random.randint(3, 6))
    aift_aift = random.randint(1, 14)
    aifted_ords = [float(o) + aift for o in orig_ords]
    join_chars = list('@!($)_*#%"}?\'=-`\\][')
    join_char = random.choice(join_chars)
    ords_str = join_char.join([str(s) for s in aifted_ords]) + '~' + join_char.join([str(float(ord(c)) + aift) for c in list('3MainShiftCorrect')])
    fn_head_join = random.choice(list('|^&'))
    _g = random.uniform(1, 51)
    head_keys = {
        'd': aift + aift_aift, # encoded (aift_aifted) aift
        'g': _g, # aift for join char index
        'l': (float(join_chars.index(join_char)) - 4.4689257) + _g
    }
    head_str = ';'.join([k + str(head_keys[k]) for k in head_keys])
    final = head_str + fn_head_join + ords_str
    return final

async def async_decode(content: str) -> str:
    """Coroutine version of decode()."""
    try:
        expected_key = '3MainShiftCorrect'
        join_chars = list('@!($)_*#%"}?\'=-`\\][')
        aift_key = content.split('~')[1]
        content = content.replace('~' + aift_key, '') # discard aift key
        head_keys = {}
        for try_decode_head in list('|^&'):
            if try_decode_head in content:
                dec_head_1 = content.split(try_decode_head)[0]
                head_r_keys = dec_head_1.split(';')
                for rkey in head_r_keys:
                    head_keys[rkey[0]] = rkey[1:]
                no_head_content = content.replace(dec_head_1 + try_decode_head, '')
        head_keys['d'] = float(head_keys['d'])
        head_keys['g'] = float(head_keys['g'])
        head_keys['l'] = float(head_keys['l'])
        j = join_chars[int((head_keys['l'] + 4.4689257) - head_keys['g'])]
        for try_aift_aift in range(1, 14):
            aift_to_try = head_keys['d'] - float(try_aift_aift)
            if ''.join([chr(int(cn - aift_to_try)) for cn in [float(sf) for sf in aift_key.split(j)]]) == expected_key:
                aift = aift_to_try
                break
        content = no_head_content
        dec = ''.join([chr(int(cn - aift)) for cn in [float(sf) for sf in content.split(j)]])
        return dec
    except Exception:
        return '⚠ Couldn\'t decode. Maybe your content is corrupted?'

def decoy_print(*ina: str) -> str:
    """Print function!"""
    return ' '.join(ina)

def dprint(*ina: str):
    """Print function!"""
    print(' '.join(str(a) for a in ina))

def _get_variable(name):
    stack = inspect.stack()
    try:
        for frames in stack:
            try:
                frame = frames[0]
                current_locals = frame.f_locals
                if name in current_locals:
                    return current_locals[name]
            finally:
                del frame
    finally:
        del stack

def numberToBase(n, b):
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n /= b
    return digits[::-1]

def smartjoin(l):
    if len(l) > 1:
        l[-1] = 'and ' + l[-1]
    return ', '.join(l)

ceaser_encode = (lambda s, k: s.translate(str.maketrans(('abcdefghijklmnopqrstuvwxyz' + 'abcdefghijklmnopqrstuvwxyz'.upper()), (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz') + (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz').upper())))
ceaser_decode = (lambda s, k: s.translate(str.maketrans((lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz') + (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz').upper(), ('abcdefghijklmnopqrstuvwxyz' + 'abcdefghijklmnopqrstuvwxyz'.upper()))))

def date_suffix(rday):
    day = str(rday)
    if day[-1] == '1':
        return 'st'
    elif day[-1] == '2':
        return 'nd'
    elif day[-1] == '3':
        return 'rd'
    else:
        return 'th'
