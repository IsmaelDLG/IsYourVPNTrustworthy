from logging import INFO, DEBUG
from pathlib import Path

_DB_HOSTNAME = "192.168.1.60"
_DB_USER = "win10_desktop"
_DB_PASSWORD = "1234"
_DB_DATABASE = "vpntfg0"

_DATA_DIRECTORY = Path(r"C:\Users\ismae\Downloads\test").resolve()
_LOAD_DATA = False

_LOG_FILE = "data_processor.log"
_JOURNAL_FILE = "journal.log"
_LOG_FORMAT = "%(asctime)s|%(threadName)s|%(name)s|%(levelname)s|%(message)s"
#_LOG_LEVEL = INFO
_LOG_LEVEL = DEBUG

_RESULTS_DIRECTORY = "C:\\Users\\ismae\\Desktop\\"