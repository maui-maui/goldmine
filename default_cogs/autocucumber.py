"""Awesome auto cucumber."""
import os
import copy
import aiohttp
import async_timeout
from discord.ext import commands
from util.perms import echeck_perms
from .cog import Cog

class AutoCucumber(Cog):
    """Spelling corrector :)"""
    special_chars = list('~`!@#$%^&*()-_=+[{]}\\|:;<,>.?/\'"')
    punctuation_chars = list(';!?.,:')
    def __init__(self, bot):
        super().__init__(bot)
        self.enabled = False

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
                await msg.edit(content=final)

    @commands.command(aliases=['autocucumber', 'cucumber', 'ac'])
    async def tac(self, ctx):
        """Toggle AutoCucumber.
        Usage: tac"""
        echeck_perms(ctx, ('bot_owner',))
        self.enabled = not self.enabled
        await ctx.send('Autocucumber is now ' + ('on.' if self.enabled else 'off.'))

    @commands.command(aliases=['spellcheck', 'autocorrect'])
    async def correct(self, ctx, *, message: str):
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
        await ctx.send(ctx.mention + ' Correction result: ' + final)

def setup(bot):
    bot.add_cog(AutoCucumber(bot))
