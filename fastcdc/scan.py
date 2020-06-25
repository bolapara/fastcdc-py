# -*- coding: utf-8 -*-
import hashlib
import os
from typing import List
from humanize import intcomma, naturalsize
import click
from codetiming import Timer

import fastcdc
from fastcdc.utils import DefaultHelp, iter_files, supported_hashes


@click.command(cls=DefaultHelp)
@click.argument(
    "path", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "-r", "--recursive", help="Scan directory tree recursively.", is_flag=True,
)
@click.option(
    "-s",
    "--size",
    type=click.INT,
    default=16384,
    help="The desired average size of the chunks.",
    show_default=True,
)
@click.option(
    "-mi", "--min-size", type=click.INT, help="Minimum chunk size (default size/4)"
)
@click.option(
    "-ma", "--max-size", type=click.INT, help="Maximum chunk size (default size*8)"
)
@click.option(
    "-hf", "--hash-function", type=click.STRING, default="sha256", show_default=True
)
def scan(path, recursive, size, min_size, max_size, hash_function):
    """Scan files in directory and report duplication."""
    if min_size is None:
        min_size = size // 4
    if max_size is None:
        max_size = size * 8

    bytes_total = 0
    bytes_dupe = 0
    fingerprints = set()
    supported = supported_hashes()
    if hash_function not in supported:
        msg = "'{}' is not a supported hash.\nTry one of these:\n{}".format(
            hash_function, ", ".join(supported)
        )
        raise click.BadOptionUsage("hf", msg)

    hf = getattr(hashlib, hash_function)
    files: List[os.DirEntry]
    files = list(iter_files(path, recursive))
    t = Timer("scan", logger=None)
    t.start()
    with click.progressbar(files) as pgbar:
        for entry in pgbar:
            chunker = fastcdc.fastcdc(entry.path, min_size, size, max_size, hf=hf)
            for chunk in chunker:
                bytes_total += chunk.length
                if chunk.hash in fingerprints:
                    bytes_dupe += chunk.length
                fingerprints.add(chunk.hash)
    t.stop()
    data_per_s = bytes_total / Timer.timers.mean("scan")
    click.echo("Files:          {}".format(intcomma(len(files))))
    click.echo(
        "Chunk Sizes:    min {} - avg {} - max {}".format(min_size, size, max_size)
    )
    click.echo("Unique Chunks:  {}".format(intcomma(len(fingerprints))))
    click.echo("Total Data:     {}".format(naturalsize(bytes_total)))
    click.echo("Dupe Data:      {}".format(naturalsize(bytes_dupe)))
    click.echo("Throughput:     {}/s".format(naturalsize(data_per_s)))


if __name__ == "__main__":
    scan()