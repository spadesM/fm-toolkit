"""A read-only mapping for public records."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Self


class FrozenMapping[KeyT, ValueT](Mapping[KeyT, ValueT]):
    """An immutable mapping that holds its own copy of the items.

    Unlike types.MappingProxyType it can be pickled and deep-copied, so records holding one
    can be too. It compares equal to any mapping with the same items and is not hashable.
    The items are copied when the instance is created, so calling __init__ again changes nothing.
    """

    __slots__ = ("_items",)
    __hash__ = None

    _items: dict[KeyT, ValueT]

    def __new__(cls, items: Mapping[KeyT, ValueT]) -> Self:
        instance = super().__new__(cls)
        instance._items = dict(items)
        return instance

    def __init__(self, items: Mapping[KeyT, ValueT]) -> None:
        """Leave the instance as built: the items were already copied when it was created."""

    def __getitem__(self, key: KeyT) -> ValueT:
        return self._items[key]

    def __iter__(self) -> Iterator[KeyT]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return repr(self._items)

    def __reduce__(self) -> tuple[type[FrozenMapping[KeyT, ValueT]], tuple[dict[KeyT, ValueT]]]:
        return (FrozenMapping, (dict(self),))
