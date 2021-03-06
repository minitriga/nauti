#      Copyright (C) 2020  Jeremy Schulman
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import wraps
from pkg_resources import iter_entry_points


from nauti.source import get_source
from nauti.collection import get_collection
from nauti.entrypoints import NAUTI_EP_TASKS
from nauti.tasks.diff_collection import diff_collections

from .registrar import _registered_plugins


__all__ = ["register_diff_task", "load_task_entrypoints", "get_diff_task"]

_PLUGIN_NAME = "diff_task"


def register_diff_task(origin, target, collection):
    def decorate(coro):
        @wraps(coro)
        async def wrapper(**options):
            src_col = get_collection(get_source(origin), collection)
            trg_col = get_collection(get_source(target), collection)

            async with src_col.source, trg_col.source:
                return await coro(src_col, trg_col, **options)

        key = (origin, target, collection)
        _registered_plugins[_PLUGIN_NAME][key] = wrapper
        return wrapper

    return decorate


async def default_diff_task(origin, target, **options):
    return await diff_collections(origin, target, **options)


def load_task_entrypoints():
    for ep in iter_entry_points(NAUTI_EP_TASKS):
        ep.load()


def get_diff_task(origin, target, collection):
    key = (origin, target, collection)

    if task := _registered_plugins[_PLUGIN_NAME].get(key) is not None:
        return task

    return register_diff_task(*key)(default_diff_task)
