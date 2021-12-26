import py

from dgtest.parse import (
    parse_definition_nodes_from_codebase,
    parse_definition_nodes_from_file,
    parse_import_nodes_from_codebase,
    parse_import_nodes_from_file,
    update_dict,
)


def test_parse_definition_nodes_from_file_collects_function_definitions(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")

    my_file1.write(
        """
def my_first_func():
    pass

def my_second_func():
    pass
    """
    )

    file_definition_map = parse_definition_nodes_from_file(my_file1.strpath)

    assert len(file_definition_map) == 2
    assert (
        isinstance(file_definition_map["my_first_func"], set)
        and len(file_definition_map["my_first_func"]) == 1
    )
    assert (
        isinstance(file_definition_map["my_second_func"], set)
        and len(file_definition_map["my_second_func"]) == 1
    )


def test_parse_definition_nodes_from_file_collects_class_definitions(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")

    my_file1.write(
        """
class Bar:
    pass

class Baz:
    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b
    """
    )

    definition_map = parse_definition_nodes_from_file(my_file1.strpath)

    assert len(definition_map) == 2
    assert (
        isinstance(definition_map["Bar"], set)
        and my_file1.strpath in definition_map["Bar"]
    )
    assert (
        isinstance(definition_map["Baz"], set)
        and my_file1.strpath in definition_map["Baz"]
    )


def test_parse_definition_nodes_from_codebase_accounts_for_namespace_collision(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")
    my_file1.write(
        """
class my_file1:
    pass
    """
    )
    my_file2 = my_dir.join("bar.py")
    my_file2.write(
        """
class my_file1:
    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b
    """
    )

    definition_map = parse_definition_nodes_from_codebase(
        [my_file1.strpath, my_file2.strpath]
    )

    assert len(definition_map) == 1
    assert (
        isinstance(definition_map["my_file1"], set) and len(definition_map["Foo"]) == 2
    )


def test_parse_import_nodes_from_file_with_no_relative_imports(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")
    my_file1.write(
        """
import copy
import datetime
import json
import logging
import os
from typing import Dict, List, Optional, Union
from uuid import UUID
    """
    )

    imports = parse_import_nodes_from_file(my_file1.strpath, "great_expectations", {})
    assert imports == set()


def test_parse_import_nodes_from_file_with_relative_imports(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")
    my_file1.write(
        """
from my_package.util import my_first_func
from my_package.core import MyClass
from my_package.core.util import my_second_func, my_third_func
    """
    )

    definition_map = {
        "my_first_func": {"my_package/util/file.py"},
        "MyClass": {"my_package/core/my_class.py"},
        "my_second_func": {"my_package/core/util.py"},
        "my_third_func": {"my_package/core/util.py"},
    }

    imports = parse_import_nodes_from_file(
        my_file1.strpath, "my_package", definition_map
    )
    assert len(imports) == 3
    assert all(
        path in imports
        for path in (
            "my_package/util/file.py",
            "my_package/core/my_class.py",
            "my_package/core/util.py",
        )
    )


def test_parse_import_nodes_from_file_with_ambiguous_imports(
    tmpdir: py.path.local,
) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")
    my_file1.write(
        """
from my_package.util import my_first_func
    """
    )

    # Namespace collision means we need to pick the closest import
    definition_map = {
        "my_first_func": {"my_package/util/file.py", "my_package/core/file.py"},
    }

    imports = parse_import_nodes_from_file(
        my_file1.strpath, "my_package", definition_map
    )
    assert len(imports) == 1

    # The import statement included "util" so we pick the first option
    assert "my_package/util/file.py" in imports
    assert "my_package/core/file.py" not in imports


def test_parse_import_nodes_from_codebase(tmpdir: py.path.local) -> None:
    my_dir = tmpdir.mkdir("my_dir")
    my_file1 = my_dir.join("foo.py")
    my_file2 = my_dir.join("bar.py")

    my_file1.write(
        """
import copy
import datetime
import json
import logging

from my_package.core import MyClass
from my_package.util import my_first_func
    """
    )
    my_file2.write(
        """
import pandas as pd
import numpy as np
import os

from my_package.core import MyClass
from my_package.core.util import my_second_func, my_third_func
    """
    )

    definition_map = {
        "my_first_func": {"my_package/util/file.py"},
        "MyClass": {"my_package/core/my_class.py"},
        "my_second_func": {"my_package/core/util.py"},
        "my_third_func": {"my_package/core/util.py"},
    }

    imports = parse_import_nodes_from_codebase(
        [my_file1.strpath, my_file2.strpath], "my_package", definition_map
    )
    assert len(imports) == 2
    assert imports[my_file1.strpath] == {
        "my_package/util/file.py",
        "my_package/core/my_class.py",
    }
    assert imports[my_file2.strpath] == {
        "my_package/core/util.py",
        "my_package/core/my_class.py",
    }


def test_parse_pytest_fixtures_from_file() -> None:
    pass  # TBD


def test_parse_pytest_fixtures_from_codebase() -> None:
    pass  # TBD


def test_update_dict_updates_existing_keys() -> None:
    A = {"my_file1": {"a", "b", "c"}}
    B = {"my_file1": {"c", "d", "e"}}

    update_dict(A, B)

    assert len(A) == 1
    assert all(num in A["my_file1"] for num in ("a", "b", "c", "d", "e"))


def test_update_dict_adds_new_keys() -> None:
    A = {"my_file1": {"a", "b", "c"}}
    B = {"bar": {"c", "d", "e"}}

    update_dict(A, B)

    assert len(A) == 2
    assert all(num in A["my_file1"] for num in ("a", "b", "c"))
    assert all(num in A["bar"] for num in ("c", "d", "e"))