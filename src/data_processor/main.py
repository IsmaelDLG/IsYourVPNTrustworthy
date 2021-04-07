from getopt import getopt
from sys import argv, stdout, getsizeof
import logging
from os import listdir, path, remove, sep
import time
import random
from gc import collect as gc_collect
from json import dump as jdump

from numpy import array2string

from config import _LOG_FILE, _LOG_FORMAT, _LOG_LEVEL, _LOAD_DATA, _DATA_DIRECTORY, _RESULTS_DIRECTORY
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


def load_files_in_database(db):
    _logger.debug("Loading files...")
    collections = resource_collection_generator(str(_DATA_DIRECTORY))
    for col in collections:
        _logger.debug("Finding a match for: %r" % col)
        db_col = db.find_matching_collection(col)

        if not (db_col is None):
            for run in col:
                db_run = db.find_matching_run(run, col_id=db_col.get_id())
                if not (db_run is None):
                    db_run = db_run[0]
                    for resource in run:
                        db_resource = db.find_matching_resource(
                            resource, run_id=db_run.get_id()
                        )
                        if not (db_resource is None):
                            index = 0
                            max_sim = 0
                            best_one = None
                            while index < len(db_resource):
                                sim = db_resource[index].compare(resource)
                                if sim >= max_sim:
                                    max_sim = sim
                                    best_one = db_resource[index]
                                index += 1

                            # Found best match.
                            best_one.join(resource)
                            db.save(best_one)
                            _logger.debug("Joining resources")
                        else:
                            db.save(resource)
                            _logger.debug("Saving new resource")
                else:
                    db.save(run)
                    _logger.debug("Saving new run")
        else:
            _logger.debug("Match not found for: %r. Saving." % col)
            db.save(col)

        gc_collect()


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
        load_files_in_database(db)

    dp = data_processor.DataProcessor(db)

    col_list = db.load_collections(recursive=False, collection_conditions=[("name !=", "no_vpn")])
    intersection_list = []
    # Try to find files common in all VPN runs, that are specific files. We can later compare these 
    # to the files common in all vpns to find which are only used by a specific VPN.

    for col in col_list:
        _logger.debug("Finding common files in collection {0}".format(col.get_name()))
        result = dp.get_static_files_in_collection(col.get_name())
        intersection_list.append(result)
        with open("{0}{1}.json".format(_RESULTS_DIRECTORY, col.get_name()), 'w') as f:
            jdump(result.print(), f)
        _logger.debug("Finished")

    # Try to find files common in all VPN, that are VPN-related files
    _logger.debug("Finding common in all collections".format(col.get_name()))
    common = RunCollection("VPNCommonFiles", data=intersection_list)
    result = common.constant_resources()
    with open("{0}{1}.json".format(_RESULTS_DIRECTORY, common.get_name()), 'w') as f:
            jdump(result.print(), f)
    _logger.debug("Finished")

    try:
        debug = dp.get_static_files_in_collection("no_vpn")
    except RuntimeError:
        _logger.error("Collection no_vpn does not exists in  the database.")
    else:
        with open("{0}{1}.json".format(_RESULTS_DIRECTORY, "StaticFilesInNoVPN"), 'w') as f:
            jdump(debug.print(), f)
    
