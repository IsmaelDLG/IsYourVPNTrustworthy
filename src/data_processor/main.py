from getopt import getopt
from sys import argv, stdout
import logging
from os import listdir, path, remove, sep
import time

from numpy import array2string
import objgraph

from config import _LOG_FILE, _LOG_FORMAT, _LOG_LEVEL, _LOAD_DATA, _DATA_DIRECTORY
from persistance.database_adapter import DatabaseAdapter
from persistance import Resource, Run, RunCollection

def _usage():
    """Usage method, executed when options -h, --help are passed or when an error occurs.
    """

    _logger.info("Usage: python3 {file} [-h|l|d <directory>]".format(file=__file__))

def _center(string: str, n: int) -> str:
    """Centers a string in a string of the length given in n parameter.
    """

    lstr = len(string)
    left_spaces = (n - lstr) // 2 if lstr < n else 0
    right_spaces = n - (left_spaces + lstr) if lstr < n else 0

    return " " * left_spaces + string + " " * right_spaces

def make_resource_collection_from_files(root_directory):
    """This method works as a generator. It uses yield, so that only one RunCollection is loaded at a time.
    """

    for ext in listdir(root_directory):
        ext_dir = root_directory + path.sep + ext
        if path.isdir(ext_dir):
            run_col = RunCollection(ext)
            # Extension directory
            for webpage in listdir(ext_dir):
                web_dir = ext_dir + path.sep + webpage
                # Webpage directory
                if path.isdir(web_dir):
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
                                _logger.debug(r)
                            _logger.debug(a_run)
                            run_col.append(a_run)
                        else:
                            # Trash file detected. It should be removed 
                            remove(run_dir)       
                else:
                    # Trash file detected. It should be removed
                    remove(web_dir)
            yield run_col
        else:
            # Trash file detected. It should be removed
            remove(ext_dir)
        

if __name__ == '__main__':
    file_handler = logging.FileHandler(_LOG_FILE, mode='a')
    file_handler.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(logging.DEBUG)

    handlers = [file_handler, stdout_handler, ]
    logging.basicConfig(handlers=handlers, format=_LOG_FORMAT)
    _logger = logging.getLogger(__name__)
    _logger.setLevel(_LOG_LEVEL)


    _logger.info("-"*50)
    _logger.info(_center("S t a r t i n g   u p", 50))
    _logger.info("-"*50)

    short_opts = "hld:"
    long_opts = ["help", "load", "directory="]

    try:
        opts, args = getopt(argv[1:], short_opts, long_opts)
    except Exception:
        _usage()
    
    for opt, arg in opts:
        if opt in ('-h', '--help') :
            _usage()
        elif opt in ('-l', '--load'):
            _LOAD_DATA = True
        elif opt in ('-d', '--directory'):
            if path.isdir(arg):
                _DATA_DIRECTORY = arg
                _logger.debug("Root directory to be used to load data changed to %s" % arg)
            else:
                _logger.error("Wrong path %s" % arg)
    
    db = DatabaseAdapter()        
    
    if _LOAD_DATA:
        _logger.debug("Loading files...")
        collections =  make_resource_collection_from_files(str(_DATA_DIRECTORY))
        try:
            for col in collections: 
                stored_collections = db.load_collections(names=[col.get_name(),], recursive=True)
                joined = False
                i = 0
                while not joined and i < len(stored_collections):
                    joined = stored_collections[i].join(col, compatible=True)
                    i += 1
                
                if not joined:
                    stored_collections.append(col)
            
                db.save_all(stored_collections)
        except MemoryError as e:
            _logger.exception(str(e))
            objgraph.show_most_common_types()
            objgraph.show_backrefs(random.choice(objgraph.by_type('Variety')), filename="Variety_refs.png")



            

