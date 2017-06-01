"""The brains of Dragon5232's awesome Discord bot.'"""
from __future__ import unicode_literals
import logging
import asyncio
import os
import sys
import shutil
import traceback
from fnmatch import filter
import discord
from default_cogs.utils.dataIO import dataIO
import __main__
__main__.core_file = __file__
from util.token import bot_token, is_bot
from convert_to_old_syntax import rc_files, cur_dir
from util.goldbot import GoldBot
from util.const import description, default_cogs
from util.proformatter import RichFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

if not discord.opus.is_loaded():
    # Windows: opus.dll (auto provided)
    # Linux: CWD/libopus.so
    # Mac: CWD/libopus.dylib
    try:
        discord.opus.load_opus('opus')
    except OSError:
        try:
            discord.opus.load_opus('libopus')
        except OSError:
            logger.warning('could not load libopus, voice will NOT be available.')

def login_fail_loop(loop, bot):
    """Handler if I couldn't login to Discord."""
    global bot_token
    global selfbot
    print('Should I: [E]xit / [Q]uit, [R]etry, or run [S]etup again?')
    r = input('> ').lower()[0]
    if r in ['e', 'q']:
        print('Ok, I\'ll exit. Bye!')
        exit(0)
    elif r == 'r':
        print('Ok, I\'ll try logging in again.')
        runbot(loop, bot)
        return
    elif r == 's':
        print('Ok, here\'s to re-running setup!')
        try:
            os.remove(os.path.join(cur_dir, 'bot_token.txt'))
        except OSError:
            print('Hmm, I couldn\'t delete the token file. Try another choice.')
            login_fail_loop(loop, bot)
        else:
            try:
                del sys.modules['util.token']
            except (KeyError, ValueError):
                pass
            try:
                del sys.modules['goldmine.util.token']
            except (KeyError, ValueError):
                pass
            del bot_token
            del selfbot
            from util.token import bot_token
    else:
        print('That\'s not a valid choice, try again!')
        login_fail_loop(loop, bot)
        return

def runbot(loop, bot):
    """Start the bot and handle Ctrl-C."""
    try:
        try:
            loop.run_until_complete(bot.start(*bot_token, bot=is_bot))
            bot.cog_http.close()
        except discord.errors.LoginFailure:
            print('''Hmm... I\'m having trouble logging into Discord.
This usually means you revoked your token, or gave an invalid token.''')
            login_fail_loop(loop, bot)
            return
    except KeyboardInterrupt:
        logger.info('The bot is now shutting down, please wait...')
        loop.run_until_complete(bot.logout())

def set_cog(cog, value):  # TODO: move this out of core.py
    data = dataIO.load_json("data/cogs.json")
    data[cog] = value
    dataIO.save_json("data/cogs.json", data)

def init_bot():
    """Initialize the bot."""
    bot = GoldBot(command_prefix='', description='', formatter=RichFormatter(), pm_help=None)
    __main__.send_cmd_help = bot.send_cmd_help
    logger.info('Init: Loading cogs')
    try:
        with open('disabled_cogs.txt', 'r') as f:
            disabled_cogs = [i.rstrip() for i in f.readlines()]
    except FileNotFoundError:
        disabled_cogs = []
    for cog in default_cogs:
        if cog not in disabled_cogs:
            logger.info('Init: Loading cog: ' + cog)
            try:
                bot.load_extension('default_cogs.' + cog)
            except Exception as e:
                logger.error('Error loading cog %s.' % cog)
                logger.error('Traceback (most recent call last):\n' + ''.join(traceback.format_tb(e.__traceback__)) \
                        + type(e).__name__ + ': ' + str(e))
    if not os.path.exists(os.path.join(cur_dir, 'cogs', 'utils')):
        shutil.copytree(os.path.join(cur_dir, 'default_cogs', 'utils'), os.path.join(cur_dir, 'cogs', 'utils') + os.path.sep)
    logger.info('Init: Loading extra cogs')
    try:
        with open('cogs.txt', 'r') as f:
            for cog in [i.rstrip().replace(' ', '_') for i in f.readlines()]:
                if cog: # for empty newlines
                    logger.info('Init: Loading extra cog: ' + cog)
                    try:
                        bot.load_extension('default_cogs.' + cog)
                    except ImportError:
                        try:
                            bot.load_extension('cogs.' + cog)
                        except ImportError:
                            logger.error('Could not load extra cog %s!', cog)
                            exit(1)
                    except Exception as e:
                        logger.error('Error loading extra cog %s.' % cog)
                        logger.error('Traceback (most recent call last):\n' + ''.join(traceback.format_tb(e.__traceback__)) \
                              + type(e).__name__ + ': ' + str(e))
    except FileNotFoundError:
        pass
    return bot
def main(use_uvloop):
    """Executes the main bot."""
    if use_uvloop:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    bot = init_bot()
    logger.info('Init: Initializing event loop')
    loop = asyncio.get_event_loop()
    logger.info('Init: Starting bot!')
    runbot(loop, bot)
    return bot.is_restart

if __name__ == '__main__':
    use_uvloop = False
    logger.info('Init: Detecting uvloop...')
    try:
        import uvloop
    except ImportError:
        logger.info('Init: Could not load uvloop')
    else:
        logger.info('Init: Will use uvloop.')
        use_uvloop = True
    main(use_uvloop)
