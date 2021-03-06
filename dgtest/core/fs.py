import glob
import pathlib
from typing import List, Optional, Tuple

import git


def get_changed_files(branch: Optional[str]) -> Tuple[List[str], List[str]]:
    """Perform `git diff HEAD <branch> --name-only` to retrieve a list of files that have changed in the last commit

    Args:
        branch: The git branch to diff against

    Returns:
        A tuple contain changed source files and changed test files.
        These files must end in .py and should still existing in the current codebase.

    """
    repo = git.Repo()

    # Collected any modified files (both staged and unstaged)
    local_diff = repo.git.diff("HEAD", name_only=True)
    files = [f.strip() for f in local_diff.split("\n")]

    # Diff against a particular branch (if applicable)
    if branch:
        branch_diff = repo.git.diff(branch, name_only=True)
        files += [f.strip() for f in branch_diff.split("\n") if f not in files]

    changed_source_files = _filter_source_files(files)
    changed_test_files = _filter_test_files(files)
    return changed_source_files, changed_test_files


def retrieve_all_source_files(source: str) -> List[str]:
    """Utility to aggregate all source files for future processing

    Args:
        source: The relative path to your source directory

    Returns:
        A list of existing Python files from your source directory

    """
    all_files = _retrieve_all_py_files(source)
    source_files = _filter_source_files(all_files)
    return source_files


def retrieve_all_test_files(source: str, tests: Optional[str]) -> List[str]:
    """Utility to aggregate all test files for future processing

    Note that the tests argument is optional because some users keep their tests
    alongside their source code. If an external tests directory is relevant to the
    given codebase, it must explicitly be passed along here.

    Args:
        source: The relative path to your source directory
        tests: The relative path to your tests directory (if applicable)

    Returns:
        A list of existing Python tests files from the provided directories

    """
    all_files = _retrieve_all_py_files(source)
    if tests is not None:
        all_files += _retrieve_all_py_files(tests)

    test_files = _filter_test_files(all_files)
    return test_files


def _retrieve_all_py_files(directory: str) -> List[str]:
    return [file for file in glob.glob(f"{directory}/**/*.py", recursive=True)]


def _filter_source_files(files: List[str]) -> List[str]:
    source_files = []
    for file in files:
        path = pathlib.Path(file)
        if not _is_existing_py_file(path):
            continue
        stem = path.stem
        if not (stem == "conftest" or path.stem.startswith("test_")):
            source_files.append(str(path))
    return sorted(source_files)


def _filter_test_files(files: List[str]) -> List[str]:
    test_files = []
    for file in files:
        path = pathlib.Path(file)
        if not _is_existing_py_file(path):
            continue
        stem = path.stem
        if stem == "conftest" or stem.startswith("test_"):
            test_files.append(str(path))
    return sorted(test_files)


def _is_existing_py_file(path: pathlib.Path) -> bool:
    return path.is_file() and path.suffix == ".py"
