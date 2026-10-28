"""The registry of field statuses: whether each public field's meaning is verified.

A status belongs to the class that declares the field. A field whose type is another record
class (optionally with None) is a group: its values flatten into the parent's columns, it has no
status of its own, and its fields are registered on the group's class. field_status resolves a
dotted path such as "ability.current" through the group's class.

Every field that uses the same group class shares that class's statuses, so groups whose
statuses can differ must be separate classes. A tuple of records is an ordinary field of the
parent; the element class registers its own fields.
"""

from __future__ import annotations

import dataclasses
import types
import typing
from collections.abc import Iterable
from typing import Literal

from fm26save._core._frozen import FrozenMapping

type FieldStatus = Literal["verified", "unconfirmed"]

_statuses_by_class: dict[type, dict[str, FieldStatus]] = {}


def _path_list(model_class: type, paths: Iterable[str], argument_name: str) -> list[str]:
    if isinstance(paths, str):
        raise TypeError(
            f"{argument_name} for {model_class.__name__} must be an iterable of paths, not a string"
        )
    return list(paths)


def _dataclass_field_names(model_class: type) -> set[str]:
    if not dataclasses.is_dataclass(model_class):
        return set()
    return {model_field.name for model_field in dataclasses.fields(model_class)}


def computed_field_names(model_class: type) -> tuple[str, ...]:
    """The names a record class lists in COMPUTED_FIELDS, empty when it lists none.

    A computed field is a read-only property worked out from the record's stored fields. It
    costs nothing per record, and every export form writes it after the stored fields.

    Raises:
        TypeError: A listed name is not a property of the class.
    """
    names: tuple[str, ...] = getattr(model_class, "COMPUTED_FIELDS", ())
    for name in names:
        if not isinstance(getattr(model_class, name, None), property):
            raise TypeError(
                f"{model_class.__name__}.{name} is listed as computed but is not a property"
            )
    return names


def _group_class(field_type: object) -> type | None:
    if typing.get_origin(field_type) in (typing.Union, types.UnionType):
        member_types = [
            member_type
            for member_type in typing.get_args(field_type)
            if member_type is not type(None)
        ]
        if len(member_types) != 1:
            return None
        field_type = member_types[0]
    if isinstance(field_type, type) and dataclasses.is_dataclass(field_type):
        # Imported here because the model modules import this module.
        from fm26save._core.models.common import CodedValue

        if field_type is not CodedValue:
            return field_type
    return None


def _group_classes(model_class: type) -> dict[str, type]:
    """Map each group field of a dataclass to the record class of its values."""
    if not dataclasses.is_dataclass(model_class):
        return {}
    type_parameters: dict[str, object] = {
        type_parameter.__name__: type_parameter
        for type_parameter in getattr(model_class, "__type_params__", ())
    }
    field_types = typing.get_type_hints(model_class, localns=type_parameters)
    group_classes: dict[str, type] = {}
    for model_field in dataclasses.fields(model_class):
        group_class = _group_class(field_types[model_field.name])
        if group_class is not None:
            group_classes[model_field.name] = group_class
    return group_classes


def register_field_statuses(
    model_class: type, *, verified: Iterable[str] = (), unconfirmed: Iterable[str] = ()
) -> None:
    """Record the status of fields declared by a record class.

    Only the class's own field names are accepted. Fields of a group are registered on the
    group's class. Registering a field again with the same status is allowed. When any field is
    rejected, nothing from the call is recorded.

    Raises:
        TypeError: verified or unconfirmed is a single string instead of an iterable of names.
        ValueError: A name is dotted or malformed, is not a dataclass field of the class, is a
            group field, is listed with both statuses, or is already registered with the other
            status; or a different class with the same name already has registered statuses.
    """
    class_name = model_class.__name__
    requested_statuses: dict[str, FieldStatus] = {}
    for field_path in _path_list(model_class, verified, "verified"):
        requested_statuses[field_path] = "verified"
    for field_path in _path_list(model_class, unconfirmed, "unconfirmed"):
        if requested_statuses.get(field_path) == "verified":
            raise ValueError(
                f"{class_name}.{field_path} is listed as both verified and unconfirmed"
            )
        requested_statuses[field_path] = "unconfirmed"
    if not requested_statuses:
        return

    field_names = _dataclass_field_names(model_class) | set(computed_field_names(model_class))
    for field_path in requested_statuses:
        if "." in field_path:
            raise ValueError(
                f"{field_path!r} is a nested path for {class_name}; register the field on the "
                "group's own class instead"
            )
        if not field_path.isidentifier():
            raise ValueError(f"malformed field name {field_path!r} for {class_name}")
        if field_path not in field_names:
            raise ValueError(f"{class_name} has no dataclass field {field_path!r}")

    group_classes = _group_classes(model_class)
    for field_path in requested_statuses:
        group_class = group_classes.get(field_path)
        if group_class is not None:
            raise ValueError(
                f"{class_name}.{field_path} is a group of {group_class.__name__} fields and has "
                f"no status of its own; register the fields on {group_class.__name__} instead"
            )

    for registered_class in _statuses_by_class:
        if registered_class is not model_class and registered_class.__name__ == class_name:
            raise ValueError(f"a different class named {class_name} already has field statuses")

    existing_statuses = _statuses_by_class.get(model_class, {})
    for field_path, status in requested_statuses.items():
        existing_status = existing_statuses.get(field_path)
        if existing_status is not None and existing_status != status:
            raise ValueError(
                f"{class_name}.{field_path} is already registered as {existing_status}"
            )

    _statuses_by_class.setdefault(model_class, {}).update(requested_statuses)


def field_status(model_class: type, field_name: str) -> FieldStatus:
    """Return whether the meaning of a public record field is verified or unconfirmed.

    Args:
        model_class: A record class, for example fmsave.SaveInfo.
        field_name: The field name. Dots reach into groups, for example "contract.wage".

    Raises:
        KeyError: The field has no registered status, or a dotted path passes through a field
            that is not a group.
    """
    *group_names, leaf_name = field_name.split(".")
    owner_class = model_class
    for group_name in group_names:
        group_class = _group_classes(owner_class).get(group_name)
        if group_class is None:
            raise KeyError(
                f"{model_class.__name__} has no registered status for {field_name!r}: "
                f"{group_name!r} is not a group field of {owner_class.__name__}"
            )
        owner_class = group_class
    try:
        return _statuses_by_class[owner_class][leaf_name]
    except KeyError:
        raise KeyError(
            f"{model_class.__name__} has no registered status for {field_name!r}"
        ) from None


def registered_statuses() -> FrozenMapping[str, FieldStatus]:
    """Return every registered status, keyed by "<ClassName>.<field>" in sorted order."""
    named_statuses: dict[str, FieldStatus] = {
        f"{model_class.__name__}.{field_path}": status
        for model_class, statuses in _statuses_by_class.items()
        for field_path, status in statuses.items()
    }
    sorted_statuses: dict[str, FieldStatus] = dict(sorted(named_statuses.items()))
    return FrozenMapping(sorted_statuses)
