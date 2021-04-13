import logging
from sys import stdout


from persistance.database_adapter import DatabaseAdapter
from config import (
    _LOG_FILE,
    _LOG_FORMAT,
    _LOG_LEVEL,
    _LOAD_DATA,
    _DATA_DIRECTORY,
    _RESULTS_DIRECTORY,
)


def _center(string: str, n: int) -> str:
    """Centers a string in a string of the length given in n parameter."""

    lstr = len(string)
    left_spaces = (n - lstr) // 2 if lstr < n else 0
    right_spaces = n - (left_spaces + lstr) if lstr < n else 0

    return " " * left_spaces + string + " " * right_spaces


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

short_opts = "hld:"
long_opts = ["help", "load", "directory="]

db = DatabaseAdapter()
cursor = db._db.conn.cursor()
cursor.execute(
    'SELECT Table_name FROM information_schema.tables WHERE table_schema = "vpntfg0" AND Table_name LIKE "%Varieties%"'
)
_logger.debug(cursor.fetchall())
for i in range(1, 9):
    _logger.debug("Starting with Varieties_{0}".format(i))
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Varieties_{0} (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            resource_id INT NOT NULL REFERENCES Resources(id), 
            name VARCHAR(40), 
            hash VARCHAR(10000), 
            content MEDIUMBLOB
        );""".format(
            i
        )
    )

    cursor.execute(
        """INSERT INTO Varieties_{0} (SELECT * FROM Varieties WHERE resource_id >= {1} AND resource_id < {2});""".format(
            i, (i - 1) * 50000, i * 50000
        )
    )
    _logger.debug("Finished with Varieties_{0}".format(i))
    # cursor.execute("""DELETE FROM Varieties WHERE resource_id >= {1} AND resource_id < {2};""".format((i-1)* 50000, i*50000))
    db._db.conn.commit()

cursor.close()

##################################################################


def _get_dir_list(a_directory):
    result = []
    files = listdir(a_directory)
    for f in files:
        if path.isdir(f):
            result.append(f)
    return result


def resource_collection_generator(root_directory):
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
                                full_path.append(
                                    (ext, run, webpage, run_dir + path.sep + file)
                                )

    col = None
    for ext, run, webpage, filepath in full_path_list:
        if col is None:
            col = ResourceCollection(ext)
        elif ext != col.get_name():
            yield col
            col = ResourceCollection(ext)

        i_run = col.find(run)

        if i_run is None:
            col.append(Run(run))
            i_run = len(col) - 1

        a_res = Resource(ext, webpage, filepath)

        i_res = col[i_run].find_similar(a_res)
        if not (i_res is None):
            aux = col[i_run][i_res]
            aux.add_varieties(res.varieties)
            col[i_run][i_res] = aux
        else:
            col[i_run].append(res)

        if getsizeof(col) >= _MAX_RELATIVE_BATCH_SIZE:
            yield col
            col = None
