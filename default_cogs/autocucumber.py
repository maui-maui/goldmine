"""Awesome auto cucumber."""
import os
import re
import copy
import aiohttp
import async_timeout
import util.commands as commands
from collections import Counter
from util.autocorrect import Corrector
from util.perms import echeck_perms
import util.dynaimport as di
from .cog import Cog

class AutoCucumber(Cog):
    """Spelling corrector :)"""
    special_chars = list('~`!@#$%^&*()-_=+[{]}\\|:;<,>.?/\'"')
    punctuation_chars = list(';!?.,:')
    def __init__(self, bot):
        super().__init__(bot)
        self.enabled = False
        self.corrections = {}
        self.corrector = None
        self.loop.create_task(self.create_corrector())
        self.load_data()
        self.emoji_re = re.compile(u'[\U00010000-\U0010ffff\u2615]')
        self.word_re = re.compile(r"[\w']+|[.,!?;:]")

    def load_data(self, text=None):
        """Load and parse spelling data."""
        if text is None:
            with open(os.path.join(self.bot.dir, 'assets', 'corrections.txt')) as f:
                text = f.read()
        items = text.split('\n')
        raw_pairs = [item.split('->') for item in items]
        for pair in raw_pairs:
            self.corrections[pair[0]] = pair[1].split(', ')[0]

    async def init_corrector(self):
        with async_timeout.timeout(60):
            async with aiohttp.request('GET', 'http://norvig.com/big.txt') as r:
                text = await r.text()
        with open(os.path.join(self.bot.dir, 'data', 'autocorrect.txt'), 'a') as f:
            f.write(text)
        self.corrector = await self.loop.run_in_executor(None, Corrector)

    async def create_corrector(self):
        """Create the auto correction engine."""
        try:
            self.corrector = await self.loop.run_in_executor(None, Corrector)
        except FileNotFoundError:
            await self.init_corrector()

    async def on_not_command(self, msg):
        if self.enabled:
            if msg.content.endswith('\u200b'): return
            old = copy.copy(msg)
            words = re.findall(self.word_re, msg.content)
            result = ''
            for word in words:
                if '`' in word:
                    result += word
                elif word in self.punctuation_chars:
                    result = result[:-1]
                    result += word + ' '
                elif word in self.special_chars:
                    result += word
                elif re.search(self.emoji_re, word):
                    result += word + ' '
                elif word in self.corrections:
                    result += self.corrections[word] + ' '
                else:
                    result += self.corrector.correct(word) + ' '
            final = result[0].upper() + result[1:]
            raw_final = final.replace('\u200b', '').replace('\n', '')
            raw_msg_content = msg.content.replace('\u200b', '').replace('\n', '')
            if raw_final != raw_msg_content:
                await self.bot.edit_message(msg, final)

    @commands.command(pass_context=True, aliases=['autocucumber', 'cucumber', 'ac'])
    async def tac(self, ctx):
        """Toggle AutoCucumber.
        Usage: tac"""
        echeck_perms(ctx, ('bot_owner',))
        self.enabled = not self.enabled
        await self.bot.say('Autocucumber is now ' + ('on.' if self.enabled else 'off.'))

    @commands.command(aliases=['spellcheck', 'autocorrect'])
    async def correct(self, *, message: str):
        """Correct a message.
        Usage: correct [message]"""
        words = re.findall(self.word_re, message)
        result = ''
        for word in words:
            if '`' in word:
                result += word
            elif word in self.punctuation_chars:
                result = result[:-1]
                result += word + ' '
            elif word in self.special_chars:
                result += word
            elif re.search(self.emoji_re, word):
                result += word + ' '
            elif word in self.corrections:
                result += self.corrections[word] + ' '
            else:
                result += self.corrector.correct(word) + ' '
        final = result[0].upper() + result[1:]
        await self.bot.reply('correction result: ' + final)

def setup(bot):
    bot.add_cog(AutoCucumber(bot))

