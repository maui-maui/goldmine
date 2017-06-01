from discord.ext.commands.errors import *

def quoted_word(view):
    current = view.current

    if current is None:
        return None

    result = [current]

    while not view.eof:
        current = view.get()
        if not current:
            return ''.join(result)

        if current == '\\':
            next_char = view.get()
            if not next_char:
                # if we aren't then we just let it through
                return ''.join(result)

            # different escape character, ignore it
            view.undo()
            result.append(current)
            continue

        if current.isspace():
            # end of word found
            return ''.join(result)

        result.append(current)

del CommandOnCooldown
class CommandOnCooldown(CommandError):
    """Exception raised when the command being invoked is on cooldown.
    Attributes
    -----------
    cooldown: Cooldown
        A class with attributes ``rate``, ``per``, and ``type`` similar to
        the :func:`cooldown` decorator.
    retry_after: float
        The amount of seconds to wait before you can retry again.
    """
    def __init__(self, cooldown, retry_after, ctx):
        self.cooldown = cooldown
        self.retry_after = retry_after
        self.ctx = ctx
        super().__init__('You are on cooldown. Try again in {:.2f}s'.format(retry_after))

class ReturnError(CommandError):
    """Raised with a message to send it to chat."""
    def __init__(self, msg, ctx):
        self.text = msg.format(ctx)
        self.ctx = ctx
        super().__init__(msg.format(ctx))

class PassException(CommandError):
    """Just pass. Used to simulate the return statement."""
    def __init__(self):
        super().__init__('Pass exception occured. You shouldn\'t be seeing this!')

class CommandPermissionError(CommandError):
    """Subclass of CommandError for permission handling errors."""
    def __init__(self, perms_required, message=None, *args):
        self.perms_required = perms_required
        super().__init__(message=message, *args)

class OrCommandPermissionError(CommandError):
    """Subclass of CommandError for permission handling errors."""
    def __init__(self, perms_ok, message=None, *args):
        self.perms_ok = perms_ok
        super().__init__(message=message, *args)
