"""The quote system!"""
import time
import random
import discord
import util.quote as quote
import util.commands as commands
from util.perms import check_perms
from .cog import Cog

class Quotes(Cog):
    """Quotes from all over the place.
    Enjoy them, and give us some more :3"""

    @commands.command(aliases=['randquote', 'getquote'])
    async def quote(self, *args):
        """Reference a quote.
        Usage: quote {quote number}"""
        if not self.bot.store['quotes']:
            await self.bot.say('There are no quotes. Add some first!')
            return
        try:
            qindx = args[0]
        except IndexError:
            qindx = random.randint(1, self.bot.store['quotes'].__len__())
        try:
            qindex = int(qindx)
        except ValueError:
            await self.bot.reply('that isn\'t a number!')
            return
        if qindex < 1:
            await self.bot.reply('there aren\'t negative or zero quotes!')
            return
        try:
            await self.bot.say(quote.qrender(self.bot.store['quotes'][qindex - 1], qindex - 1, self.bot))
        except IndexError:
            await self.bot.reply('that quote doesn\'t exist!')

    @commands.command(aliases=['quotes', 'listquote', 'quoteslist', 'listquotes', 'dumpquotes', 'quotedump', 'quotesdump'])
    async def quotelist(self, *rshow_pages: int):
        """List all the quotes.
        Usage: quotelist"""
        # maybe PM this
        if not self.bot.store['quotes']:
            await self.bot.say('There are no quotes. Add some first!')
            return
        show_pages = [i for i in rshow_pages]
        pager = commands.Paginator(prefix='', suffix='', max_size=1595)
        if not show_pages:
            show_pages = (1,)
        for n, i in enumerate(self.bot.store['quotes']):
            qout = quote.qrender(i, n, self.bot)
            pager.add_line(qout)
        for page_n in show_pages:
            try:
                await self.bot.say('**__Listing page *{0}* of *{1}* of quotes.__**\n'.format(page_n, len(pager.pages)) + pager.pages[page_n - 1])
            except IndexError:
                await self.bot.say('**__Error: page *{0}* doesn\'t exist! There are *{1}* pages.__**'.format(page_n, len(pager.pages)))

    @commands.command(pass_context=True, aliases=['newquote', 'quotenew', 'addquote', 'makequote', 'quotemake', 'createquote', 'quotecreate', 'aq'])
    async def quoteadd(self, ctx, target: discord.User, *, text: str):
        """Add a quote.
        Usage: quoteadd [member] [text here]"""
        if len(text) > 360:
            await self.bot.reply('your text is too long!')
            return
        if target == self.bot.user:
            if not check_perms(ctx, ('bot_owner',)):
                await self.bot.reply('you can\'t add a quote as me!')
                return
        fmt_time = [int(i) for i in time.strftime("%m/%d/%Y").split('/')]
        q_template = {
            'id': 0,
            'quote': 'Say-whaaaa?',
            'author': ctx.message.author.display_name,
            'author_ids': [''],
            'date': fmt_time
        }
        mauthor = target
        q_template['quote'] = text.replace('\n', ' ').replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        q_template['author'] = mauthor.display_name
        if mauthor.display_name != mauthor.name:
            q_template['author'] += ' (' + mauthor.name + ')'
        q_template['author_ids'] = [mauthor.id, ctx.message.author.id]
        q_template['id'] = len(self.bot.store['quotes']) # +1 for next id, but len() counts from 1
        self.bot.store['quotes'].append(q_template)
        await self.bot.reply(f'you added quote **#{q_template["id"] + 1}**!')

    @commands.command(pass_context=True, aliases=['quoteedit', 'modquote', 'editquote'])
    async def quotemod(self, ctx, qindex: int, *, text: str):
        """Edit an existing quote.
        Usage: quotemod [quote number] [new text here]"""
        if len(text) > 360:
            await self.bot.reply('your text is too long!')
            return
        if qindex < 0:
            await self.bot.reply('there aren\'t negative quotes!')
            return
        try:
            q_template = self.bot.store['quotes'][qindex - 1]
        except IndexError:
            await self.bot.reply('that quote doesn\'t already exist!')
            return
        if not check_perms(ctx, ('bot_admin',)):
            if ctx.message.author.id not in q_template['author_ids']:
                await self.bot.reply('you need more permissions!')
                return
        q_template['quote'] = text.replace('\n', ' ').replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        self.bot.store['quotes'][qindex - 1] = q_template
        await self.bot.reply(f'you edited quote **#{qindex}**!')

    @commands.command(pass_context=True, aliases=['rmquote', 'quoterm', 'delquote'])
    async def quotedel(self, ctx, qindex: int):
        """Delete an existing quote.
        Usage: quotedel [quote number]"""
        if qindex < 0:
            await self.bot.reply('there aren\'t negative quotes!')
            return
        try:
            q_target = self.bot.store['quotes'][qindex - 1]
        except IndexError:
            await self.bot.reply(f'quote **#{qindex}** doesn\'t already exist!')
            return
        mauthor = ctx.message.author
        _pcheck = check_perms(ctx, ('bot_admin',))
        if (mauthor.id == q_target['author_ids'][0]) or (_pcheck):
            del self.bot.store['quotes'][qindex - 1]
            await self.bot.reply(f'you deleted quote **#{qindex}**!')
        else:
            await self.bot.reply(f'you can\'t delete quote **#{qindex}** because you didn\'t write it. Sorry!')

def setup(bot):
    c = Quotes(bot)
    bot.add_cog(c)
