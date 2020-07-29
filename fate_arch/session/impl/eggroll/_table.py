#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#


import typing

from eggroll.roll_pair.roll_pair import RollPair
from fate_arch.common.profile import log_elapsed
from fate_arch.data_table.base import AddressABC, EggRollAddress
from fate_arch.session._interface import TableABC


class Table(TableABC):

    def __init__(self, rp: RollPair):
        self._rp = rp

    def _as_federation_format(self):
        return self._rp

    @log_elapsed
    def save(self, address: AddressABC, partitions: int, schema: dict, **kwargs):
        options = kwargs.get("options", {})
        if isinstance(address, EggRollAddress):
            self._rp.save_as(name=address.name, namespace=address.namespace, partition=partitions, options=options)
            schema.update(self.schema)
            return
        raise NotImplementedError(f"address type {type(address)} not supported with eggroll backend")

    @log_elapsed
    def collect(self, **kwargs) -> list:
        return self._rp.get_all()

    @log_elapsed
    def count(self, **kwargs) -> int:
        return self._rp.count()

    def take(self, n=1, **kwargs):
        options = dict(keys_only=False)
        return self._rp.take(n=n, options=options)

    def first(self):
        options = dict(keys_only=False)
        return self._rp.first(options=options)

    @log_elapsed
    def map(self, func, **kwargs):
        return Table(self._rp.map(func))

    @log_elapsed
    def mapValues(self, func: typing.Callable[[typing.Any], typing.Any], **kwargs):
        return Table(self._rp.map_values(func))

    @log_elapsed
    def mapPartitions(self, func, **kwargs):
        return Table(self._rp.collapse_partitions(func))

    def mapPartitions2(self, func, **kwargs):
        return Table(self._rp.map_partitions(func))

    @log_elapsed
    def reduce(self, func, key_func=None, **kwargs):
        if key_func is None:
            return self._rp.reduce(func)

        it = self._rp.get_all()
        ret = {}
        for k, v in it:
            agg_key = key_func(k)
            if agg_key in ret:
                ret[agg_key] = func(ret[agg_key], v)
            else:
                ret[agg_key] = v
        return ret

    @log_elapsed
    def join(self, other: 'Table', func, **kwargs):
        return Table(self._rp.join(other._rp, func=func))

    @log_elapsed
    def glom(self, **kwargs):
        return Table(self._rp.glom())

    @log_elapsed
    def sample(self, fraction, seed=None, **kwargs):
        return Table(self._rp.sample(fraction=fraction, seed=seed))

    @log_elapsed
    def subtractByKey(self, other: 'Table', **kwargs):
        return Table(self._rp.subtract_by_key(other._rp))

    @log_elapsed
    def filter(self, func, **kwargs):
        return Table(self._rp.filter(func))

    @log_elapsed
    def union(self, other: 'Table', func=lambda v1, v2: v1, **kwargs):
        return Table(self._rp.union(other._rp, func=func))

    @log_elapsed
    def flatMap(self, func, **kwargs):
        flat_map = self._rp.flat_map(func)
        shuffled = flat_map.map(lambda k, v: (k, v))  # trigger shuffle
        return Table(shuffled)