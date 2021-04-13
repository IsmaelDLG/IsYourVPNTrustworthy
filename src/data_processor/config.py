from logging import INFO, DEBUG
from pathlib import Path

_DB_HOSTNAME = "192.168.1.60"
_DB_USER = "win10_desktop"
_DB_PASSWORD = "1234"
_DB_DATABASE = "vpntfg0"

_DATA_DIRECTORY = Path(r"C:\Users\ismae\Downloads\test").resolve()
_LOAD_DATA = False
_PROCESS_DATA = False

_LOG_FILE = "data_processor.log"
_LOG_FORMAT = "%(asctime)s|%(threadName)s|%(name)s|%(levelname)s|%(message)s"
_LOG_LEVEL = INFO

_RESULTS_DIRECTORY = "C:\\Users\\ismae\\Desktop\\Results\\130421\\"

# Tells the number of different resources that can be referenced in the varieties table.
# For example, Varieties_1 can reference id [0, _VARIETIESIZE), Varieties_2 [_VARIETIES_SIZE, 2*_VARIETIES_SIZE] from Resources table.

_VARIETIES_SIZE = 50000

_MAX_RELATIVE_BATCH_SIZE = 400000
