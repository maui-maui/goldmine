"""Self monitor."""
import util.commands as commands
from .cog import Cog

class Monitor(Cog):
    """The self error monitor cog."""
    def __init__(self, bot):
        super().__init__(bot)
        self.error_data = {}

def setup(bot):
    bot.add_cog(Monitor(bot))
