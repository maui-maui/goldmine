'Extended context.'
import asyncio
from discord import File
from discord.ext.commands import Context
from discord.errors import InvalidArgument

class ExtContext(Context):
    """Custom extended context for commands."""
    def __init__(self, *args, **kwargs):
        Context.__init__(self, *args, **kwargs)
        self.mention = self.author.mention

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, reason=None, delete_after=None, filter=True):
        """Sends a message to the destination with the content given."""
        channel = await self._get_channel()
        state = self._state
        if content:
            content = str(content)
            if filter:
                if not self.bot.selfbot:
                    content = content.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            if len(content) > 2000:
                truncate_msg = '**... (truncated)**'
                if '```' in content:
                    truncate_msg = '```' + truncate_msg
                content = content[:2000 - len(truncate_msg)] + truncate_msg
            elif len(content) <= 1999:
                if self.bot.selfbot:
                    if filter:
                        content += '\u200b'

        if embed is not None:
            embed = embed.to_dict()

        if file is not None and files is not None:
            raise InvalidArgument('cannot pass both file and files parameter to send()')

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument('file parameter must be File')

            try:
                data = await state.http.send_files(channel.id, files=[(file.open_file(), file.filename)],
                                                        content=content, tts=tts, embed=embed)
            finally:
                file.close()

        elif files is not None:
            if len(files) < 2 or len(files) > 10:
                raise InvalidArgument('files parameter must be a list of 2 to 10 elements')

            try:
                param = [(f.open_file(), f.filename) for f in files]
                data = await state.http.send_files(channel.id, files=param, content=content, tts=tts, embed=embed)
            finally:
                for f in files:
                    f.close()
        else:
            data = await state.http.send_message(channel.id, content, tts=tts, embed=embed)

        ret = state.create_message(channel=channel, data=data)
        if delete_after is not None:
            async def delete():
                await asyncio.sleep(delete_after, loop=state.loop)
                try:
                    await ret.delete(reason=reason)
                except:
                    pass
            state.loop.create_task(delete())
        return ret
