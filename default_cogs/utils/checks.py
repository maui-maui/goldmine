import discord
from discord.ext import commands
import discord.utils

#
# This is a modified version of checks.py, originally made by Rapptz
#
#          https://github.com/Rapptz/RoboDanny/tree/async
#

def is_owner_check(ctx):
    return ctx.author.id == ctx.bot.owner_user.id

def is_owner():
    return commands.check(is_owner_check)

# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually having
# the permissions required for them.
# Of course, the owner will always be able to execute commands.

def check_permissions(ctx, perms):
    if is_owner_check(ctx):
        return True
    elif not perms:
        return False

    ch = ctx.channel
    author = ctx.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())

def role_or_permissions(ctx, check, **perms):
    if check_permissions(ctx, perms):
        return True

    ch = ctx.channel
    author = ctx.author
    if isinstance(msg.channel, discord.abc.PrivateChannel):
        return False # can't have roles in PMs

    role = discord.utils.find(check, author.roles)
    return role is not None

def mod_or_permissions(**perms):
    def predicate(ctx):
        guild = ctx.guild
        mod_role = settings.get_guild_mod(guild).lower()
        admin_role = settings.get_guild_admin(guild).lower()
        return role_or_permissions(ctx, lambda r: r.name.lower() in (mod_role,admin_role), **perms)

    return commands.check(predicate)

def admin_or_permissions(**perms):
    def predicate(ctx):
        guild = ctx.guild
        admin_role = settings.get_guild_admin(guild)
        return role_or_permissions(ctx, lambda r: r.name.lower() == admin_role.lower(), **perms)

    return commands.check(predicate)

def guildowner_or_permissions(**perms):
    def predicate(ctx):
        if ctx.guild is None:
            return False
        guild = ctx.guild
        owner = guild.owner

        if ctx.author.id == owner.id:
            return True

        return check_permissions(ctx,perms)
    return commands.check(predicate)

def guildowner():
    return guildowner_or_permissions()

def admin():
    return admin_or_permissions()

def mod():
    return mod_or_permissions()
