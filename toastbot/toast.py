import discord.ext.commands as commands
import asyncio
import logging


class ToastBot(commands.Bot):
    def __init__(self, command_prefix, formatter=None, description=None, pm_help=False, **options):
        super().__init__(command_prefix, formatter, description, pm_help, ** options)

    @asyncio.coroutine
    def close(self, force_close=False):
        if force_close:
            for extension in tuple(self.extensions):
                try:
                    self.unload_extension(extension)
                except:
                    pass

            for cog in tuple(self.cogs):
                try:
                    self.remove_cog(cog)
                except:
                    pass

            yield from super().close()
        else:
            logging.warning('Connection closed; autorecovering...')
            self.run()
