"""The bot's Cozmo module. Only works with Cozmo!"""
import asyncio
import functools
from discord.ext import commands
import util.dynaimport as di
cozmo = di.load('cozmo')
from .cog import Cog

class Cozmo(Cog):
    """Some commands to interface with Cozmo robots.
    You probably don't want this in the open.
    """

    def __init__(self, bot):
        self.sdk_conn = None
        self.robot = None
        try:
            self.default_connector = cozmo.run.FirstAvailableConnector()
        except ImportError:
            self.default_connector = None
        super().__init__(bot)

    async def check_conn(self, ctx):
        """Check the connection to Cozmo."""
        if not self.robot:
#            raise commands.ReturnError('{0.message.author.mention} **Not connected to Cozmo!**', ctx)
            await ctx.send('Not connected to Cozmo!')
            raise commands.PassException()

    @commands.command()
    async def cspeak(self, ctx, *, text: str):
        """Make Cozmo speak something.
        Usage: cspeak [stuff to say]"""
        await self.check_conn(ctx)
        status = await ctx.send('Talking...')
        c_voice = '[VOICE:N]' not in text
        self.robot.say_text(text.replace('[VOICE:N]', '')[:255], use_cozmo_voice=c_voice, duration_scalar=0.9)

    @commands.command()
    async def cdrive(self, ctx, drive_time: float):
        """Make Cozmo drive for n seconds.
        Usage: cdrive [seconds to drive]"""
        await self.check_conn(ctx)
        status = await ctx.send('Driving...')
        await self.robot.drive_wheels(50, 50, 50, 50, duration=drive_time)
        await status.edit(content='Finished driving!')

    @commands.command(aliases=['cinit'])
    async def cinitialize(self, ctx):
        """Connect to Cozmo.
        Usage: cinit"""
        try:
            self.sdk_conn = await self.cozmo_connect(self.loop)
        except cozmo.ConnectionError as e:
            await ctx.send("A connection error occurred: %s" % e)
            return False
        self.robot = await self.sdk_conn.wait_for_robot()
        await ctx.send('Connected to robot!')

    async def cozmo_connect(self, loop, conn_factory=None, connector=None):
        '''Uses the supplied event loop to connect to a device.
        Returns:
            A :class:`cozmo.conn.CozmoConnection` instance.
        '''
        conn = cozmo.conn
        if conn_factory is None:
            conn_factory = conn.CozmoConnection
        if connector is None:
            connector = self.default_connector

        factory = functools.partial(conn_factory, loop=loop)
        async def conn_check(coz_conn):
            await coz_conn.wait_for(conn.EvtConnected, timeout=5)
        async def connect():
            return await connector.connect(loop, factory, conn_check)

        transport, coz_conn = await connect()
        return coz_conn

def setup(bot):
    c = Cozmo(bot)
    bot.add_cog(c)
