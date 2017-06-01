"""Error handlers."""
import traceback
import asyncio
import random
import discord
from discord.ext.commands.errors import CommandOnCooldown as DiscordCNC
from discord.ext import commands
from util.const import *
from util.func import bdel
import util.commands as ext
from .cog import Cog

arg_err_map = {
    commands.MissingRequiredArgument: 'out enough arguments',
    commands.BadArgument: ' an invalid argument',
    commands.TooManyArguments: ' too many arguments'
}

class Errors(Cog):
    """Error handling gears."""
    async def on_error(self, ev_name, *ev_args, **ev_kwargs):
        kw_args = ', ' + (', '.join([k + '=' + str(ev_kwargs[k]) for k in ev_kwargs])) if ev_kwargs else ''
        self.logger.error(f'Event handler {ev_name} errored! Called with ' +
                          (', '.join([bdel(str(i), 'Command raised an exception: ') \
                          for i in ev_args]) if ev_args else 'nothing') + kw_args)
        self.logger.error(traceback.format_exc())

    async def on_command_error(self, ctx, exp):
        if self.bot.selfbot:
            try:
                cmdfix = self.bot.store['properties']['global']['selfbot_prefix']
            except KeyError:
                cmdfix = ctx.me.name[0].lower() + '.'
        else:
            cmdfix = self.bot.store.get_cmdfix(ctx.message)

        cproc = ctx.message.content.split()[0]
        cprocessed = bdel(cproc, cmdfix)
        c_key = str(exp)
        bc_key = bdel(c_key, 'Command raised an exception: ')
        eprefix = 's'

        try:
            cmid = ctx.guild.id
        except AttributeError:
            cmid = ctx.author.id
            eprefix = 'dm'

        if ctx.guild:
            location = ctx.guild.name
        else:
            location = '[DM with %s]' % str(ctx.author)

        # Logging
        if isinstance(exp, commands.CommandNotFound):
            self.logger.error(str(ctx.author) + ' in ' + location + ': command \'' + cprocessed + '\' not found')
        elif isinstance(exp, commands.CommandInvokeError):
            self.logger.error(str(ctx.author) + ' in ' + location + f': [cmd {cprocessed}] ' + bc_key)
            self.logger.error('Traceback (most recent call last):\n' + ''.join(traceback.format_tb(exp.original.__traceback__)) \
                              + type(exp.original).__name__ + ': ' + str(exp.original))
        elif isinstance(exp, ext.CommandPermissionError) or isinstance(exp, ext.OrCommandPermissionError):
            self.logger.error(str(ctx.author) + ' in ' + location + f': Not enough permissions for ' + ctx.message.content[:150])
        elif isinstance(exp, commands.MissingRequiredArgument) or \
             isinstance(exp, commands.BadArgument) or isinstance(exp, commands.TooManyArguments):
            self.logger.error(str(ctx.author) + ' in ' + location + f': [cmd {cprocessed}] Argument error. ' + str(exp))
        else:
            self.logger.error(str(ctx.author) + ' in ' + location + f': [cmd {cprocessed}] ' + str(exp) + ' (%s)' % type(exp).__name__)
            self.logger.error('Traceback (most recent call last):\n' + ''.join(traceback.format_tb(exp.__traceback__)) \
                              + type(exp).__name__ + ': ' + str(exp))


        # Message
        if isinstance(exp, commands.NoPrivateMessage):
            await ctx.send(npm_fmt.format(ctx.author, cprocessed, cmdfix))
        elif isinstance(exp, commands.CommandNotFound):
            pass
        elif isinstance(exp, commands.DisabledCommand):
            await ctx.send(ccd_fmt.format(ctx.author, cprocessed, cmdfix))
        elif isinstance(exp, ext.CommandOnCooldown) or isinstance(exp, DiscordCNC):
            await ctx.send(':warning: :gear: ' + random.choice(clocks))
        elif isinstance(exp, ext.PassException):
            pass
        elif isinstance(exp, ext.ReturnError):
            await ctx.send(exp.text)
        elif isinstance(exp, ext.CommandPermissionError):
            _perms = ''
            if exp.perms_required:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_required]
                if len(perm_list) > 1:
                    perm_list[-1] = '**and **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await ctx.send(cpe_fmt.format(ctx.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, ext.OrCommandPermissionError):
            _perms = ''
            if exp.perms_ok:
                perm_list = [i.lower().replace('_', ' ').title() for i in exp.perms_ok]
                if len(perm_list) > 1:
                    perm_list[-1] = '**or **' + perm_list[-1] # to cancel bold
                _perms = ', '.join(perm_list)
            else:
                _perms = 'Not specified'
            await ctx.send(ocpe_fmt.format(ctx.author, cprocessed, cmdfix, _perms))
        elif isinstance(exp, commands.CommandInvokeError):
            if isinstance(exp.original, discord.HTTPException):
                key = bdel(bc_key, 'HTTPException: ')
                if key.startswith('BAD REQUEST'):
                    key = bdel(bc_key, 'BAD REQUEST')
                    if key.endswith('Cannot send an empty message'):
                        await ctx.send(emp_msg.format(ctx.author, cprocessed, cmdfix))
                    elif c_key.endswith('BAD REQUEST (status code: 400)'):
                        if (eprefix == 'dm') and (ctx.command.name == 'user'):
                            await ctx.send('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                        else:
                            await ctx.send(big_msg.format(ctx.author, cprocessed, cmdfix))
                    else:
                        await ctx.send(msg_err.format(ctx.author, cprocessed, cmdfix, key))
                elif c_key.startswith('Command raised an exception: HTTPException: BAD REQUEST (status code: 400)'):
                    await ctx.send(big_msg.format(ctx.author, cprocessed, cmdfix))
                elif c_key.startswith('Command raised an exception: RuntimeError: PyNaCl library needed in order to use voice'):
                    await ctx.send('**The bot owner hasn\'t enabled voice!**')
                else:
                    await ctx.send(msg_err.format(ctx.author, cprocessed, cmdfix, key))
            elif isinstance(exp.original, asyncio.TimeoutError):
                await ctx.send(tim_err.format(ctx.author, cprocessed, cmdfix))
            elif ctx.command.name == 'eval':
                await ctx.send(ast_err.format(ctx.author, cprocessed, cmdfix))
            else:
                await ctx.send('⚠ Error in `%s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')
        elif type(exp) in (commands.MissingRequiredArgument, commands.TooManyArguments, commands.BadArgument):
            if ctx.invoked_subcommand is None:
                tgt_cmd = self.bot.all_commands[cprocessed]
            else:
                tgt_cmd = ctx.invoked_subcommand
            try:
                r_usage = bdel(bdel(bdel(tgt_cmd.help.split('\n')[-1], 'Usage: '),
                                         tgt_cmd.name), cprocessed)
            except AttributeError:
                r_usage = ''
            await ctx.send(arg_err.format(ctx.author, cprocessed, cmdfix, cmdfix +
                             cprocessed + r_usage, arg_err_map[type(exp)]))
        else:
            await ctx.send('⚠ Error in `%s`!\n```' % (cmdfix + cprocessed) + bc_key + '```')

def setup(bot):
    bot.add_cog(Errors(bot))
