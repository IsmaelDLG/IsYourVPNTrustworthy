from getopt import getopt
from sys import argv, stdout, getsizeof
import logging
from os import listdir, path, remove, sep
import time
import random
from gc import collect as gc_collect

from numpy import array2string

from config import _LOG_FILE, _LOG_FORMAT, _LOG_LEVEL, _LOAD_DATA, _DATA_DIRECTORY
from persistance.database_adapter import DatabaseAdapter
from persistance import Resource, Run, RunCollection


def _usage():
    """Usage method, executed when options -h, --help are passed or when an error occurs."""

    _logger.info("Usage: python3 {file} [-h|l|d <directory>]".format(file=__file__))


def _center(string: str, n: int) -> str:
    """Centers a string in a string of the length given in n parameter."""

    lstr = len(string)
    left_spaces = (n - lstr) // 2 if lstr < n else 0
    right_spaces = n - (left_spaces + lstr) if lstr < n else 0

    return " " * left_spaces + string + " " * right_spaces


def ResourceCollectionGenerator(root_directory):
    for ext in listdir(root_directory):
        ext_dir = root_directory + path.sep + ext
        if path.isdir(ext_dir):
            # Extension Directory
            for webpage in listdir(ext_dir):
                web_dir = ext_dir + path.sep + webpage
                if path.isdir(web_dir):
                    # Webpage directory
                    # We create collections from here, for the
                    # size of the Collection will be smaller and
                    # easier to treat
                    current_collection = RunCollection(ext)

                    for run in listdir(web_dir):
                        run_dir = web_dir + path.sep + run
                        if path.isdir(run_dir):
                            a_run = Run(run)
                            for file in listdir(run_dir):
                                r = Resource(ext, webpage, run_dir + path.sep + file)
                                index = a_run.find_similar(r)
                                if not (index is None):
                                    aux = a_run[index]
                                    aux.add_varieties(r.varieties)
                                    a_run[index] = aux
                                else:
                                    a_run.append(r)
                                # _logger.debug(r)
                                del r
                            # _logger.debug(a_run)
                            current_collection.append(a_run)
                            del a_run
                        else:
                            # Trash file detected. It should be removed
                            remove(run_dir)

                    _logger.debug(
                        "Element %r returned with size %i"
                        % (current_collection, getsizeof(current_collection))
                    )
                    yield current_collection
                    del current_collection
                else:
                    # Trash file detected. It should be removed
                    remove(web_dir)
        else:
            # Trash file detected. It should be removed
            remove(ext_dir)


if __name__ == "__main__":
    file_handler = logging.FileHandler(_LOG_FILE, mode="a")
    file_handler.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(logging.DEBUG)

    handlers = [
        file_handler,
        stdout_handler,
    ]
    logging.basicConfig(handlers=handlers, format=_LOG_FORMAT)
    _logger = logging.getLogger(__name__)
    _logger.setLevel(_LOG_LEVEL)

    _logger.info("-" * 50)
    _logger.info(_center("S t a r t i n g   u p", 50))
    _logger.info("-" * 50)

    short_opts = "hld:"
    long_opts = ["help", "load", "directory="]

    try:
        opts, args = getopt(argv[1:], short_opts, long_opts)
    except Exception:
        _usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            _usage()
        elif opt in ("-l", "--load"):
            _LOAD_DATA = True
        elif opt in ("-d", "--directory"):
            if path.isdir(arg):
                _DATA_DIRECTORY = arg
                _logger.debug(
                    "Root directory to be used to load data changed to %s" % arg
                )
            else:
                _logger.error("Wrong path %s" % arg)

    db = DatabaseAdapter()

    if _LOAD_DATA:
        _logger.debug("Loading files...")
        collections = ResourceCollectionGenerator(str(_DATA_DIRECTORY))
        try:
            for col in collections:
                col_joined = False
                stored_collections = db.load_collections(
                    recursive=False,
                    collection_conditions=[
                        ("name =", col.get_name()),
                    ],
                )
                for st_col in stored_collections:
                    _logger.debug("Attempt to join %r and %r" % (st_col, col))
                    if st_col.can_join(col):
                        _logger.debug(
                            "%r and %r can join. Trying to find matching runs"
                            % (st_col, col)
                        )
                        for run in col:
                            run_joined = False
                            stored_runs = db.load_runs(
                                recursive=False,
                                run_conditions=[
                                    ("name =", run.get_name()),
                                    ("collection_id =", st_col.get_id()),
                                ],
                            )
                            _logger.debug("Candidates are: %r" % stored_runs)
                            for st_run in stored_runs:
                                if st_run.can_join(run):
                                    _logger.debug(
                                        "Runs %r and %r can join. Merging runs!"
                                        % (st_run, run)
                                    )
                                    # Load one unique run using primary key
                                    to_merge = db.load_runs(
                                        recursive=True,
                                        run_conditions=[
                                            ("id =", st_run.get_id()),
                                            ("collection_id =", st_col.get_id()),
                                        ],
                                    )[0]

                                    to_merge.join(run)
                                    db.save(to_merge, parent_id=st_col.get_id())
                                    run_joined = True
                                    _logger.debug("Joined %r and %r!" % (to_merge, run))
                                    break

                            if not run_joined:
                                _logger.debug(
                                    "Could not join with any run! Saving %r." % run
                                )
                                db.save(run, parent_id=st_col.get_id())
                        col_joined = True
                        _logger.debug("Joined %r and %r!" % (st_col, col))
                        break
                    else:
                        _logger.debug("Can not join!")

                if not col_joined:
                    db.save(col)
                    _logger.debug("%r Unique, adding to database." % col)

                gc_collect()

        except MemoryError as e:
            _logger.exception(str(e))
