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

    def get_static_files_in_collection(self, collection_name):
        """Gets static files (that are there in every run) for the given collection.
        
        We use batch processing for the datasets are too big."""

        a_collection = None
        try:
            a_collection = self._db.load_collections(collection_conditions=[("name =", collection_name)]
            )[0]
        except IndexError:
            raise RuntimeError("No RunCollection %s is not in the DB" % collection_name)
        
        list_of_runs = self._db.load_runs(run_conditions=[("collection_id =", a_collection.get_id())])
        _logger.debug("Collection %r has the following runs: %r" % (a_collection, list_of_runs))
        result = None
        for run in list_of_runs:
            # Using primary key only returns 1 Run object
            a_run = self._db.load_runs(
                recursive = True,
                run_conditions=[("id =", run.get_id())],
            )[0]
            
            _logger.debug("Processing %r" % a_run)

            if (result is None):
                result = a_run
            else:
                result = result.intersection(a_run)

        return result


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
