"""The immutable sequence of records that every reader returns."""

from __future__ import annotations

import dataclasses
import functools
import os
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from enum import IntEnum
from typing import Any, ClassVar, NoReturn, cast, overload

from fm26save._core import export
from fm26save._core._frozen import FrozenMapping
from fm26save._core._status import computed_field_names
from fm26save._core.models.common import CodedValue

_NAME_FIELD = "name"
_UID_FIELD = "uid"
_ID_FIELD = "id"

# Each key field, with the wording its message needs, the other key field a record may carry
# instead, and the pair of methods that reads that other field.
_KEY_FIELDS = {
    _UID_FIELD: ("a 'uid' field", _ID_FIELD, "by_id or get_by_id"),
    _ID_FIELD: ("an 'id' field", _UID_FIELD, "by_uid or get_by_uid"),
}


def _normalized_name(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold().strip()


def _matches_wanted_value(record_value: object, wanted_value: object) -> bool:
    """Say whether a field's value answers to a value where passed.

    A coded-value field answers to a bare enum member when its label is that member, so a
    query names the label the save's code stands for. Everything else is plain equality.
    """
    if isinstance(wanted_value, IntEnum) and isinstance(record_value, CodedValue):
        coded_value = cast("CodedValue[IntEnum]", record_value)
        return coded_value.label is wanted_value
    return bool(record_value == wanted_value)


@functools.cache
def _coded_tuple_field_names(record_type: type) -> frozenset[str]:
    """Return the fields of a record type whose type hints say they hold coded values in a tuple.

    The names come from the hints alone, so a query is judged without reading a record. A
    record type whose fields export cannot plan has none of them, and its queries are matched
    by equality as they always were.
    """
    try:
        class_plan = export._class_plan(record_type)  # pyright: ignore[reportPrivateUsage]
    except (TypeError, ValueError):
        return frozenset()
    return frozenset(
        field_plan.name for field_plan in class_plan.fields if field_plan.kind == "coded_values"
    )


def _dataclass_field_names(candidate: object) -> tuple[str, ...] | None:
    """Return the field names of a dataclass type, computed fields last, or None when candidate
    is not one."""
    if not isinstance(candidate, type) or not dataclasses.is_dataclass(candidate):
        return None
    stored_names = tuple(record_field.name for record_field in dataclasses.fields(candidate))
    return stored_names + computed_field_names(candidate)


class Table[RecordT](Sequence[RecordT]):
    """An immutable sequence of records of one dataclass type, with queries and export.

    Indexing with an int returns a record and slicing returns a Table of the same record type.
    Queries return new tables and never change this one. Tables compare equal when they have
    the same record type and equal records, are not hashable, and can be pickled and
    deep-copied.
    """

    __slots__ = ("_coverage", "_id_index", "_record_type", "_records", "_uid_index")
    __hash__: ClassVar[None] = None  # pyright: ignore[reportIncompatibleMethodOverride]

    _records: tuple[RecordT, ...]
    _record_type: type[RecordT]
    _uid_index: dict[object, RecordT] | None
    _id_index: dict[object, RecordT] | None
    _coverage: FrozenMapping[str, float] | None

    def __init__(self, records: Iterable[RecordT], record_type: type[RecordT]) -> None:
        """Store the records as a tuple.

        Args:
            records: The records, all of record_type.
            record_type: The dataclass the records are instances of.

        Raises:
            TypeError: record_type is not a dataclass, or a record is not exactly of record_type
                (an instance of a subclass is rejected too).
        """
        if _dataclass_field_names(record_type) is None:
            raise TypeError(f"Table record_type must be a dataclass, not {record_type!r}")
        stored_records = tuple(records)
        stray_types = set(map(type, stored_records))
        stray_types.discard(record_type)
        if stray_types:
            stray_names = ", ".join(sorted(stray_type.__name__ for stray_type in stray_types))
            raise TypeError(f"Table expected {record_type.__name__} records, not {stray_names}")
        self._store(stored_records, record_type)

    def _store(self, records: tuple[RecordT, ...], record_type: type[RecordT]) -> None:
        object.__setattr__(self, "_records", records)
        object.__setattr__(self, "_record_type", record_type)
        object.__setattr__(self, "_uid_index", None)
        object.__setattr__(self, "_id_index", None)
        object.__setattr__(self, "_coverage", None)

    def _from_checked_records(self, records: tuple[RecordT, ...]) -> Table[RecordT]:
        """Build a table of this record type from records already checked by this table."""
        table = cast("Table[RecordT]", object.__new__(Table))
        table._store(records, self._record_type)
        return table

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError(f"Table is immutable: cannot set {name!r}")

    def __delattr__(self, name: str) -> NoReturn:
        raise AttributeError(f"Table is immutable: cannot delete {name!r}")

    def __reduce__(self) -> tuple[type[Table[RecordT]], tuple[tuple[RecordT, ...], type[RecordT]]]:
        # The key indexes and coverage are rebuilt on demand, so only the records are kept.
        return (Table, (self._records, self._record_type))

    @property
    def record_type(self) -> type[RecordT]:
        """The dataclass the records are instances of."""
        return self._record_type

    @overload
    def __getitem__(self, index: int) -> RecordT: ...

    @overload
    def __getitem__(self, index: slice) -> Table[RecordT]: ...

    def __getitem__(self, index: int | slice) -> RecordT | Table[RecordT]:
        if isinstance(index, slice):
            return self._from_checked_records(self._records[index])
        return self._records[index]

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[RecordT]:
        return iter(self._records)

    def __reversed__(self) -> Iterator[RecordT]:
        return reversed(self._records)

    def index(self, value: object, start: int = 0, stop: int | None = None) -> int:
        """Return the position of the first record equal to value between start and stop.

        A stop of None means the end of the table. Negative start and stop count from the end.

        Raises:
            ValueError: No such record.
        """
        return self._records.index(value, start, len(self._records) if stop is None else stop)

    def count(self, value: object) -> int:
        """Return how many records equal value."""
        return self._records.count(value)

    def __contains__(self, value: object) -> bool:
        return value in self._records

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Table):
            return NotImplemented
        other_table = cast("Table[object]", other)
        return (
            self._record_type is other_table._record_type and self._records == other_table._records
        )

    def __repr__(self) -> str:
        return f"Table[{self._record_type.__name__}]({len(self._records)} records)"

    def _field_names(self) -> tuple[str, ...]:
        return _dataclass_field_names(self._record_type) or ()

    def _require_field(self, field_name: str, method_name: str) -> None:
        if field_name not in self._field_names():
            raise ValueError(
                f"{method_name} needs a {field_name!r} field, and "
                f"{self._record_type.__name__} has none"
            )

    def where(self, **equals: object) -> Table[RecordT]:
        """Return the records whose named top-level fields all equal the given values.

        Nested group columns such as "contract_wage" are not field names; use filter for them.

        A coded-value field holds a CodedValue, which carries the number the save stores and
        the label fmsave reads it as. Passing a whole CodedValue matches the records whose
        label and raw number both equal it. Passing the label alone, as in
        where(cause=InjuryCause.IN_MATCH), matches every record carrying that label whatever
        its raw number, so where(cause=InjuryCause.UNKNOWN) is how you ask for the records
        whose code fmsave does not recognise. A label of another enum never matches. A field
        holding a tuple of coded values, such as a player's traits, matches only an equal whole
        tuple, and a label passed to one raises rather than coming back empty, because no tuple
        can equal a label; the message names the filter that looks inside the tuple.

        Raises:
            TypeError: A field holding a tuple of coded values was given a bare label.
            ValueError: A name is not a field of the record type. The message lists every such
                name and the valid field names.
        """
        field_names = self._field_names()
        unknown_names = [name for name in equals if name not in field_names]
        if unknown_names:
            raise ValueError(
                f"unknown {self._record_type.__name__} fields: {', '.join(unknown_names)}; "
                f"valid fields: {', '.join(field_names)}"
            )
        self._check_coded_tuple_labels(equals)
        wanted_values = tuple(equals.items())
        return self.filter(
            lambda record: all(
                _matches_wanted_value(getattr(record, field_name), wanted_value)
                for field_name, wanted_value in wanted_values
            )
        )

    def _check_coded_tuple_labels(self, equals: Mapping[str, object]) -> None:
        """Refuse a bare label passed to a field that holds a tuple of coded values.

        The field's type hints say a tuple can never equal a label, so the query could not
        have matched whatever the records hold, and no record is read to know it.

        Raises:
            TypeError: Such a field was given a bare label.
        """
        labelled_names = [
            field_name for field_name, wanted in equals.items() if isinstance(wanted, IntEnum)
        ]
        if not labelled_names:
            return
        tuple_field_names = _coded_tuple_field_names(self._record_type)
        for field_name in labelled_names:
            if field_name in tuple_field_names:
                wanted_label = cast("IntEnum", equals[field_name])
                label_type_name = type(wanted_label).__name__
                raise TypeError(
                    f"{self._record_type.__name__}.{field_name} holds a tuple of coded values, "
                    f"which no {label_type_name} member can equal; use filter, as in "
                    f"filter(lambda record: any(coded.label is "
                    f"{label_type_name}.{wanted_label.name} for coded in record.{field_name}))"
                )

    def filter(self, predicate: Callable[[RecordT], bool]) -> Table[RecordT]:
        """Return the records for which predicate returns true, in order."""
        return self._from_checked_records(
            tuple(record for record in self._records if predicate(record))
        )

    def sorted_by(self, key: Callable[[RecordT], Any], *, reverse: bool = False) -> Table[RecordT]:
        """Return the records ordered by key, smallest first, or largest first when reverse.

        key is called once per record and its values are compared to each other, so they must
        be comparable: sorted_by(lambda player: player.ability.current) orders by current
        ability, and a key returning None for some records raises TypeError. Records with
        equal keys keep the order they have here.

        Raises:
            TypeError: Two key values cannot be compared to each other.
        """
        return self._from_checked_records(tuple(sorted(self._records, key=key, reverse=reverse)))

    def find(self, *, name: str) -> Table[RecordT]:
        """Return the records whose name equals name, ignoring case and surrounding whitespace.

        Both names are compared after NFKC normalization and casefolding, so "NORTHBRIDGE FC"
        finds "Northbridge FC". The whole name must match: "northbridge" does not. Records
        whose name is None never match.

        Raises:
            ValueError: The record type has no name field.
        """
        self._require_field(_NAME_FIELD, "find")
        wanted_name = _normalized_name(name)

        def has_wanted_name(record: RecordT) -> bool:
            record_name: object = getattr(record, _NAME_FIELD)
            return isinstance(record_name, str) and _normalized_name(record_name) == wanted_name

        return self.filter(has_wanted_name)

    def _require_key_field(self, field_name: str) -> None:
        """Check that the record type has this key field, and name the other pair when it does not.

        Raises:
            ValueError: The record type has no such field. The message points at the other
                pair of lookups when the record type carries the key they read.
        """
        wanted_text, other_field, other_methods = _KEY_FIELDS[field_name]
        field_names = self._field_names()
        if field_name in field_names:
            return
        message = (
            f"{field_name} lookup needs {wanted_text}, and {self._record_type.__name__} has none"
        )
        if other_field in field_names:
            message += f"; it keys on {other_field!r}, so use {other_methods}"
        raise ValueError(message)

    def _build_key_index(self, field_name: str) -> dict[object, RecordT]:
        self._require_key_field(field_name)
        # Walk backwards so the first record with a repeated key is the one kept.
        return {getattr(record, field_name): record for record in reversed(self._records)}

    def _uid_lookup(self) -> dict[object, RecordT]:
        uid_index = self._uid_index
        if uid_index is None:
            uid_index = self._build_key_index(_UID_FIELD)
            object.__setattr__(self, "_uid_index", uid_index)
        return uid_index

    def _id_lookup(self) -> dict[object, RecordT]:
        id_index = self._id_index
        if id_index is None:
            id_index = self._build_key_index(_ID_FIELD)
            object.__setattr__(self, "_id_index", id_index)
        return id_index

    def by_uid(self, uid: int) -> RecordT:
        """Return the first record with this uid.

        Tables of people, clubs and grounds key on uid; the rest key on id, and say so.

        Raises:
            KeyError: No record has this uid.
            ValueError: The record type has no uid field. The message names by_id and
                get_by_id when the record type keys on id.
        """
        uid_index = self._uid_lookup()
        if uid not in uid_index:
            raise KeyError(f"no record with uid {uid}")
        return uid_index[uid]

    def get_by_uid(self, uid: int) -> RecordT | None:
        """Return the first record with this uid, or None when no record has it.

        Raises:
            ValueError: The record type has no uid field. The message names by_id and
                get_by_id when the record type keys on id.
        """
        return self._uid_lookup().get(uid)

    def by_id(self, id: int) -> RecordT:
        """Return the first record with this id.

        Competitions, stages and injury types key on id; tables of people, clubs and grounds
        key on uid instead, and say so.

        Raises:
            KeyError: No record has this id.
            ValueError: The record type has no id field. The message names by_uid and
                get_by_uid when the record type keys on uid.
        """
        id_index = self._id_lookup()
        if id not in id_index:
            raise KeyError(f"no record with id {id}")
        return id_index[id]

    def get_by_id(self, id: int) -> RecordT | None:
        """Return the first record with this id, or None when no record has it.

        Raises:
            ValueError: The record type has no id field. The message names by_uid and
                get_by_uid when the record type keys on uid.
        """
        return self._id_lookup().get(id)

    @property
    def coverage(self) -> Mapping[str, float]:
        """The share of records whose value is not None, for each flat column.

        Keys are export.column_names(record_type). An empty tuple counts as present, and every
        column of a missing group counts as missing. An empty table gives 0.0 for every column.
        """
        coverage = self._coverage
        if coverage is None:
            record_count = len(self._records)
            present_counts = export._present_counts(  # pyright: ignore[reportPrivateUsage]
                self._records, self._record_type, operation_name="coverage"
            )
            coverage = FrozenMapping(
                {
                    column_name: present_count / record_count if record_count else 0.0
                    for column_name, present_count in present_counts.items()
                }
            )
            object.__setattr__(self, "_coverage", coverage)
        return coverage

    def to_columns(self) -> dict[str, list[object]]:
        """Return flat columns of Python values; see export.to_columns."""
        return export.to_columns(self._records, self._record_type)

    def to_dicts(self, *, json_ready: bool = False) -> list[dict[str, object]]:
        """Return one nested dict per record; see export.record_to_dict."""
        return [export.record_to_dict(record, json_ready=json_ready) for record in self._records]

    def to_pandas(self) -> Any:
        """Return a pandas.DataFrame of the flat columns; see export.to_pandas.

        Raises:
            ImportError: pandas is not installed.
        """
        return export.to_pandas(self.to_columns())

    def to_polars(self) -> Any:
        """Return a polars.DataFrame of the flat columns; see export.to_polars.

        Raises:
            ImportError: polars is not installed.
        """
        return export.to_polars(self.to_columns())

    def write_csv(self, path: str | os.PathLike[str]) -> None:
        """Write every flat column as UTF-8 CSV; see export.write_csv for how cells are written."""
        export._write_records_csv(  # pyright: ignore[reportPrivateUsage]
            self._records, self._record_type, path, operation_name="write_csv"
        )

    def write_json(self, path: str | os.PathLike[str]) -> None:
        """Write the JSON-ready nested dicts as one JSON array; see export.write_json."""
        export.write_json(self._json_rows(), path)

    def write_jsonl(self, path: str | os.PathLike[str]) -> None:
        """Write the JSON-ready nested dicts as JSON Lines; see export.write_jsonl."""
        export.write_jsonl(self._json_rows(), path)

    def _json_rows(self) -> Iterator[dict[str, object]]:
        return (export.record_to_dict(record, json_ready=True) for record in self._records)
