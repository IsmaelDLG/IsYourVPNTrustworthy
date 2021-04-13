from getopt import getopt
from sys import argv, stdout, getsizeof
import logging
from os import listdir, path, remove, sep
import time
import random
from gc import collect as gc_collect
from json import dump as jdump

from numpy import array2string

from config import (
    _LOG_FILE,
    _LOG_FORMAT,
    _LOG_LEVEL,
    _LOAD_DATA,
    _PROCESS_DATA,
    _DATA_DIRECTORY,
    _RESULTS_DIRECTORY,
    _MAX_RELATIVE_BATCH_SIZE,
)
from persistance.database_adapter import DatabaseAdapter
from persistance import Resource, Run, RunCollection
import data_processor


def _usage():
    """Usage method, executed when options -h, --help are passed or when an error occurs."""

    _logger.info("Usage: python3 {file} [-h|l|d <directory>]".format(file=__file__))


def _center(string: str, n: int) -> str:
    """Centers a string in a string of the length given in n parameter."""

    lstr = len(string)
    left_spaces = (n - lstr) // 2 if lstr < n else 0
    right_spaces = n - (left_spaces + lstr) if lstr < n else 0

    return " " * left_spaces + string + " " * right_spaces


def resource_collection_generator(root_directory):
    """A Generator method that splits all the files to save into the database in an iterable, that makes sure
    everything is well categorized (RunCollection) and that the size of the object created in memory is not too
    big.
    """

    full_path_list = []

    for ext in listdir(root_directory):
        ext_dir = root_directory + path.sep + ext
        if path.isdir(ext_dir):
            # Extension Directory
            for webpage in listdir(ext_dir):
                web_dir = ext_dir + path.sep + webpage
                if path.isdir(web_dir):
                    for run in listdir(web_dir):
                        run_dir = web_dir + path.sep + run
                        if path.isdir(run_dir):
                            for file in listdir(run_dir):
                                full_path_list.append(
                                    (ext, run, webpage, run_dir + path.sep + file)
                                )

    col = None
    for ext, run, webpage, filepath in full_path_list:
        if col is None:
            col = RunCollection(ext)
        elif ext != col.get_name():
            yield col
            col = RunCollection(ext)

        i_run = col.find(run)

        if i_run is None:
            col.append(Run(run))
            i_run = len(col) - 1

        a_res = Resource(ext, webpage, filepath)

        i_res = col[i_run].find_similar(a_res)
        if not (i_res is None):
            aux = col[i_run][i_res]
            aux.add_varieties(a_res.varieties)
            col[i_run][i_res] = aux
        else:
            col[i_run].append(a_res)

        # getsizeof gives an indication of how much memory the collection requires
        if getsizeof(col) >= _MAX_RELATIVE_BATCH_SIZE:
            yield col
            col = None


def load_files_in_database(db):
    _logger.info("Loading files...")
    collections = resource_collection_generator(str(_DATA_DIRECTORY))
    for col in collections:
        _logger.info("Finding a match for: %r" % col)

        db_col = db.find_matching_collection(col)

        if not (db_col is None):
            for run in col:
                _logger.info("Finding a match for: %r" % run)
                db_run = db.find_matching_run(run, col_id=db_col.get_id())
                if not (db_run is None):
                    _logger.info("Found. Joining runs.")
                    db_run = db.find_matching_run(
                        run, col_id=db_col.get_id(), recursive=True
                    )
                    changes = db_run.join(run, compatible=True)
                    if changes:

                        db.save(db_run, parent_id=db_col.get_id())
                else:
                    _logger.info("Not found. Saving new run")
                    db.save(run, parent_id=db_col.get_id())
        else:
            _logger.info("Match not found for: %r. Saving new collection" % col)
            db.save(col)

        gc_collect()


if __name__ == "__main__":
    file_handler = logging.FileHandler(_LOG_FILE, mode="w")
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

    short_opts = "hld:p"
    long_opts = ["help", "load", "directory=", "process"]

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
                _logger.info(
                    "Root directory to be used to load data changed to %s" % arg
                )
            else:
                _logger.error("Wrong path %s" % arg)
        elif opt in ("-p", "--process"):
            _PROCESS_DATA = True

    db = DatabaseAdapter()

    if _LOAD_DATA:
        load_files_in_database(db)
        _logger.info("Finished loading files into DB")

    if _PROCESS_DATA:
        dp = data_processor.DataProcessor(db)

        # intersection_list = dp.common_files_batch(excluded= ["no_vpn", "Result_", "1click", "adguard", "astard", "betternet", "browsec"])
        intersection_list = dp.common_files_batch()
        dp.save_partial_result_as_collection("Result_CF_01", intersection_list)

        _logger.info("Finding diffenrent files in all collections from no_vpn")

        difference_list = dp.different_files_batch()
        dp.save_partial_result_as_collection("Result_DF_01", difference_list)
