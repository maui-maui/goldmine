"""Extended version of the Help Formatter component."""
import itertools
import inspect

from discord.ext.commands.formatter import HelpFormatter, Paginator
from discord.ext.commands.core import Command

class RichFormatter(HelpFormatter):
    def _add_subcommands_to_page(self, max_width, commands):
        for name, command in commands:
            if name in command.aliases:
                # skip aliases
                continue

            entry = '  \u2022  **{0}**: *{1}'.format(name, (command.short_doc if command.short_doc else 'I\'m a command.'))
            shortened = self.shorten(entry) + '*'
            self._paginator.add_line(shortened)

    def format(self):
        """Handles the actual behavior involved with formatting.
        To change the behavior, this method should be overridden.
        Returns
        --------
        list
            A paginated output of the help command.
        """
        self._paginator = Paginator(prefix='', suffix='')

        # we need a padding of ~80 or so
        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):
            # <signature portion>
            signature = self.get_command_signature()
            self._paginator.add_line('```' + signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help + '```')

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return '**__' + cog + '__**:' if cog is not None else '\u200b**__No Category:__**'

        if self.is_bot():
            data = sorted(self.filter_command_list(), key=category)
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                commands = list(commands)
                if len(commands) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, commands)
        else:
            self._paginator.add_line('**__Commands__**:')
            self._add_subcommands_to_page(max_width, self.filter_command_list())

        # add the ending note
        self._paginator.add_line()
        ending_note = self.get_ending_note()
        self._paginator.add_line(ending_note)
        return self._paginator.pages
