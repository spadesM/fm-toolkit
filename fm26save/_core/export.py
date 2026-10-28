"""Flatten records into columns and write them as CSV, JSON, JSON Lines or DataFrames.

A record becomes a nested dict with record_to_dict and a flat row with flatten_dict. Nested
groups flatten to "<field>_<subfield>" columns, the same names pandas.json_normalize(sep="_")
gives for record_to_dict(record, json_ready=True). A coded value, or a tuple of coded values,
becomes a label column plus a "<field>_code" column. Tuples stay single values: JSON arrays in
JSON, ";"-joined text in CSV, or compact JSON text in CSV when their items are groups.

A field holding a mapping whose keys the record type declares in UNKNOWN_KEYS, which the
`unknown` field of every record is, flattens to one "<field>_<key>" column per declared key. A
mapping whose keys are not declared, such as `SaveInfo.section_schemas`, stays one column
holding the mapping itself, since a key that differs from save to save cannot be a column name.

Only the names in __all__ are public.
"""

from __future__ import annotations

import csv
import dataclasses
import functools
import importlib
import itertools
import json
import operator
import os
import types
import typing
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import date, time
from enum import StrEnum
from typing import Any, Literal, TextIO, TypeGuard, cast

from fm26save._core._frozen import FrozenMapping
from fm26save._core._status import computed_field_names
from fm26save._core.models.common import CodedValue

__all__ = [
    "column_names",
    "flat_rows",
    "flatten_dict",
    "record_to_dict",
    "select_columns",
    "to_columns",
    "to_pandas",
    "to_polars",
    "write_csv",
    "write_json",
    "write_jsonl",
]

type _FieldKind = Literal[
    "value",
    "bool",
    "date",
    "text_enum",
    "coded",
    "group",
    "values",
    "coded_values",
    "records",
    "unknown",
    "mapping",
]
type _ScalarKind = Literal["value", "bool", "date", "text_enum"]
type _Step = _FieldRun | _FieldPlan

_UNKNOWN_FIELD_NAME = "unknown"
_CODE_SUFFIX = "_code"
_CSV_ITEM_SEPARATOR = ";"
_MISSING_PAIR: tuple[None, None] = (None, None)
_NONE_TYPE = type(None)
# The csv module writes cells of exactly these types the way _csv_cell would.
_CSV_NATIVE_TYPES: frozenset[type] = frozenset((str, int, _NONE_TYPE))
_STR_ONLY: frozenset[type] = frozenset((str,))
_INT_ONLY: frozenset[type] = frozenset((int,))
_is_present: Callable[[object], bool] = functools.partial(operator.is_not, None)
_read_label_text = operator.attrgetter("label_text")
_read_raw = operator.attrgetter("raw")


def _read_no_fields(record: object) -> tuple[object, ...]:
    return ()


@dataclasses.dataclass(frozen=True, slots=True)
class _FieldRun:
    """Consecutive fields whose values are copied as they are.

    Attributes:
        values: The slice of the record's field values that the run covers.
        names: The field names of the run, in order.
    """

    values: slice
    names: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class _ClassPlan:
    """How the fields of one record class turn into dict keys and flat columns.

    Attributes:
        record_type: The record class.
        fields: One plan per dataclass field, in declaration order.
        columns: The flat column names, in order.
        read_fields: Returns every field value of a record as a tuple, in declaration order.
        steps: Runs of plain, bool and date fields, and the plans of every other field, in
            declaration order. Used for flat values and for dicts that are not JSON-ready.
        json_steps: The same, but runs hold plain and bool fields only. Used for JSON-ready
            dicts.
        csv_steps: The same, but runs hold int and str fields only. Used for CSV cells.
        all_plain: Whether steps is at most one run, so the field values are the flat values.
        json_all_plain: The same for json_steps, so the field values are the JSON-ready flat
            values.
        csv_all_plain: The same for csv_steps, so the field values are the CSV cells.
        missing_columns: One None per column, for a missing group.
    """

    record_type: type
    fields: tuple[_FieldPlan, ...]
    columns: tuple[str, ...]
    read_fields: Callable[[object], tuple[object, ...]]
    steps: tuple[_Step, ...]
    json_steps: tuple[_Step, ...]
    csv_steps: tuple[_Step, ...]
    all_plain: bool
    json_all_plain: bool
    csv_all_plain: bool
    missing_columns: tuple[None, ...]


_NO_MEMBERS = _ClassPlan(object, (), (), _read_no_fields, (), (), (), True, True, True, ())


@dataclasses.dataclass(frozen=True, slots=True)
class _FieldPlan:
    """How one dataclass field turns into dict keys."""

    name: str
    kind: _FieldKind
    index: int
    qualified_name: str
    code_name: str = ""
    item_kind: _ScalarKind = "value"
    members: _ClassPlan = _NO_MEMBERS
    unknown_keys: tuple[str, ...] = ()
    unknown_key_set: frozenset[str] = frozenset()


def _is_record_class(candidate: object) -> TypeGuard[type]:
    return (
        isinstance(candidate, type)
        and dataclasses.is_dataclass(candidate)
        and candidate is not CodedValue
    )


def _is_coded_value_type(annotation: object) -> bool:
    return annotation is CodedValue or typing.get_origin(annotation) is CodedValue


def _without_none(annotation: object) -> object:
    if typing.get_origin(annotation) not in (typing.Union, types.UnionType):
        return annotation
    member_types = [
        member_type for member_type in typing.get_args(annotation) if member_type is not type(None)
    ]
    if len(member_types) != 1:
        return annotation
    return member_types[0]


def _scalar_kind(annotation: object) -> _ScalarKind | None:
    # A float flattens exactly as an int does: it is written as it is, and every format these
    # records reach (CSV, JSON, a DataFrame column) holds one natively.
    if annotation is int or annotation is str or annotation is float:
        return "value"
    if annotation is bool:
        return "bool"
    if annotation is date or annotation is time:
        # A time of day flattens the way a date does: kept as it is, or ISO 8601 when the
        # values are JSON-ready, so the two share one kind.
        return "date"
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return "text_enum"
    return None


def _unknown_keys(record_type: type) -> tuple[str, ...]:
    declared_keys: object = getattr(record_type, "UNKNOWN_KEYS", None)
    if isinstance(declared_keys, tuple):
        key_items = cast("tuple[object, ...]", declared_keys)
        key_names = tuple(key for key in key_items if isinstance(key, str))
        if len(key_names) == len(key_items):
            return key_names
    raise TypeError(
        f"{record_type.__name__} has an {_UNKNOWN_FIELD_NAME} field but no UNKNOWN_KEYS tuple "
        "of key names"
    )


def _plan_field(record_type: type, index: int, field_name: str, annotation: object) -> _FieldPlan:
    qualified_name = f"{record_type.__name__}.{field_name}"
    code_name = f"{field_name}{_CODE_SUFFIX}"
    field_type = _without_none(annotation)
    scalar_kind = _scalar_kind(field_type)
    if scalar_kind is not None:
        return _FieldPlan(field_name, scalar_kind, index, qualified_name)
    if _is_coded_value_type(field_type):
        return _FieldPlan(field_name, "coded", index, qualified_name, code_name=code_name)
    if _is_record_class(field_type):
        return _FieldPlan(
            field_name, "group", index, qualified_name, members=_class_plan(field_type)
        )
    origin = typing.get_origin(field_type)
    if origin is tuple:
        type_arguments = typing.get_args(field_type)
        if len(type_arguments) == 2 and type_arguments[1] is Ellipsis:
            item_type: object = type_arguments[0]
            item_kind = _scalar_kind(_without_none(item_type))
            if item_kind is not None:
                return _FieldPlan(field_name, "values", index, qualified_name, item_kind=item_kind)
            if _is_coded_value_type(item_type):
                return _FieldPlan(
                    field_name, "coded_values", index, qualified_name, code_name=code_name
                )
            if _is_record_class(item_type):
                return _FieldPlan(
                    field_name, "records", index, qualified_name, members=_class_plan(item_type)
                )
    if origin is Mapping and typing.get_args(field_type) == (str, int):
        if field_name != _UNKNOWN_FIELD_NAME:
            # A mapping whose keys the record type does not declare. Its keys come from the
            # save rather than from the class, so they cannot be columns: the field is one
            # column holding the mapping whole.
            return _FieldPlan(field_name, "mapping", index, qualified_name)
        unknown_keys = _unknown_keys(record_type)
        return _FieldPlan(
            field_name,
            "unknown",
            index,
            qualified_name,
            unknown_keys=unknown_keys,
            unknown_key_set=frozenset(unknown_keys),
        )
    raise TypeError(f"{qualified_name} has a type that export does not support: {annotation!r}")


def _nested_keys(field_plans: tuple[_FieldPlan, ...]) -> list[str]:
    keys: list[str] = []
    for field_plan in field_plans:
        keys.append(field_plan.name)
        if field_plan.code_name and field_plan.kind in ("coded", "coded_values"):
            keys.append(field_plan.code_name)
    return keys


def _flat_columns(field_plans: tuple[_FieldPlan, ...]) -> list[str]:
    columns: list[str] = []
    for field_plan in field_plans:
        match field_plan.kind:
            case "coded" | "coded_values":
                columns.extend((field_plan.name, field_plan.code_name))
            case "group":
                columns.extend(
                    f"{field_plan.name}_{member_column}"
                    for member_column in field_plan.members.columns
                )
            case "unknown":
                columns.extend(f"{field_plan.name}_{key}" for key in field_plan.unknown_keys)
            case "value" | "bool" | "date" | "text_enum" | "values" | "records" | "mapping":
                columns.append(field_plan.name)
    return columns


_FLAT_RUN_KINDS: frozenset[_FieldKind] = frozenset(("value", "bool", "date"))
_JSON_RUN_KINDS: frozenset[_FieldKind] = frozenset(("value", "bool"))
_CSV_RUN_KINDS: frozenset[_FieldKind] = frozenset(("value",))


def _steps(
    field_plans: tuple[_FieldPlan, ...], run_kinds: frozenset[_FieldKind]
) -> tuple[_Step, ...]:
    """Merge each stretch of consecutive fields whose kind is in run_kinds into one run."""
    steps: list[_Step] = []
    run_plans: list[_FieldPlan] = []
    for field_plan in (*field_plans, None):
        if field_plan is not None and field_plan.kind in run_kinds:
            run_plans.append(field_plan)
            continue
        if run_plans:
            run_values = slice(run_plans[0].index, run_plans[-1].index + 1)
            steps.append(_FieldRun(run_values, tuple(run_plan.name for run_plan in run_plans)))
            run_plans = []
        if field_plan is not None:
            steps.append(field_plan)
    return tuple(steps)


def _field_reader(field_names: tuple[str, ...]) -> Callable[[object], tuple[object, ...]]:
    if not field_names:
        return _read_no_fields
    if len(field_names) == 1:
        only_field_name = field_names[0]
        return lambda record: (getattr(record, only_field_name),)
    return operator.attrgetter(*field_names)


def _first_duplicate(names: Iterable[str]) -> str | None:
    seen_names: set[str] = set()
    for name in names:
        if name in seen_names:
            return name
        seen_names.add(name)
    return None


@functools.cache
def _class_plan(record_type: type) -> _ClassPlan:
    type_name = record_type.__name__
    if not dataclasses.is_dataclass(record_type) or record_type is CodedValue:
        raise TypeError(f"{type_name} is not a record dataclass")
    type_parameters: dict[str, object] = {
        type_parameter.__name__: type_parameter
        for type_parameter in getattr(record_type, "__type_params__", ())
    }
    field_types = typing.get_type_hints(record_type, localns=type_parameters)
    field_names = tuple(record_field.name for record_field in dataclasses.fields(record_type))
    # Computed fields follow the stored ones, typed by what their property returns.
    for computed_name in computed_field_names(record_type):
        getter = cast("property", getattr(record_type, computed_name)).fget
        field_types[computed_name] = typing.get_type_hints(getter)["return"]
        field_names += (computed_name,)
    field_plans = tuple(
        _plan_field(record_type, index, field_name, field_types[field_name])
        for index, field_name in enumerate(field_names)
    )
    columns = tuple(_flat_columns(field_plans))
    for names, name_role in ((_nested_keys(field_plans), "key"), (columns, "column")):
        duplicate_name = _first_duplicate(names)
        if duplicate_name is not None:
            raise ValueError(f"{type_name} has more than one {name_role} named {duplicate_name!r}")
    steps = _steps(field_plans, _FLAT_RUN_KINDS)
    json_steps = _steps(field_plans, _JSON_RUN_KINDS)
    csv_steps = _steps(field_plans, _CSV_RUN_KINDS)
    return _ClassPlan(
        record_type=record_type,
        fields=field_plans,
        columns=columns,
        read_fields=_field_reader(field_names),
        steps=steps,
        json_steps=json_steps,
        csv_steps=csv_steps,
        all_plain=_is_one_run(steps),
        json_all_plain=_is_one_run(json_steps),
        csv_all_plain=_is_one_run(csv_steps),
        missing_columns=(None,) * len(columns),
    )


def _is_one_run(steps: tuple[_Step, ...]) -> bool:
    return len(steps) == 0 or (len(steps) == 1 and isinstance(steps[0], _FieldRun))


def column_names(record_type: type) -> tuple[str, ...]:
    """Return the flat column names of a record type, in field declaration order.

    The names come from the type hints alone, are computed once per type, and equal the keys of
    flatten_dict(record_to_dict(record, ...)) for every record of the type.

    Raises:
        TypeError: record_type is not a record dataclass, a field has a type that export does
            not support, or an unknown field has no UNKNOWN_KEYS.
        ValueError: Two fields give the same dict key or flat column name.
    """
    return _class_plan(record_type).columns


def _sequence_type_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(f"{field_plan.qualified_name} is not a tuple or None")


def _coded_type_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(f"{field_plan.qualified_name} is not a CodedValue or None")


def _coded_item_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(f"{field_plan.qualified_name} holds an item that is not a CodedValue")


def _record_item_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(
        f"{field_plan.qualified_name} holds an item that is not an instance of "
        f"{field_plan.members.record_type.__name__}"
    )


def _mapping_type_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(f"{field_plan.qualified_name} is not a mapping")


def _sequence_items(field_plan: _FieldPlan, value: object) -> Sequence[object]:
    if not isinstance(value, (tuple, list)):
        raise _sequence_type_error(field_plan)
    return cast("Sequence[object]", value)


def _coded_pair(field_plan: _FieldPlan, value: object) -> tuple[object, object]:
    if value is None:
        return _MISSING_PAIR
    if not isinstance(value, CodedValue):
        raise _coded_type_error(field_plan)
    coded_value = cast("CodedValue[Any]", value)
    return coded_value.label_text, coded_value.raw


def _scalar_items(field_plan: _FieldPlan, value: object, *, json_ready: bool) -> object:
    if value is None:
        return None
    items = _sequence_items(field_plan, value)
    if field_plan.item_kind == "text_enum":
        items = [item.value if isinstance(item, StrEnum) else item for item in items]
    elif field_plan.item_kind == "date" and json_ready:
        items = [item.isoformat() if isinstance(item, (date, time)) else item for item in items]
    return list(items) if json_ready else tuple(items)


def _coded_items(
    field_plan: _FieldPlan, value: object, *, json_ready: bool
) -> tuple[object, object]:
    if value is None:
        return _MISSING_PAIR
    labels: list[str] = []
    codes: list[int] = []
    for item in _sequence_items(field_plan, value):
        if not isinstance(item, CodedValue):
            raise _coded_item_error(field_plan)
        coded_item = cast("CodedValue[Any]", item)
        labels.append(coded_item.label_text)
        codes.append(coded_item.raw)
    if json_ready:
        return labels, codes
    return tuple(labels), tuple(codes)


def _record_items(field_plan: _FieldPlan, value: object, *, json_ready: bool) -> object:
    if value is None:
        return None
    members = field_plan.members
    nested_items: list[object] = []
    for item in _sequence_items(field_plan, value):
        if not isinstance(item, members.record_type):
            raise _record_item_error(field_plan)
        nested_items.append(_nested_record(item, members, json_ready=json_ready))
    return nested_items if json_ready else tuple(nested_items)


def _filled_unknown(field_plan: _FieldPlan, value: object) -> dict[object, object]:
    """Return the declared unknown keys in order, each with the mapping's value or None.

    Raises:
        TypeError: value is not a mapping.
        ValueError: The mapping holds a key that UNKNOWN_KEYS does not declare.
    """
    if not isinstance(value, Mapping):
        raise _mapping_type_error(field_plan)
    unknown_mapping = cast("Mapping[object, object]", value)
    filled = cast("dict[object, object]", dict.fromkeys(field_plan.unknown_keys))
    filled.update(unknown_mapping)
    if len(filled) != len(field_plan.unknown_keys):
        undeclared_keys = [key for key in unknown_mapping if key not in field_plan.unknown_key_set]
        raise ValueError(
            f"{field_plan.qualified_name} has keys missing from UNKNOWN_KEYS: "
            + ", ".join(repr(key) for key in undeclared_keys)
        )
    return filled


def _whole_mapping(field_plan: _FieldPlan, value: object) -> FrozenMapping[str, int] | None:
    """A mapping field as one value, read-only so that a flat row keeps it whole.

    It is copied into a FrozenMapping whatever mapping the record holds, because flatten_dict
    and pandas.json_normalize both split a plain dict into a column per key, and the keys of
    this field are not columns.

    Raises:
        TypeError: value is not a mapping.
    """
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise _mapping_type_error(field_plan)
    return FrozenMapping(cast("Mapping[str, int]", value))


def _unknown_values(field_plan: _FieldPlan, value: object) -> list[object]:
    if value is None:
        return [None] * len(field_plan.unknown_keys)
    return list(_filled_unknown(field_plan, value).values())


def _group_type_error(field_plan: _FieldPlan) -> TypeError:
    return TypeError(
        f"{field_plan.qualified_name} is not an instance of "
        f"{field_plan.members.record_type.__name__} or None"
    )


def _missing_nested(class_plan: _ClassPlan) -> dict[str, object]:
    """Build the nested dict of a missing group: every key present, every value None."""
    nested: dict[str, object] = {}
    for field_plan in class_plan.fields:
        match field_plan.kind:
            case "group":
                nested[field_plan.name] = _missing_nested(field_plan.members)
            case "unknown":
                nested[field_plan.name] = dict.fromkeys(field_plan.unknown_keys)
            case "coded" | "coded_values":
                nested[field_plan.name] = None
                nested[field_plan.code_name] = None
            case "value" | "bool" | "date" | "text_enum" | "values" | "records" | "mapping":
                nested[field_plan.name] = None
    return nested


def _nested_record(
    record: object, class_plan: _ClassPlan, *, json_ready: bool
) -> dict[str, object]:
    field_values = class_plan.read_fields(record)
    nested: dict[str, object] = {}
    for step in class_plan.json_steps if json_ready else class_plan.steps:
        if isinstance(step, _FieldRun):
            nested.update(zip(step.names, field_values[step.values]))
            continue
        field_name = step.name
        value = field_values[step.index]
        match step.kind:
            case "value" | "bool":
                nested[field_name] = value
            case "date":
                nested[field_name] = (
                    value.isoformat() if json_ready and isinstance(value, (date, time)) else value
                )
            case "text_enum":
                nested[field_name] = value.value if isinstance(value, StrEnum) else value
            case "coded":
                nested[field_name], nested[step.code_name] = _coded_pair(step, value)
            case "group":
                members = step.members
                if value is None:
                    nested[field_name] = _missing_nested(members)
                elif isinstance(value, members.record_type):
                    nested[field_name] = _nested_record(value, members, json_ready=json_ready)
                else:
                    raise _group_type_error(step)
            case "values":
                nested[field_name] = _scalar_items(step, value, json_ready=json_ready)
            case "coded_values":
                nested[field_name], nested[step.code_name] = _coded_items(
                    step, value, json_ready=json_ready
                )
            case "records":
                nested[field_name] = _record_items(step, value, json_ready=json_ready)
            case "unknown":
                nested[field_name] = dict(zip(step.unknown_keys, _unknown_values(step, value)))
            case "mapping":
                nested[field_name] = _whole_mapping(step, value)
    return nested


def _append_flat_values(
    flat_values: list[object], record: object, class_plan: _ClassPlan, *, json_ready: bool
) -> None:
    """Append a record's flat column values, in column order, without building nested dicts."""
    field_values = class_plan.read_fields(record)
    for step in class_plan.json_steps if json_ready else class_plan.steps:
        if isinstance(step, _FieldRun):
            flat_values.extend(field_values[step.values])
            continue
        value = field_values[step.index]
        match step.kind:
            case "group":
                members = step.members
                if value is None:
                    flat_values.extend(members.missing_columns)
                elif not isinstance(value, members.record_type):
                    raise _group_type_error(step)
                elif members.json_all_plain if json_ready else members.all_plain:
                    flat_values.extend(members.read_fields(value))
                else:
                    _append_flat_values(flat_values, value, members, json_ready=json_ready)
            case "coded":
                flat_values.extend(_coded_pair(step, value))
            case "text_enum":
                flat_values.append(value.value if isinstance(value, StrEnum) else value)
            case "values":
                flat_values.append(_scalar_items(step, value, json_ready=json_ready))
            case "coded_values":
                flat_values.extend(_coded_items(step, value, json_ready=json_ready))
            case "records":
                flat_values.append(_record_items(step, value, json_ready=json_ready))
            case "unknown":
                flat_values.extend(_unknown_values(step, value))
            case "mapping":
                flat_values.append(_whole_mapping(step, value))
            case "date":
                flat_values.append(
                    value.isoformat() if json_ready and isinstance(value, (date, time)) else value
                )
            case "value" | "bool":
                flat_values.append(value)


def _append_csv_cells(cells: list[object], record: object, class_plan: _ClassPlan) -> None:
    """Append a record's CSV cells, in column order, without building flat rows.

    A cell is either the text _csv_cell gives for the flat value, or a value the csv module
    writes as that same text: an int or str field's value, a coded value's label and code, a
    text enum's value, an unknown mapping's values, and None for a missing tuple or an empty
    tuple of records. An empty tuple of plain or coded values gives "".
    """
    field_values = class_plan.read_fields(record)
    for step in class_plan.csv_steps:
        if isinstance(step, _FieldRun):
            cells.extend(field_values[step.values])
            continue
        value = field_values[step.index]
        match step.kind:
            case "group":
                members = step.members
                if value is None:
                    cells.extend(members.missing_columns)
                elif not isinstance(value, members.record_type):
                    raise _group_type_error(step)
                elif members.csv_all_plain:
                    cells.extend(members.read_fields(value))
                else:
                    _append_csv_cells(cells, value, members)
            case "values":
                # Text enum and date items give the same text through _csv_items_text.
                cells.append(
                    None if value is None else _csv_items_text(_sequence_items(step, value))
                )
            case "date":
                cells.append(
                    value.isoformat()
                    if type(value) is date or type(value) is time
                    else _csv_cell(value)
                )
            case "records":
                # Every item is a dict, so a tuple with items is always compact JSON.
                record_items = _record_items(step, value, json_ready=False)
                cells.append(_compact_json(record_items) if record_items else None)
            case "coded":
                cells.extend(_coded_pair(step, value))
            case "coded_values":
                if value is None:
                    cells.extend(_MISSING_PAIR)
                else:
                    labels, codes = cast(
                        "tuple[Sequence[object], Sequence[object]]",
                        _coded_items(step, value, json_ready=False),
                    )
                    cells.extend((_csv_items_text(labels), _csv_items_text(codes)))
            case "unknown":
                cells.extend(_unknown_values(step, value))
            case "mapping":
                # A mapping is always compact JSON, which is what _csv_cell gives for one, so
                # an empty mapping is "{}" and only a missing one is an empty cell.
                whole_mapping = _whole_mapping(step, value)
                cells.append(None if whole_mapping is None else _compact_json(whole_mapping))
            case "text_enum":
                cells.append(value.value if isinstance(value, StrEnum) else value)
            case "bool":
                cells.append(("true" if value else "false") if type(value) is bool else value)
            case "value":
                cells.append(value)


def record_to_dict(record: object, *, json_ready: bool) -> dict[str, object]:
    """Turn a record into a nested dict of its fields, in declaration order.

    A group field becomes a nested dict, and a missing group a nested dict of None values. A
    coded value "x" becomes the keys "x" (its label text) and "x_code" (its raw number); a tuple
    of coded values becomes the same two keys holding the label texts and the raw numbers in
    order. A StrEnum becomes its value string. The unknown field becomes a dict with exactly
    the record type's UNKNOWN_KEYS, None where a key is absent. A mapping field whose keys the
    type does not declare stays one read-only mapping, so flatten_dict keeps it whole. Tuples
    of plain values keep their None items.

    Args:
        record: A record dataclass instance.
        json_ready: When true, dates and times become ISO 8601 strings and tuples become lists.

    Raises:
        TypeError: The record's type is not supported (see column_names), or a value does not
            match its field's type: for example a group of another class, or a None item in a
            tuple of records or coded values.
        ValueError: Two fields of the type give the same key or column name, or the unknown
            mapping holds a key its type does not declare in UNKNOWN_KEYS.
    """
    return _nested_record(record, _class_plan(type(record)), json_ready=json_ready)


def _flatten_into(flat: dict[str, object], nested: Mapping[str, object], prefix: str) -> None:
    for key, value in nested.items():
        column_name = f"{prefix}{key}"
        if isinstance(value, dict):
            _flatten_into(flat, cast("dict[str, object]", value), f"{column_name}_")
        else:
            flat[column_name] = value


def flatten_dict(nested: Mapping[str, object]) -> dict[str, object]:
    """Join the keys of nested dicts with "_", the way pandas.json_normalize(sep="_") does.

    Lists and tuples are kept whole as single values, even when their items are dicts, and so
    is a mapping that is not a dict, which is what a mapping column holds.
    """
    flat: dict[str, object] = {}
    _flatten_into(flat, nested, "")
    return flat


def select_columns(flat_row: Mapping[str, object], selected: Sequence[str]) -> dict[str, object]:
    """Return the selected columns of a flat row, in the order they were selected.

    Raises:
        ValueError: A selected name is not a column of the row. The message lists every such
            name.
    """
    unknown_names = [name for name in selected if name not in flat_row]
    if unknown_names:
        raise ValueError("unknown columns: " + ", ".join(unknown_names))
    return {name: flat_row[name] for name in selected}


def to_columns(records: Iterable[object], record_type: type) -> dict[str, list[object]]:
    """Collect records into flat columns of Python values, keyed by column_names(record_type).

    Values are not made JSON-ready: dates stay datetime.date and tuples stay tuples.

    Raises:
        TypeError: A record is not exactly of record_type, record_type is not supported, or a
            value does not match its field's type.
        ValueError: Two fields give the same column name, or a record's unknown mapping holds
            an undeclared key.
    """
    class_plan = _class_plan(record_type)
    columns: dict[str, list[object]] = {name: [] for name in class_plan.columns}
    column_appenders = [column_values.append for column_values in columns.values()]
    flat_values: list[object] = []
    for record in records:
        if type(record) is not record_type:
            raise _record_type_error("to_columns", record_type, record)
        flat_values.clear()
        _append_flat_values(flat_values, record, class_plan, json_ready=False)
        for append_value, value in zip(column_appenders, flat_values, strict=True):
            append_value(value)
    return columns


def _require_types(
    values: Iterable[object],
    expected_type: type | tuple[type, ...],
    type_error: Callable[[], TypeError],
) -> None:
    """Raise type_error() unless every value is an instance of expected_type.

    Each distinct type is checked once, so the cost barely grows with the number of values.
    """
    for value_type in set(map(type, values)):
        if not issubclass(value_type, expected_type):
            raise type_error()


def _present_values(values: Sequence[object]) -> list[object]:
    return list(filter(_is_present, values))


def _items_of_present_values(values: Sequence[object]) -> list[object]:
    return list(itertools.chain.from_iterable(cast("Sequence[Iterable[object]]", values)))


def _missing_counts(records: Sequence[object], class_plan: _ClassPlan) -> list[int]:
    """Count the records whose flat value is None, for each column of class_plan, in order.

    The fields of all records are read at once into one tuple of values per field, and None
    is counted with tuple.count, so no flat column is built. Values are checked against their
    field types, and a malformed value raises the same error to_columns raises for it. Checks
    run one field at a time across all records, though, so when several values are malformed
    the first error raised may differ from the one to_columns raises first.
    """
    record_count = len(records)
    if records:
        field_columns = list(zip(*map(class_plan.read_fields, records), strict=True))
    else:
        field_columns = [()] * len(class_plan.fields)
    missing_counts: list[int] = []
    for field_plan in class_plan.fields:
        values: tuple[object, ...] = field_columns[field_plan.index]
        match field_plan.kind:
            case "value" | "bool" | "date" | "text_enum":
                missing_counts.append(values.count(None))
            case "coded":
                _require_types(
                    values,
                    (CodedValue, _NONE_TYPE),
                    functools.partial(_coded_type_error, field_plan),
                )
                present = _present_values(values)
                absent_count = record_count - len(present)
                for read_part in (_read_label_text, _read_raw):
                    missing_counts.append(absent_count + list(map(read_part, present)).count(None))
            case "group":
                members = field_plan.members
                _require_types(
                    values,
                    (members.record_type, _NONE_TYPE),
                    functools.partial(_group_type_error, field_plan),
                )
                present = _present_values(values)
                absent_count = record_count - len(present)
                missing_counts.extend(
                    absent_count + member_missing_count
                    for member_missing_count in _missing_counts(present, members)
                )
            case "values" | "coded_values" | "records":
                _require_types(
                    values,
                    (tuple, list, _NONE_TYPE),
                    functools.partial(_sequence_type_error, field_plan),
                )
                # A present tuple is a present value, even when it is empty.
                missing_count = values.count(None)
                if field_plan.kind == "values":
                    missing_counts.append(missing_count)
                    continue
                items = _items_of_present_values(_present_values(values))
                if field_plan.kind == "coded_values":
                    _require_types(
                        items, CodedValue, functools.partial(_coded_item_error, field_plan)
                    )
                    missing_counts.extend((missing_count, missing_count))
                    continue
                _require_types(
                    items,
                    field_plan.members.record_type,
                    functools.partial(_record_item_error, field_plan),
                )
                # Only checks the items' own values; their counts are not columns.
                _missing_counts(items, field_plan.members)
                missing_counts.append(missing_count)
            case "mapping":
                _require_types(
                    values,
                    (Mapping, _NONE_TYPE),
                    functools.partial(_mapping_type_error, field_plan),
                )
                # A present mapping is a present value, even when it holds nothing.
                missing_counts.append(values.count(None))
            case "unknown":
                _require_types(
                    values,
                    (Mapping, _NONE_TYPE),
                    functools.partial(_mapping_type_error, field_plan),
                )
                present = _present_values(values)
                absent_count = record_count - len(present)
                filled_mappings = [
                    _filled_unknown(field_plan, unknown_mapping) for unknown_mapping in present
                ]
                missing_counts.extend(
                    absent_count + list(map(operator.itemgetter(key), filled_mappings)).count(None)
                    for key in field_plan.unknown_keys
                )
    return missing_counts


def _present_counts(  # pyright: ignore[reportUnusedFunction]
    records: Iterable[object], record_type: type, *, operation_name: str
) -> dict[str, int]:
    """Count the records whose flat value is not None, for each column of record_type.

    Keys are column_names(record_type). Each count equals len(values) - values.count(None) for
    that column of to_columns(records, record_type), but no column is built. A present tuple
    counts as present even when it is empty, and every column of a missing group counts as
    missing.

    Raises the errors to_columns raises, except that the error for a record of another type
    names operation_name instead. Every record's type is checked before any value, and values
    one field at a time, so when several things are wrong the first error raised may differ.

    Args:
        records: Records that are all exactly of record_type.
        record_type: The record class.
        operation_name: The public operation the caller offers, such as "coverage", which the
            error for a record of another type names.

    Raises:
        TypeError: A record is not exactly of record_type, record_type is not supported, or a
            value does not match its field's type.
        ValueError: Two fields give the same column name, or a record's unknown mapping holds
            an undeclared key.
    """
    class_plan = _class_plan(record_type)
    record_list = list(records)
    if set(map(type, record_list)) - {record_type}:
        stray_record = next(record for record in record_list if type(record) is not record_type)
        raise _record_type_error(operation_name, record_type, stray_record)
    record_count = len(record_list)
    missing_counts = _missing_counts(record_list, class_plan)
    return {
        column_name: record_count - missing_count
        for column_name, missing_count in zip(class_plan.columns, missing_counts, strict=True)
    }


def flat_rows[RecordT](
    records: Iterable[RecordT], record_type: type[RecordT], *, json_ready: bool = False
) -> Iterator[dict[str, object]]:
    """Yield each record as a flat row keyed by column_names(record_type), one at a time.

    Each row equals flatten_dict(record_to_dict(record, json_ready=json_ready)), but is built
    in one pass without nested dicts.

    Args:
        records: Records that are all exactly of record_type.
        record_type: The record class.
        json_ready: When true, dates and times become ISO 8601 strings and tuples become lists.

    Raises:
        TypeError: A record is not exactly of record_type, record_type is not supported, or a
            value does not match its field's type.
        ValueError: Two fields give the same column name, or a record's unknown mapping holds
            an undeclared key.

    An unsupported record_type raises when flat_rows is called; problems with the records
    themselves raise while the rows are iterated.
    """
    class_plan = _class_plan(record_type)
    return _flat_row_values(records, record_type, class_plan, json_ready=json_ready)


def _flat_row_values(
    records: Iterable[object], record_type: type, class_plan: _ClassPlan, *, json_ready: bool
) -> Iterator[dict[str, object]]:
    columns = class_plan.columns
    for record in records:
        if type(record) is not record_type:
            raise _record_type_error("flat_rows", record_type, record)
        flat_values: list[object] = []
        _append_flat_values(flat_values, record, class_plan, json_ready=json_ready)
        yield dict(zip(columns, flat_values, strict=True))


def _record_type_error(function_name: str, record_type: type, record: object) -> TypeError:
    return TypeError(
        f"{function_name} expected {record_type.__name__} records, not {type(record).__name__}"
    )


def _json_default(value: object) -> object:
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Mapping):
        # A read-only mapping column, which json writes as an object. A plain dict never
        # reaches here, since json writes one itself.
        return dict(cast("Mapping[str, object]", value))
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=_json_default)


def _csv_items_text(items: Sequence[object]) -> str:
    """A tuple or list as one cell: compact JSON when an item is a mapping, else joined with ";"."""
    if not items:
        return ""
    item_types = set(map(type, items))
    if item_types <= _STR_ONLY:
        return _CSV_ITEM_SEPARATOR.join(cast("Sequence[str]", items))
    if item_types <= _INT_ONLY:
        return _CSV_ITEM_SEPARATOR.join(map(str, items))
    if any(isinstance(item, Mapping) for item in items):
        return _compact_json(items)
    return _CSV_ITEM_SEPARATOR.join(_csv_cell(item) for item in items)


def _csv_cell(value: object) -> str:
    value_type = type(value)
    if value_type is str:
        return cast("str", value)
    if value_type is int:
        return str(value)
    if value is None:
        return ""
    if value_type is tuple or value_type is list:
        return _csv_items_text(cast("Sequence[object]", value))
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return _compact_json(cast("Mapping[object, object]", value))
    if isinstance(value, (tuple, list)):
        # Only tuple and list subclasses reach this; exact tuples and lists are handled above.
        return _csv_items_text(cast("Sequence[object]", value))
    return str(value)


def _cell_reader[KeyT](keys: list[KeyT]) -> Callable[[Any], tuple[object, ...]]:
    """Return the cells at the given keys of a row, as a tuple, for any number of keys."""
    if not keys:
        return lambda row: ()
    if len(keys) == 1:
        only_key = keys[0]
        return lambda row: (row[only_key],)
    return operator.itemgetter(*keys)


@contextmanager
def _text_output(
    destination: str | os.PathLike[str] | TextIO, *, newline: str
) -> Generator[TextIO, None, None]:
    """Yield a text stream: a path is opened as UTF-8 and closed, a stream is left open."""
    if isinstance(destination, (str, os.PathLike)):
        with open(destination, "w", encoding="utf-8", newline=newline) as stream:
            yield stream
    else:
        yield destination


def write_csv(
    flat_rows: Iterable[Mapping[str, object]],
    columns: Sequence[str],
    destination: str | os.PathLike[str] | TextIO,
) -> None:
    """Write flat rows as UTF-8 CSV with a header row, keeping only the given columns.

    None is an empty cell, booleans are "true" or "false" and dates are ISO 8601. A tuple or
    list of plain values is joined with ";" (a None item is an empty segment), and one holding
    dicts is compact JSON text. Rows end with "\\r\\n", as in standard CSV. A path is opened
    and closed here; a stream is written to and left open, and should have been opened with
    newline="".

    Raises:
        TypeError: columns is a single string instead of a sequence of names.
        KeyError: A row has no value for one of the columns.
    """
    if isinstance(columns, str):
        raise TypeError("columns must be a sequence of column names, not a string")
    column_list = list(columns)
    read_cells = _cell_reader(column_list)
    with _text_output(destination, newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(column_list)
        for flat_row in flat_rows:
            # Strings and plain ints, the most common cells, skip the conversion call.
            writer.writerow(
                [
                    cell
                    if (cell_type := type(cell)) is str or cell_type is int
                    else _csv_cell(cell)
                    for cell in read_cells(flat_row)
                ]
            )


def _write_records_csv[RecordT](  # pyright: ignore[reportUnusedFunction]
    records: Iterable[RecordT],
    record_type: type[RecordT],
    destination: str | os.PathLike[str] | TextIO,
    *,
    columns: Sequence[str] | None = None,
    operation_name: str,
) -> None:
    """Write records as UTF-8 CSV with a header row, straight from their fields.

    The text equals write_csv(flat_rows(records, record_type), columns, destination), with
    columns defaulting to column_names(record_type), but no flat rows are built. See write_csv
    for how cells are written and how the destination is handled.

    Args:
        records: Records that are all exactly of record_type.
        record_type: The record class.
        destination: A path, or a stream opened with newline="".
        columns: The flat column names to write, in this order, or None for every column.
        operation_name: The public operation the caller offers, such as "write_csv", which
            the error for a record of another type names.

    Raises:
        TypeError: columns is a single string, a record is not exactly of record_type,
            record_type is not supported, or a value does not match its field's type.
        ValueError: A name in columns is not a column of record_type (raised before anything
            is written), two fields give the same column name, or a record's unknown mapping
            holds an undeclared key.
    """
    class_plan = _class_plan(record_type)
    if isinstance(columns, str):
        raise TypeError("columns must be a sequence of column names, not a string")
    column_list = list(class_plan.columns if columns is None else columns)
    read_cells: Callable[[list[object]], tuple[object, ...]] | None = None
    if column_list != list(class_plan.columns):
        column_indexes = {name: index for index, name in enumerate(class_plan.columns)}
        unknown_names = [name for name in column_list if name not in column_indexes]
        if unknown_names:
            raise ValueError("unknown columns: " + ", ".join(unknown_names))
        read_cells = _cell_reader([column_indexes[name] for name in column_list])
    with _text_output(destination, newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(column_list)
        writer.writerows(_csv_rows(records, record_type, class_plan, read_cells, operation_name))


def _csv_rows(
    records: Iterable[object],
    record_type: type,
    class_plan: _ClassPlan,
    read_cells: Callable[[list[object]], tuple[object, ...]] | None,
    operation_name: str,
) -> Iterator[Sequence[object]]:
    for record in records:
        if type(record) is not record_type:
            raise _record_type_error(operation_name, record_type, record)
        cells: list[object] = []
        _append_csv_cells(cells, record, class_plan)
        row: Sequence[object] = cells if read_cells is None else read_cells(cells)
        if not _CSV_NATIVE_TYPES.issuperset(map(type, row)):
            # A value whose type its field does not declare, such as a bool in an int field.
            row = [_csv_cell(cell) for cell in row]
        yield row


def write_json(
    nested_rows: Iterable[Mapping[str, object]], destination: str | os.PathLike[str] | TextIO
) -> None:
    """Write nested rows as one UTF-8 JSON array, indented by 2 spaces.

    Rows are expected from record_to_dict(record, json_ready=True). The text equals
    json.dumps(rows, ensure_ascii=False, indent=2) plus a final newline, but rows are written
    one at a time. A path destination is opened with "\\n" line endings on every OS and closed
    here. A stream destination is written to and left open, and its own newline setting
    applies.
    """
    with _text_output(destination, newline="\n") as stream:
        wrote_a_row = False
        for nested_row in nested_rows:
            row_text = json.dumps(nested_row, ensure_ascii=False, indent=2, default=_json_default)
            stream.write("," if wrote_a_row else "[")
            stream.write("\n  " + row_text.replace("\n", "\n  "))
            wrote_a_row = True
        stream.write("\n]\n" if wrote_a_row else "[]\n")


def write_jsonl(
    nested_rows: Iterable[Mapping[str, object]], destination: str | os.PathLike[str] | TextIO
) -> None:
    """Write nested rows as UTF-8 JSON Lines: one compact object per line.

    Rows are expected from record_to_dict(record, json_ready=True). A path destination is
    opened with "\\n" line endings on every OS and closed here. A stream destination is written
    to and left open, and its own newline setting applies.
    """
    with _text_output(destination, newline="\n") as stream:
        for nested_row in nested_rows:
            stream.write(_compact_json(nested_row) + "\n")


def _is_nullable_integer_column(values: list[object]) -> bool:
    has_integer = False
    has_none = False
    for value in values:
        if value is None:
            has_none = True
        elif isinstance(value, int) and not isinstance(value, bool):
            has_integer = True
        else:
            return False
    return has_integer and has_none


def to_pandas(columns: Mapping[str, list[object]]) -> Any:
    """Build a pandas.DataFrame from flat columns, such as those from to_columns.

    Integer columns that also hold None use the nullable "Int64" dtype. Every other column
    uses the pandas default.

    Returns:
        A pandas.DataFrame. The return type is Any because pandas is an optional dependency.

    Raises:
        ImportError: pandas is not installed.
    """
    try:
        pandas_module = importlib.import_module("pandas")
    except ImportError as error:
        raise ImportError('to_pandas() needs pandas: pip install "fmsave[pandas]"') from error
    frame_columns: dict[str, object] = {
        name: pandas_module.array(values, dtype="Int64")
        if _is_nullable_integer_column(values)
        else values
        for name, values in columns.items()
    }
    return pandas_module.DataFrame(frame_columns)


def _polars_column(values: list[object]) -> list[object]:
    """The column as polars takes it: a read-only mapping becomes a plain dict.

    polars builds a struct column from dicts and does not read any other mapping. Only the
    first value present is looked at, since every value of a column is of its field's one kind.
    """
    first_value = next((value for value in values if value is not None), None)
    if isinstance(first_value, Mapping) and not isinstance(first_value, dict):
        return [
            dict(cast("Mapping[str, object]", value)) if value is not None else None
            for value in values
        ]
    return values


def to_polars(columns: Mapping[str, list[object]]) -> Any:
    """Build a polars.DataFrame from flat columns, such as those from to_columns.

    A mapping column becomes a struct column.

    Returns:
        A polars.DataFrame built with strict=False. The return type is Any because polars is an
        optional dependency.

    Raises:
        ImportError: polars is not installed.
    """
    try:
        polars_module = importlib.import_module("polars")
    except ImportError as error:
        raise ImportError('to_polars() needs polars: pip install "fmsave[polars]"') from error
    return polars_module.DataFrame(
        {name: _polars_column(values) for name, values in columns.items()}, strict=False
    )
