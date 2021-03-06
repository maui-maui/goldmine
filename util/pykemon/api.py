#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pykemon.api
User interaction with this package is done through this file."""

from .request import endpoints
from .request import make_request

async def get(**kwargs):
    """Make a request to PokeAPI and return the requested resource.
    Resource choices:

    pokedex_id
    pokemon
    pokemon_id
    move_id
    ability_id
    type_id
    egg_id
    description_id
    sprite_id
    game_id"""
    if len(kwargs.keys()) > 1:
        raise ValueError('Too many arguments. Only pass 1 argument')

    if list(kwargs.keys())[0] in endpoints:
        return await make_request(kwargs)

    else:
        raise ValueError('An invalid argument was passed')
