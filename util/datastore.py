"""Functions for handling the Data Store."""
import asyncio
import os
import sys
import util.json as json
import util.dynaimport as di
from discord.ext.commands import CommandInvokeError
from properties import storage_backend
bson = di.load('bson')

class DataStore():
    """The data store central."""
    exts = {
        'json': 'json',
        'leveldb': 'ldb',
        'pickle': 'db',
        'bson': 'bson'
    }
    def __init__(self, backend, path=None, join_path=True, commit_interval=3):
        self.dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].core_file))
        self.backend = backend
        self.session = None
        self.commit_interval = commit_interval
        self.path = ''
        if path:
            if join_path:
                self.path = os.path.join(self.dir, path)
            else:
                self.path = path
        else:
            self.path = os.path.join(self.dir, 'storage.' + self.exts[storage_backend])
        self.store = {}
        if self.backend == 'json':
            try:
                with open(self.path, 'r') as storefile:
                    self.store = json.loads(storefile.read())
            except FileNotFoundError:
                print('Creating storage file...')
                with open(self.path, 'a') as f, open(os.path.join(self.dir, 'assets', 'emp_storage.json')) as df:
                    orig = df.read()
                    f.write(orig)
                self.store = json.loads(orig)
        elif self.backend == 'bson':
            try:
                with open(self.path, 'rb') as storefile:
                    self.store = bson.loads(storefile.read())
            except FileNotFoundError:
                print('Creating storage file...')
                with open(self.path, 'ab') as f, open(os.path.join(self.dir, 'assets', 'emp_storage.json')) as df:
                    orig = df.read()
                    f.write(bson.dumps(orig))
                self.store = json.loads(orig)

    def __getitem__(self, item: str):
        return self.store[item]

    def __setitem__(self, key, item):
        self.store[key] = item

    def __len__(self):
        return len(self.store)

    def __contains__(self, item):
        return item in self.store

    def __iter__(self):
        return iter(self.store)

    def keys(self):
        return self.store.keys()
    def values(self):
        return self.store.values()
    def get(self, *args):
        return self.store.get(*args)

    async def read(self):
        """Re-read the datastore from disk, discarding changes."""
        if self.backend == 'json':
            with open(self.path, 'r') as storefile:
                self.store = json.loads(storefile.read())
        elif self.backend == 'bson':
            with open(self.path, 'rb') as storefile:
                self.store = bson.loads(storefile.read())

    async def commit(self):
        """Commit the current datastore to disk."""
        if self.backend == 'json':
            with open(self.path, 'w+') as storefile:
                storefile.write(json.dumps(self.store))
        elif self.backend == 'bson':
            with open(self.path, 'wb+') as storefile:
                storefile.write(bson.dumps(self.store))

    async def commit_task(self):
        """Continous background task for comitting datastore."""
        while True:
            await asyncio.sleep(self.commit_interval * 60)
            await self.commit()

    def get_cmdfix(self, msg):
        """Easy method to retrieve the command prefix."""
        if msg.guild is None:
            return self.store['properties']['global']['command_prefix']
        try:
            return self.store['properties']['by_guild'][msg.guild.id]['command_prefix']
        except KeyError:
            return self.store['properties']['global']['command_prefix']

    def get_props_s(self, msg):
        """Get the guild properties of a message."""
        try:
            return self.store['properties']['by_guild'][msg.guild.id]
        except KeyError:
            self.store['properties']['by_guild'][msg.guild.id] = {
                'name': msg.guild.name,
                'orig_members': len(msg.guild.members)
            }
            return {}

    def get_props_u(self, msg):
        """Get the user properties of a message."""
        try:
            return self.store['properties']['by_user'][msg.author.id]
        except KeyError:
            return {}

    def set_prop(self, msg, scope: str, prop: str, content):
        try:
            t_scope = self.store['properties'][scope]
        except (KeyError, AttributeError):
            raise AttributeError('Invalid scope specified. Valid scopes are by_user, by_guild, and global.')
        else:
            if scope == 'by_user':
                t_scope[msg.author.id][prop] = content
            elif scope == 'by_guild':
                t_scope[msg.guild.id][prop] = content
            elif scope == 'global':
                t_scope[prop] = content
            else:
                raise AttributeError('Invalid scope specified. Valid scopes are by_user, by_guild, and global.')
            self.store['properties'][scope] = t_scope

    def get_prop(self, msg, prop: str, hint=[]):
        """Get the final property referenced in msg's scope."""
        try: # User
            return self.get_props_u(msg)[prop]
        except (KeyError, AttributeError):
            try: # guild
                return self.get_props_s(msg)[prop]
            except (KeyError, AttributeError):
                try:
                    return self.store['properties']['global'][prop]
                except KeyError as e:
                    if prop.startswith('profile_'):
                        thing = self.store['properties']['global']['profile'].copy()
                        if msg.author.id not in self.store['properties']['by_user']:
                            self.store['properties']['by_user'][msg.author.id] = {}
                        self.store['properties']['by_user'][msg.author.id]['profile_' + str(msg.guild.id)] = thing
                        return thing
                    else:
                        raise e
