from typing import Optional, Tuple

import click

from dgtest.fs import get_changed_files
from dgtest.graph import determine_tests_to_run, prettify_graphs
from dgtest.parse import get_dependency_graphs


@click.group()
def cli() -> None:
    pass


@cli.command(help="Run dependency graph test runner")
@click.option(
    "-t",
    "--tests",
    "tests",
    help="The relative path to your tests directory (if applicable)",
    type=click.Path(exists=True),
)
@click.option(
    "-d",
    "--depth",
    "depth",
    help="The desired maximum depth of the graph traversal algorithm",
    default=3,
    type=int,
)
@click.option(
    "-i",
    "--ignore",
    "ignore_paths",
    help="Exclude results that begin with any provided path prefix",
    type=click.Path(),
    multiple=True,
)
@click.option(
    "-f",
    "--filter",
    "filter_",
    help="Filter results to only include those that being with the provided path prefix",
    type=click.Path(),
)
@click.option(
    "-b",
    "--branch",
    "branch",
    help="The specific branch to diff against",
    default="origin/develop",
    type=str,
)
@click.argument("source", type=click.Path(exists=True))
def run(
    source: str,
    tests: Optional[str],
    depth: int,
    ignore_paths: Tuple[str],
    filter_: Optional[str],
    branch: str,
) -> None:
    """Command used to run dependency graph test strategy on a target codebase.

    Args:
        source: The relative path to your source directory
        tests: The relative path to your tests directory
        depth: The depth of the graph traversal (the larger the number, the greater the coverage but the smaller the specificity)
        ignore_paths: Any test files that starts with any paths in this collection are ignored in the output
        filter_: Only test paths that start with this value are included in the output
        branch: The specific branch to diff against to determine changed files

    Returns:
        Prints a list of '\n'-delimited test file names

    """
    changed_source_files, changed_test_files = get_changed_files(branch)
    source_dependency_graph, tests_dependency_graph = get_dependency_graphs(
        source, tests
    )
    files_to_test = determine_tests_to_run(
        changed_source_files,
        changed_test_files,
        source_dependency_graph,
        tests_dependency_graph,
        depth,
        ignore_paths,
        filter_,
    )

    for file in files_to_test:
        click.echo(file)


@cli.command(help="Print dependency graphs")
@click.option(
    "-t",
    "--tests",
    "tests",
    help="The relative path to your tests directory (if applicable)",
    type=click.Path(exists=True),
)
@click.argument("source", type=click.Path(exists=True))
def graph(
    source: str,
    tests: Optional[str],
) -> None:
    """Command used to print out source/test dependency graphs to STDOUT

    Args:
        source: The relative path to your source directory
        tests: The relative path to your tests directory

    Returns:
        Prints a formatted, prettified version of the source and tests dependency graphs

    """
    source_dependency_graph, tests_dependency_graph = get_dependency_graphs(
        source, tests
    )

    stringified_graph = prettify_graphs(
        ("Source Dependency Graph", source_dependency_graph),
        ("Tests Dependency Graph", tests_dependency_graph),
    )

    click.echo(stringified_graph)
