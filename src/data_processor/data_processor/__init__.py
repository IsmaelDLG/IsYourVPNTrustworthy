# uncompyle6 version 3.7.4
# Python bytecode 3.8 (3413)
# Decompiled from: Python 3.8.5 (tags/v3.8.5:580fbb0, Jul 20 2020, 15:43:08) [MSC v.1926 32 bit (Intel)]
# Embedded file name: B:\myRepos\AreVPNsAnonymus\src\data_processor\data_processor\__init__.py
# Compiled at: 2021-04-08 10:11:46
# Size of source mod 2**32: 3811 bytes
import logging
from time import time
from json import dump as jdump
import matplotlib.pyplot as plt
import numpy as np


from config import _RESULTS_DIRECTORY, _LOG_LEVEL


class DataProcessor:
    __doc__ = "This class takes care or processing data. It uses the database to do batch processing."

    def __init__(self, database):
        self._name = "DataProcessor_%.3f" % time()
        self._db = database

    

    def _calc_common_files(self, collection_name):
        """Internal function that calculates common files in a collection."""

        result = None
        try:
            a_collection = self._db.load_collections(
                collection_conditions=[("name =", collection_name)]
            )[0]
        except IndexError:
            raise RuntimeError("No RunCollection %s is not in the DB" % collection_name)
        else:
            list_of_runs = self._db.load_runs(
                run_conditions=[("collection_id =", a_collection.get_id())]
            )
            _logger.info(
                "Collection %r has the following runs: %r"
                % (a_collection, list_of_runs)
            )

            done = False
            i = 0
            while not done and i < len(list_of_runs):
                a_run = self._db.load_runs(
                    recursive=True, run_conditions=[("id =", list_of_runs[i].get_id())]
                )[0]
                if result is None:
                    result = a_run
                else:
                    # For some reason, some runs do not have stored resources. Avoid misleading mistakes with this check
                    if len(a_run) > 0:
                        result = result.intersection(a_run)

                if len(result) < 1:
                    done = True

                i += 1

            if not (result is None):
                result.set_name("CF_{0}".format(collection_name[:11]))
                id = self._db.save(result)
                if id > 0 and not (id is None):
                    result.set_id(id)

        return result

    def get_static_files_in_collection(self, collection_name, redo=False):
        """Gets static files (that are there in every run) for the given collection."""

        a_collection = None
        result = None
        if not redo:
            a_run = self._db.load_runs(
                recursive=True,
                run_conditions=[("name =", "CF_{0}".format(collection_name[0:11]))],
            )
            if not len(a_run) > 0:
                result = self._calc_common_files(collection_name)
            else:
                result = a_run[0]
                _logger.info(
                    "Using stored static files for collection %s" % collection_name
                )
        else:
            result = self._calc_common_files(collection_name)

        return result

    def common_files_batch(self, excluded=["Result_CF_01", "Result_DF_01"]):
        """Batch version to get all common files in all VPN extension.

        For each run, returns a run that represents the common files, generator-like.
        """

        conditions = [("name !=", x) for x in excluded]
        col_list = self._db.load_collections(
            recursive=False, collection_conditions=conditions
        )
        for col in col_list:
            _logger.debug(
                "Finding common files in collection {0}".format(col.get_name())
            )
            result = self.get_static_files_in_collection(col.get_name())
            if not (result is None):
                with open(
                    "{0}{1}_common_files_in_collection.json".format(
                        _RESULTS_DIRECTORY, col.get_name()
                    ),
                    "w",
                ) as f:
                    jdump(result.print(), f, indent=2)
                _logger.debug("Finished")
                yield result

    def different_files_batch(self, target="no_vpn", use_previous=True):
        """Batch version to get all different files in all VPN extensions from target.

        target is the name of the collection to perform the difference against.

        If use_previous is True, it attempts to use the CF_* collections to reduce computing time.
        """

        target = self.get_static_files_in_collection(target)
        cols = self._db.load_collections(
            recursive=False, collection_conditions=[("name NOT LIKE", "%Result%")]
        )
        for col in cols:
            other = self.get_static_files_in_collection(col.get_name())
            if not (other is None):
                aux = other.difference(target)
                aux.set_name("DF_{0}".format(col.get_name()[:11]))
                with open(
                    "{0}{1}_different_files_from_{2}.json".format(
                        _RESULTS_DIRECTORY, other.get_name()[3:], target.get_name()
                    ),
                    "w",
                ) as f:
                    jdump(aux.print(), f, indent=2)

                yield aux
    
    def get_metadata(self, name):
        """Gets metadata from the specified RunCollection."""
        
        col = None
        try:
            col = self._db.load_collections(recursive=False, collection_conditions=[("name =", name),], run_conditions=[] )[0]

            runs = self._db.load_runs(recursive=False, run_conditions=[("collection_id =", col.get_id())])
            col.extend(runs)

            for run in col:
                res = self._db.load_resources_major(recursive=False, resource_conditions=[("run_id =", run.get_id())])
                run.extend(res)

        except:
            raise RuntimeError("Collection %s could not be loaded from DB" % name)

        min = col.min_resources_per_run()
        max = col.max_resources_per_run()
        avg = col.avg_resources_per_run()

        return min, max, avg
        
    
    def metadata_batch(self, excluded=["Result_CF_01", "Result_DF_01"]):
        
        conditions = [("name !=", x) for x in excluded]
        col_list = self._db.load_collections(
            recursive=False, collection_conditions=conditions
        )
        min_list = []
        max_list = []
        avg_list = []
        name_list = []
        for col in col_list:
            _logger.info("Processing col %s" % col.get_name())
            min, max, avg = self.get_metadata(col.get_name())

            yield col.get_name(), [min, max, avg]

    


_logger = logging.getLogger(__name__)
_logger.setLevel(_LOG_LEVEL)

if __name__ == "__main__":
    db = DatabaseAdapter()
    dp = data_processor.DataProcessor(db)
