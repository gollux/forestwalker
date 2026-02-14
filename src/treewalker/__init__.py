# A simple module for walking through a parsed JSON-like file
# (c) 2023-2026 Martin Mareš <mj@ucw.cz>

from collections.abc import Iterator
from enum import Enum
import re
from typing import Any, Optional, NoReturn, Tuple, Set, Type, TypeVar, Self


T = TypeVar('T')
E = TypeVar('E', bound=Enum)


class Walker:
    """
        A Walker is a pointer to a particular node of the tree,
        or possible a missing child node. It also remembers the
        path to the node.
    """

    obj: Any
    """The tree node. :py:class:`MissingValue` if it is a missing node."""

    parent: Optional['Walker'] = None
    """Walker of the parent node. Used to reconstruct the path."""

    custom_context: str = ""

    def __init__(self, root: Any) -> None:
        """Create a walker point to the given root of the tree."""
        self.obj = root

    def raise_error(self, msg) -> NoReturn:
        """Raise a :py:exc:`WalkerError` on the current node with the given error message."""
        raise WalkerError(self, msg)

    def is_null(self) -> bool:
        """Tests if the current node is ``None`` (JSON ``null``)."""
        return self.obj is None

    def is_str(self) -> bool:
        """Tests if the current node is a string."""
        return isinstance(self.obj, str)

    def is_int(self) -> bool:
        """Tests if the current node is an integer."""
        return isinstance(self.obj, int)

    def is_number(self) -> bool:
        """Tests if the current node is an integer or float."""
        return isinstance(self.obj, int) or isinstance(self.obj, float)

    def is_bool(self) -> bool:
        """Tests if the current node is a Boolean value."""
        return isinstance(self.obj, bool)

    def is_missing(self) -> bool:
        """Tests if the current node is a missing child."""
        return isinstance(self.obj, MissingValue)

    def is_present(self) -> bool:
        """Tests if the current node is *not* a missing child."""
        return not isinstance(self.obj, MissingValue)

    def is_array(self) -> bool:
        """Tests if the current node is an array."""
        return isinstance(self.obj, list)

    def is_object(self) -> bool:
        """Tests if the current node is an object (dictionary)."""
        return isinstance(self.obj, dict)

    def expect_present(self) -> Self:
        """Raises an error if the current node is a missing child. Returns itself."""
        if self.is_missing():
            self.raise_error('Mandatory key is missing')
        return self

    def as_type(self, typ: Type[T], msg: str, default: Optional[T] = None) -> T:
        if isinstance(self.obj, typ):
            return self.obj
        elif self.is_missing():
            if default is None:
                self.raise_error('Mandatory key is missing')
            else:
                return default
        else:
            self.raise_error(msg)

    def as_optional_type(self, typ: Type[T], msg: str) -> Optional[T]:
        if isinstance(self.obj, typ):
            return self.obj
        elif self.is_missing():
            return None
        else:
            self.raise_error(msg)

    def as_str(self, default: Optional[str] = None) -> str:
        """
            If the current node is a string, returns its value.
            If it is missing and *default* is given, returns *default*.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_type(str, 'Expected a string', default)

    def as_int(self, default: Optional[int] = None) -> int:
        """
            If the current node is an integer, returns its value.
            If it is missing and *default* is given, returns *default*.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_type(int, 'Expected an integer', default)

    def as_float(self, default: Optional[float] = None) -> float:
        """
            If the current node is a float, returns its value.
            If it is an integer, it is cast to a float.
            If it is missing and *default* is given, returns *default*.
            Otherwise raises :py:exc:`WalkerError`.
        """
        if isinstance(self.obj, int):
            return float(self.obj)
        else:
            return self.as_type(float, 'Expected a number', default)

    def as_bool(self, default: Optional[bool] = None) -> bool:
        """
            If the current node is a Boolean, returns its value.
            If it is missing and *default* is given, returns *default*.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_type(bool, 'Expected a Boolean value', default)

    def as_enum(self, enum: Type[E], default: Optional[E] = None) -> E:
        """
            If the current node is a string, returns its value
            cast to the given enumeration type (descendant of :py:class:`Enum`).
            If the node is missing and *default* is given, returns *default*.
            Otherwise raises :py:exc:`WalkerError`.
        """
        if self.is_missing() and default is not None:
            return default
        try:
            return enum(self.as_str())
        except ValueError:
            self.raise_error('Must be one of ' + '/'.join(sorted(enum.__members__.values())))  # FIXME: type

    def as_optional_str(self) -> Optional[str]:
        """
            If the current node is a string, returns its value.
            If it is missing, returns ``None``.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_optional_type(str, 'Expected a string')

    def as_optional_int(self) -> Optional[int]:
        """
            If the current node is an integer, returns its value.
            If it is missing, returns ``None``.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_optional_type(int, 'Expected an integer')

    def as_optional_float(self) -> Optional[float]:
        """
            If the current node is a float, returns its value.
            If it is an integer, it is cast to a float.
            If it is missing, returns ``None``.
            Otherwise raises :py:exc:`WalkerError`.
        """
        if isinstance(self.obj, int):
            return float(self.obj)
        else:
            return self.as_optional_type(float, 'Expected a number')

    def as_optional_bool(self) -> Optional[bool]:
        """
            If the current node is a Boolean, returns its value.
            If it is missing, returns ``None``.
            Otherwise raises :py:exc:`WalkerError`.
        """
        return self.as_optional_type(bool, 'Expected a Boolean value')

    def array_values(self) -> Iterator['WalkerInArray']:
        """
            Produces an iterator over an array node, which yields :py:class:`WalkerInArray`
            objects for the elements of the array.
            If the node is not an array, raises :py:exc:`WalkerError`.
        """
        ary = self.as_type(list, 'Expected an array')
        for i, obj in enumerate(ary):
            yield WalkerInArray(obj, self, i)

    def object_values(self) -> Iterator['WalkerInObject']:
        """
            Produces an iterator over attributes of an object (dictionary), which yields :py:class:`WalkerInObject`
            objects for the values of the attributes.
            If the node is not an object, raises :py:exc:`WalkerError`.
        """
        dct = self.as_type(dict, 'Expected an object')
        for key, obj in dct.items():
            yield WalkerInObject(obj, self, key)

    def object_items(self) -> Iterator[Tuple[str, 'WalkerInObject']]:
        """
            Produces an iterator over attributes of an object (dictionary), which yields pairs of the
            attribute's name and a :py:class:`WalkerInObject` object for the attribute's value.
            If the node is not an object, raises :py:exc:`WalkerError`.
        """
        dct = self.as_type(dict, 'Expected an object')
        for key, obj in dct.items():
            yield key, WalkerInObject(obj, self, key)

    def enter_object(self) -> 'ObjectWalker':
        """
            Produces an :py:class:`ObjectWalker` for an object (dictionary),
            which allows indexing of the object's attributes and checking which
            attributes are missing.
            If the node is not an object, raises :py:exc:`WalkerError`.
        """
        dct = self.as_type(dict, 'Expected an object')
        return ObjectWalker(dct, self)

    def default_to(self, default) -> 'Walker':    # XXX: Use Self when available
        """
            If the current node is missing, make the walker point to *default* instead.
            Returns itself, so it is possible to write e.g.
            ``walker.default_to([]).array_values()``.
        """
        if self.is_missing():
            self.obj = default
        return self

    def context(self) -> str:
        """Construct a path fragment for the current node."""
        return 'root'

    def set_custom_context(self, ctx: str) -> None:
        """Set a string that is appended to the path fragment returned by :py:meth:`context`."""
        self.custom_context = ctx


class WalkerInArray(Walker):
    """
        A :py:class:`Walker` referring to an array item.
        Never constructed directly, use :py:meth:`Walker.array_items` to obtain it.
    """

    index: int
    """Position of the item in the array (zero-based)."""

    def __init__(self, obj: Any, parent: Walker, index: int) -> None:
        super().__init__(obj)
        self.parent = parent
        self.index = index

    def context(self) -> str:
        return f'[{self.index}]'


class WalkerInObject(Walker):
    """
        A :py:class:`Walker` referring to an object attribute (dictionary item).
        Never constructed directly, use :py:meth:`Walker.object_values`,
        :py:meth:`Walker.object_items`, or indexing in :py:meth:`ObjectWalker`
        to obtain it.
    """

    key: str
    """Key of the attribute."""

    def __init__(self, obj: Any, parent: Walker, key: str) -> None:
        super().__init__(obj)
        self.parent = parent
        self.key = key

    def context(self) -> str:
        if re.fullmatch(r'\w+', self.key):
            return f'.{self.key}'
        else:
            quoted_key = re.sub(r'(\\|")', r'\\\1', self.key)
            return f'."{quoted_key}"'

    def unexpected(self) -> NoReturn:
        """Raises a :py:exc:`WalkerError` complaining that this key was not expected."""
        self.raise_error('Unexpected key')


class ObjectWalker(Walker):
    """
        A :py:class:`Walker` for inspecting an object (dictionary).
        In addition to the default walker, it allows indexing of attribute
        by the square brackets operator. It also remembers which attributes
        were referenced this way and when used as a context manager, it
        complains upon exit from the context if the object contains
        unreferenced attributes.

        Never constructed directly, use :py:meth:`Walker.enter_object`
        to obtain it.
    """

    referenced_keys: Set[str]
    """A set of keys of referenced attributes."""

    def __init__(self, obj: Any, parent: Walker) -> None:
        super().__init__(obj)
        assert isinstance(obj, dict)
        self.parent = parent
        self.referenced_keys = set()

    def __enter__(self) -> 'ObjectWalker':
        """Enter a context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit a context, calling :py:meth:`assert_no_other_keys`."""
        if exc_type is None:
            self.assert_no_other_keys()

    def context(self) -> str:
        return ""

    def __contains__(self, key: str) -> bool:
        """
            Implements the ``in`` operator for testing if the object contains an
            attribute with the given key.
        """
        return key in self.obj

    def __getitem__(self, key: str) -> WalkerInObject:
        """
            Implements the ``[]`` operator for accessing an attribute with
            the given key. Returns a :py:class:`WalkerInObject` referring to
            the attribute's value.
        """
        if key in self.obj:
            self.referenced_keys.add(key)
            return WalkerInObject(self.obj[key], self, key)
        else:
            return WalkerInObject(MissingValue(), self, key)

    def assert_no_other_keys(self) -> None:
        """
            Checks if the object has attributes not accessed by the ``[]``
            operator. Raises an :py:exc:`WalkerError` if there are any.
        """
        for key, val in self.obj.items():
            if key not in self.referenced_keys:
                WalkerInObject(val, self, key).unexpected()


class MissingValue:
    pass


class WalkerError(Exception):
    """An exception for any error occurring during walking the tree."""

    walker: Walker
    """
        The walker that raised the exception. Used to reconstruct the path
        to the erroneous node.
    """

    msg: str
    """Error message."""

    def __init__(self, walker: Walker, msg: str) -> None:
        self.walker = walker
        self.msg = msg

    def __str__(self) -> str:
        """Returns a string consisting of the path in the tree and the error message."""
        contexts = []
        w: Optional[Walker] = self.walker
        while w is not None:
            contexts.append(w.context())
            contexts.append(w.custom_context)
            w = w.parent
        return "".join(reversed(contexts)) + ": " + self.msg
