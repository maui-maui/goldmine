"""Permission handling code."""
import asyncio
from .commands import CommandPermissionError, OrCommandPermissionError

def check_perms(ctx, perms_required):
    """Check permissions required for an action."""
    perms_satisfied = 0
    sender = ctx.author
    sender_id = sender.id
    bot_owner = ctx.bot.owner_user.id
    dc_perms = ctx.author.permissions_in(ctx.channel)
    try:
        sowner = ctx.guild.owner
        sowner_id = sowner.id
    except AttributeError: # if in a DM (PrivateChannel)
        sowner = ctx.channel.owner
        try:
            sowner_id = sowner.id
        except AttributeError: # if in a non-group DM (PrivateChannel)
            sowner = sender
            sowner_id = sender_id
    if sender_id == bot_owner:
        return True
    elif sender_id == ctx.bot.user.id:
        return True
    for i in perms_required:
        if (i == 'guild_owner') and (sender_id == sowner_id):
            perms_satisfied += 1
        elif i == 'bot_admin' and sender_id in ctx.bot.store['bot_admins']:
            perms_satisfied += 1
        else:
            try:
                if getattr(dc_perms, i.lower()):
                    perms_satisfied += 1
            except AttributeError:
                pass
    return len(perms_required) == perms_satisfied

def echeck_perms(ctx, perms_required):
    """Easy wrapper for permission checking."""
    if not check_perms(ctx, perms_required):
        raise CommandPermissionError(perms_required, message=ctx.message.content)

def or_check_perms(ctx, perms_ok):
    """Easy wrapper for permission checking."""
    results = set()
    for perm in perms_ok:
        res = check_perms(ctx, [perm])
        results.add(res)
    if not any(results):
        raise OrCommandPermissionError(perms_ok, message=ctx.message.content)
