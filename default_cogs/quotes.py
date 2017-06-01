"""The quote system!"""
import time
import random
import discord
import util.quote as quote
from discord.ext import commands
from util.perms import check_perms
from .cog import Cog

class Quotes(Cog):
    """Quotes from all over the place.
    Enjoy them, and give us some more :3"""

    @commands.command()
    async def quote(self, ctx, *args):
        """Reference a quote.
        Usage: quote {quote number}"""
        if not self.bot.store['quotes']:
            await ctx.send('There are no quotes. Add some first!')
            return
        try:
            qindx = args[0]
        except IndexError:
            qindx = random.randint(1, self.bot.store['quotes'].__len__())
        try:
            qindex = int(qindx)
        except ValueError:
            await ctx.send(ctx.mention + ' That isn\'t a number!')
            return
        if qindex < 1:
            await ctx.send(ctx.mention + ' There aren\'t negative or zero quotes!')
            return
        try:
            await ctx.send(quote.qrender(self.bot.store['quotes'][qindex - 1], qindex - 1, self.bot))
        except IndexError:
            await ctx.send(ctx.mention + ' That quote doesn\'t exist!')

    @commands.command(aliases=['quotes'])
    async def quotelist(self, ctx, *show_pages: int):
        """List all the quotes.
        Usage: quotelist"""
        if not self.bot.store['quotes']:
            await ctx.send('There are no quotes. Add some first!')
            return
        rshow_pages = [i for i in show_pages]
        pager = commands.Paginator(prefix='', suffix='', max_size=1595)
        if not show_pages:
            show_pages = (1,)
        for n, i in enumerate(self.bot.store['quotes']):
            qout = quote.qrender(i, n, self.bot)
            pager.add_line(qout)
        for page_n in show_pages:
            try:
                await ctx.send('**__Listing page *{0}* of *{1}* of quotes.__**\n'.format(page_n, len(pager.pages)) + pager.pages[page_n - 1])
            except IndexError:
                await ctx.send('**__Error: page *{0}* doesn\'t exist! There are *{1}* pages.__**'.format(page_n, len(pager.pages)))

    @commands.command(aliases=['addquote'])
    async def quoteadd(self, ctx, target: discord.User, *, text: str):
        """Add a quote.
        Usage: quoteadd [member] [text here]"""
        if len(text) > 360:
            await ctx.send(ctx.mention + ' Your text is too long!')
            return
        if target == self.bot.user:
            if not check_perms(ctx, ('bot_owner',)):
                await ctx.send(ctx.mention + ' You can\'t add a quote as me!')
                return
        fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
        q_template = {
            'id': 0,
            'quote': 'Say-whaaaa?',
            'author': ctx.author.display_name,
            'author_ids': [''],
            'date': fmt_time
        }
        mauthor = target
        q_template['quote'] = text.replace('\n', ' ').replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        q_template['author'] = mauthor.display_name
        if mauthor.display_name != mauthor.name:
            q_template['author'] += ' (' + mauthor.name + ')'
        q_template['author_ids'] = [mauthor.id, ctx.author.id]
        q_template['id'] = len(self.bot.store['quotes']) # +1 for next id, but len() counts from 1
        self.bot.store['quotes'].append(q_template)
        await ctx.send(f'Quote **#{q_template["id"] + 1}** added!')

    @commands.command(aliases=['modquote', 'editquote'])
    async def quotemod(self, ctx, qindex: int, *, text: str):
        """Edit an existing quote.
        Usage: quotemod [quote number] [new text here]"""
        if len(text) > 360:
            await ctx.send(ctx.mention + ' Your text is too long!')
            return
        if qindex < 0:
            await ctx.send(ctx.mention + ' There aren\'t negative quotes!')
            return
        try:
            q_template = self.bot.store['quotes'][qindex - 1]
        except IndexError:
            await ctx.send(ctx.mention + ' That quote doesn\'t already exist!')
            return
        if not check_perms(ctx, ('bot_admin',)):
            if ctx.author.id not in q_template['author_ids']:
                await ctx.send(ctx.mention + ' You need more permissions!')
                return
        q_template['quote'] = text.replace('\n', ' ').replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        self.bot.store['quotes'][qindex - 1] = q_template
        await ctx.send(f'Quote **#{qindex}** edited!')

    @commands.command(aliases=['rmquote', 'delquote'])
    async def quotedel(self, ctx, qindex: int):
        """Delete an existing quote.
        Usage: quotedel [quote number]"""
        if qindex < 0:
            await ctx.send(ctx.mention + ' There aren\'t negative quotes!')
            return
        try:
            q_target = self.bot.store['quotes'][qindex - 1]
        except IndexError:
            await ctx.send(ctx.mention + f' Quote **#{qindex}** doesn\'t already exist!')
            return
        _pcheck = check_perms(ctx, ('bot_admin',))
        if (ctx.author.id == q_target['author_ids'][0]) or (_pcheck):
            del self.bot.store['quotes'][qindex - 1]
            await ctx.send(f'Quote **#{qindex}** deleted.')
        else:
            await ctx.send(ctx.mention + f' You can\'t delete quote **#{qindex}** because you didn\'t write it. Sorry!')

def setup(bot):
    c = Quotes(bot)
    bot.add_cog(c)
