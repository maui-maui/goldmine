"""The REPL module for power users."""
from contextlib import redirect_stdout
import importlib.util
from util.asizeof import asizeof
from util.perms import echeck_perms
from util.const import eval_blocked
import util.dynaimport as di
from .cog import Cog

for mod in ['asyncio', 're', 'os', 'sys', 'io', 'traceback', 'inspect',
            'asteval', 'async_timeout', 'discord', 'subprocess', 'contextlib']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

class REPL(Cog):
    def __init__(self, bot):
        self.sessions = set()
        self.asteval = asteval.Interpreter(use_numpy=False)
        self.root_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].core_file))
        super().__init__(bot)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n>')

    def get_syntax_error(self, e):
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    async def math_task(self, code: str):
        eval_exc = self.loop.run_in_executor(None, self.bot.asteval.eval, code)
        return await eval_exc

    async def asteval_iface(self, code):
        for key in eval_blocked:
            if re.search(key, code):
                return '⚠ Blocked keyword found!'
        try:
            sio = io.StringIO()
            with async_timeout.timeout(3):
                with contextlib.redirect_stdout(sio):
                    m_result = await self.math_task(code)
            v = sio.getvalue()
            if v:
                m_result = v + str(m_result)
        except (asyncio.TimeoutError, RuntimeError) as exp:
            resp = '⚠ Your code took too long to evaluate!'
            if isinstance(exp, RuntimeError):
                if str(exp).startswith('Execution exceeded time limit, max runtime is '):
                    return resp
                else:
                    return '⚠ Timeouted!'
            else:
                return resp
        if self.bot.asteval.error:
            err = self.bot.asteval.error[0].get_error()
            if err[0] == 'MemoryError':
                await self.bot.reset_asteval(reason='due to MemoryError')
                return '⚠ Please rerun your code!'
            else:
                return '\n'.join(err)
        try:
            byte_size = await self.loop.run_in_executor(None, asizeof, self.bot.asteval.symtable)
            if byte_size > 50_000_000: # 110 MiB 115_343_360, 107 MiB 112_197_632, 107 MB 107_000_000
                await self.bot.reset_asteval(reason='due to memory usage > 50M', note=f'was using {byte_size / 1048576} MiB')
        except MemoryError:
            await self.bot.reset_asteval(reason='due to MemoryError during asizeof')
        else:
            del byte_size
        return m_result
    
    async def emerg_quit_task(self, ctx):
        while True:
            msg = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel, check=lambda m: m.content.startswith('`'))
            if msg.content.replace('`', '').replace('\n', '').strip('py') in ['quit', 'exit', 'exit()', 'sys.exit()']:
                await asyncio.sleep(1)
                if msg.channel.id in self.sessions:
                    await self.bot.send_message(ctx.message.channel, '**Exiting...**')
                    self.sessions.remove(msg.channel.id)
                    raise commands.PassException()

    @commands.command(pass_context=True)
    async def repl(self, ctx, *flags: str):
        """A REPL, in Discord.
        Usage: repl {flags}"""
        await echeck_perms(ctx, ('bot_owner',))
        msg = ctx.message

        def import_by_path(name: str, path: str) -> None:
            """Import a module (name) from path."""
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        platform_shell = lambda s: subprocess.check_output(['bash', '-c', s]).decode('utf-8', 'ignore')
        if sys.platform == 'win32':
            platform_shell = lambda s: subprocess.check_output(s.split()).decode('utf-8', 'ignore')
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': msg,
            'server': msg.server,
            'channel': msg.channel,
            'author': msg.author,
            'last': None,
            'kek': 'lol',
            'self': self,
            'msg': msg,
            'test': 'Test right back at ya!',
            'lol': 'kek',
            'loop': self.bot.loop,
            'context': ctx,
            'shell': platform_shell,
            'file_import': import_by_path,
            'get_server': lambda s_name: {s.name: s for s in self.bot.servers}[s_name],
            'server_dict': lambda: {s.name: s for s in self.bot.servers},
            'get_voice': lambda: {self.bot.cogs['Voice'].voice_states[s].voice.channel.server.name: [str(e) for e in list(self.bot.cogs['Voice'].voice_states[s].songs._queue) + [self.bot.cogs['Voice'].voice_states[s].current] if e] for s in self.bot.cogs['Voice'].voice_states if self.bot.cogs['Voice'].voice_states[s].voice},
            'rgb_to_hex': lambda r, g, b: '#%02X%02X%02X' % (r, g, b),
            'hex_to_rgb': lambda shex: [int(h.upper(), 16) for h in [shex.replace('#', '').replace('0x', '')[i:i + 2] for i in range(0, len(shex.replace('#', '').replace('0x', '')), 2)]],
            'is_playing': lambda s: self.bot.cogs['Voice'].voice_states[{g.name: g for g in self.bot.servers}[s].id].current.player.is_playing(),
            'vstate': lambda s: self.bot.cogs['Voice'].voice_states[{g.name: g for g in self.bot.servers}[s].id],
            'cm_discrim': lambda d: list(set(str(m) for m in self.bot.get_all_members() if m.discriminator == d)),
        }
        is_shell = False
        valid_flags = ['public', 'asteval', 'py', 'split', 'shell']
        for flag in flags:
            if flag not in valid_flags:
                await self.bot.say(f'Flag `{flag}` is invalid. Valid flags are `{", ".join(valid_flags)}`.')
                return
        if 'public' in flags:
            del variables['self']
            del variables['bot']
            del variables['ctx'].bot
            checks = {}
            ex_check = lambda m: ((m.author.id != self.bot.user.id) if not self.bot.selfbot else True) and (not m.author.bot) and (not m.content.endswith('\u200b'))
        else:
            checks = {
                'author': msg.author
            }
            ex_check = lambda m: not m.content.endswith('\u200b')
        use_asteval = 'asteval' in flags
        truncate = 'split' not in flags
        if 'py' in flags:
            await self.bot.say('⚠ Flag `py` is not implemented yet!')
            return
        if 'shell' in flags:
            is_shell = True

        if msg.channel.id in self.sessions:
            await self.bot.say('Already running a REPL session in this channel. Exit it with `quit`.')
            return
        self.sessions.add(msg.channel.id)

        alt_prefix = []
        if alt_prefix:
            prefix = ' '.join(alt_prefix)
        else:
            prefix = '`'

        flags_imsg = ''
        if flags:
            flags_imsg = ' Using flag(s) `' + ' '.join(flags) + '`.'
        await self.bot.say(f'Enter code to execute or evaluate. `exit()` or `quit` to exit.{flags_imsg} Prefix is: ```{prefix}```')
        quit_task = self.loop.create_task(self.emerg_quit_task(ctx))
        while True:
            response = await self.bot.wait_for_message(channel=msg.channel, check=lambda m: m.content.startswith(prefix) and ex_check(m), **checks)
            variables['message'] = response
            variables['msg'] = response
            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()', 'sys.exit()'):
                await self.bot.say('**Exiting...**')
                self.sessions.remove(msg.channel.id)
                quit_task.cancel()
                return

            if use_asteval:
                result = await self.asteval_iface(cleaned)
                if inspect.isawaitable(result):
                    result = await result
                fmt = str(result) + '\n'
            elif is_shell:
                try:
                    result = await self.loop.run_in_executor(None, platform_shell, cleaned)
                except subprocess.CalledProcessError as e:
                    result = 'Error. Exit code: ' + str(e.returncode) + '\n'
                    if e.output:
                        result += 'Output: ' + e.output.decode('utf-8', 'ignore') + '\n'
                    if e.stdout:
                        result +='Output: ' + e.stdout.decode('utf-8', 'ignore') + '\n'
                    if e.stderr:
                        result +='Output: ' + e.stderr.decode('utf-8', 'ignore') + '\n'
                fmt = result + '\n'
            else:
                executor = exec
                if cleaned.count('\n') == 0:
                    try:
                        code = compile(cleaned, '<repl session>', 'eval')
                    except SyntaxError:
                        pass
                    else:
                        executor = eval
                if executor is exec:
                    try:
                        code = compile(cleaned, '<repl session>', 'exec')
                    except SyntaxError as e:
                        await self.bot.say(self.get_syntax_error(e))
                        continue
                fmt = None
                stdout = io.StringIO()
                try:
                    with redirect_stdout(stdout):
                        result = await self.loop.run_in_executor(None, executor, code, variables)
                        if inspect.isawaitable(result):
                            result = await result
                except Exception as e:
                    value = stdout.getvalue()
                    fmt = '{}{}\n'.format(value, traceback.format_exc())
                else:
                    value = stdout.getvalue()
                    if result is not None:
                        fmt = f'{value}{result}\n'
                        variables['last'] = result
                    elif value:
                        fmt = f'{value}\n'
            try:
                if fmt is not None:
                    fmt = fmt.replace(self.root_path, 'bot_path')
                    if len(fmt) > 2000:
                        if truncate:
                            await self.bot.send_message(msg.channel, f'```py\n{fmt}```')
                        else:
                            for i in range(0, len(fmt), 1990):
                                await self.bot.send_message(msg.channel, '```py\n%s```' % fmt[i:i+1992])
                    else:
                        await self.bot.send_message(msg.channel, f'```py\n{fmt}```')
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await self.bot.send_message(msg.channel, f'Unexpected error: `{e}`')
        quit_task.cancel()

def setup(bot):
    bot.add_cog(REPL(bot))
