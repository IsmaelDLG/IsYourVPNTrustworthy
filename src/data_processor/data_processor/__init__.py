import logging
from time import time


class DataProcessor:
    """This class takes care or processing data. It uses the database to do batch processing."""

    def __init__(self, database):
        self._name = "DataProcessor_%.3f" % time()
        self._db = database

    def get_metadata(self):
        """Gets metadata from the different RunCollections present in the database."""
        pass


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
