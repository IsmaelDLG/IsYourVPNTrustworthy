import logging
from time import sleep

from mysql import connector
from numpy import array, array2string
from numpy import uint64

from config import _DB_DATABASE, _DB_HOSTNAME, _DB_PASSWORD, _DB_USER
from persistance import Resource, Run, RunCollection


class Database:
    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db = db_name
        self.conn = connector.connect(
            host=host, user=user, passwd=password, db="vpntfg0"
        )

    def close(self):
        """Closes the connection to the database."""

        self.conn.close()

    def initialize(self):
        """Initializes the database, creating tables if needed."""

        cursor = self.conn.cursor()

        # This table can be used as a parent for a collection of runs
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS RunCollections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(14)
            );"""
        )

        # This table holds in which run each appears.
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Runs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(14),
                comparison_threshold DECIMAL,
                collection_id INT REFERENCES RunCollections(id)
            );"""
        )

        # This table holds resources, which can be in multiple runs and have multiple varieties
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Resources (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                extension VARCHAR(20), 
                webpage VARCHAR(30),
                run_id INT REFERENCES Runs(id)
            );"""
        )

        # This table holds the different files found.
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Varieties (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                resource_id INT NOT NULL REFERENCES Resources(id), 
                name VARCHAR(40), 
                hash VARCHAR(10000), 
                content MEDIUMBLOB
            );"""
        )

        _logger.debug("Database initialized")

    def __select(self, fields, tables, conditions, values, order):
        """Internal select function."""

        request = "SELECT {fields} FROM {tables}{conditions}{order}"

        if conditions:
            cond_list = " WHERE "
            for index, cond in enumerate(conditions):
                cond_list += "(" + cond
                if values[index] == "NULL":
                    cond_list += " IS %s)"
                    values[index] = None
                elif values[index] == "NOT NULL":
                    cond_list += " IS NOT %s)"
                    values[index] = None
                else:
                    cond_list += " %s)"
                if index < len(conditions) - 1:
                    cond_list += " AND "
        else:
            cond_list = ""

        if order:
            ord_list = " ORDER BY {0}".format(", ".join(order))
        else:
            ord_list = ""

        request = request.format(
            fields=", ".join(fields),
            tables=", ".join(tables),
            conditions=cond_list,
            order=ord_list,
        )
        cursor = self.conn.cursor(dictionary=True)
        results = []
        _logger.debug("%r, %r" % (request, values))
        try:
            if values:
                cursor.execute(request, tuple(values))
            else:
                cursor.execute(request)
        except Exception as error:
            _logger.exception(str(error))
        else:
            for row in cursor.fetchall():
                result = {}
                for key in row.keys():
                    result[key] = row[key]
                    if row[key] == "NULL":
                        result[key] = None
                results.append(result)
            _logger.debug(
                "SELECT REQUEST ON {0} OK. Results: {1}".format(
                    ", ".join(tables), results
                )
            )
        cursor.close()
        return results

    def select(self, fields, tables, conditions, values, order):
        """Calls the internal _select function."""

        result = self.__select(fields, tables, conditions, values, order)
        return result

    def __update(self, table, fields, conditions, values):
        """Internal update fucntion."""

        if fields and len(fields) + len(conditions) != len(values):
            _logger.warning("Incorrect number of fields/conditions/values")
            return False

        request = "UPDATE {table} SET {fields} WHERE {conditions}"
        request = request.format(
            table=table,
            fields=" = %s,".join(fields + ["0"])[0:-2],
            conditions=" %s".join(conditions + ["0"])[:-1],
        )
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except Exception as error:
            _logger.exception(str(error))
            cursor.close()
            return False
        else:
            _logger.debug("UPDATE REQUEST ON %s OK." % table)
            cursor.close()
            return True

    def update(self, table, element):
        """Update the table for the given element id, using the internal function.

        Returns False if the request failed, else True.
        """

        if "id" not in element.keys():
            return False
        fields = []
        conditions = []
        values = []
        for key in element.keys():
            if key != "id":
                fields.append(key)
                values.append(element[key])
        conditions.append("id =")
        values.append(element["id"])
        result = self.__update(table, fields, conditions, values)

        return result

    def __insert(self, table, fields, values):
        """Creates a standard INSERT request."""

        if fields and len(fields) != len(values):
            _logger.warning("Incorrect number of field/values")
            return -1

        request = "INSERT INTO {table} ({fields}) VALUES ({values})"
        request = request.format(
            table=table, fields=", ".join(fields), values=("%s, " * len(values))[0:-2]
        )
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except Exception as error:
            _logger.exception(str(error))
            return -1
        else:
            self.conn.commit()
            row_id = cursor.lastrowid
            _logger.debug("INSERT REQUEST ON {0} OK. Row_id: {1}".format(table, row_id))
            cursor.close()
            return row_id

    def insert(self, table, element):
        """Insert the element if it can not be updated first (doesn't exists) using the internal function.

        If successful returns lastrowid.
        """

        update = self.update(table, element)
        if update:
            return update

        fields = []
        values = []
        for key in element.keys():
            fields.append(key)
            values.append(element[key])
        result = self.__insert(table, fields, values)
        return result

    def __delete(self, table, conditions, values):
        """Creates and executes a standard DELETE request.

        Returns True on success.
        """

        # Slightly improved version
        request = "DELETE FROM {table} WHERE {conditions}"
        request = request.format(
            table=table, conditions=" %s AND".join(conditions + ["0"])[0:-5]
        )
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except Exception as error:

            _logger.exception(str(error))
            cursor.close()
            return False
        else:
            self.conn.commit()
            _logger.debug("DELETE REQUEST OK.")
            cursor.close()
            return True

    def delete(self, table, element):
        """Removes the element from the table, using the internal method.

        Returns True on success.
        """

        conditions = ["id"]
        values = element["id"]
        result = self.__delete(table, conditions, [values])
        return result


class DatabaseAdapter:
    """This class is used as an interface between the rest of the program structure and the structure of the Database.

    It translates domain object to tables and viceversa.
    """

    def __init__(self):
        self._db = Database(_DB_HOSTNAME, _DB_USER, _DB_PASSWORD, _DB_DATABASE)
        self._db.initialize()

    def _translate_to_resource(
        self, resource, recursive=False, variety_conditions=[], load_content=False
    ):
        """Translates an object from the database into a resource object.

        This method returns a Resource object.
        """

        conditions = []
        values = []
        try:
            for cond, val in variety_conditions:
                conditions.append(cond)
                values.append(val)
        except ValueError:
            raise RuntimeError(
                "Error: variety_conditins requires tuples of 2 values in every condition."
            )

        variety_list = []
        if recursive:
            row_list = []
            conditions.extend(["resource_id ="])
            values.extend(
                [
                    resource["id"],
                ]
            )
            if not load_content:

                row_list = self._db.select(
                    ["id", "name", "hash"],
                    [
                        "Varieties",
                    ],
                    conditions,
                    values,
                    None,
                )
            else:
                row_list = self._db.select(
                    ["id", "name", "hash", "content"],
                    [
                        "Varieties",
                    ],
                    conditions,
                    values,
                    None,
                )
            for vrow in row_list:
                # Make string representation of array
                translated_hash = list(vrow["hash"][1:-2].split(" "))

                variety = Resource.Variety(
                    content=vrow["content"] if "content" in vrow else "NotLoaded",
                    hash=translated_hash,
                )
                variety.set_name(vrow["name"])
                variety_list.append(variety)

        result = Resource(resource["extension"], resource["webpage"])
        result.add_varieties(variety_list)
        result.set_id(resource["id"])

        return result

    def _translate_from_resource(self, resource):
        """Translates resource(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to.
        """

        resource_row = {
            "extension": resource.get_extension(),
            "webpage": resource.get_webpage(),
        }
        # If this resource has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = resource.get_id()
        if not (an_id is None):
            resource_row["id"] = an_id

        variety_group = []

        for variety in resource.varieties:
            the_hash = variety.get_hash_string()
            if len(the_hash.split("\n")) > 1:
                raise RuntimeError("Hash is too big! Cannot be stored in the DB")

            variety_row = {
                "resource_id": resource.get_id(),
                "name": variety.get_name(),
                "hash": the_hash,
                "content": variety.get_content(),
            }

            an_id = variety.get_id()
            if not (an_id is None):
                variety_row["id"] = an_id

            variety_group.append(variety_row)

        return resource_row, variety_group

    def _translate_to_run(
        self, run, recursive=False, resource_conditions=[], variety_conditions=[]
    ):
        """Translates a row from the DB into a Run object from the domain."""

        list_of_resources = []
        if recursive:
            conditions = [
                ("run_id =", run["id"]),
            ]
            conditions.extend(resource_conditions)
            list_of_resources = self.load_resources(
                recursive=recursive,
                resource_conditions=conditions,
                variety_conditions=variety_conditions,
            )

        result = Run(run["name"], data=list_of_resources)
        result.set_id(run["id"])

        return result

    def _translate_from_run(self, run):
        """Translates  run(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to.
        """

        row = {
            "name": run.get_name(),
        }
        # If this run has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = run.get_id()
        if not (an_id is None):
            row["id"] = an_id

        return row

    def _translate_from_collection(self, collection):
        """Translates  collection(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to.
        """

        row = {
            "name": collection.get_name(),
        }
        # If this run has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = collection.get_id()
        if an_id:
            row["id"] = an_id

        return row

    def _translate_to_collection(
        self,
        collection,
        recursive=False,
        run_conditions=[],
        resource_conditions=[],
        variety_conditions=[],
    ):
        """Translates a row from the DB into a RunCollection object from the domain."""

        run_list = []
        if recursive:
            run_conditions.extend(
                [
                    ("collection_id =", collection["id"]),
                ]
            )
            run_list = self.load_runs(
                recursive=recursive,
                run_conditions=run_conditions,
                resource_conditions=resource_conditions,
                variety_conditions=variety_conditions,
            )

        res = RunCollection(collection["name"], data=run_list)
        res.set_id(collection["id"])

        return res

    def _save_resource(self, resource, run_id=None):
        """Private method to update or insert resources in the DB.

        resources argument must be an iterable.
        """
        _logger.debug("Save %r" % resource)
        a_resource, varieties = self._translate_from_resource(resource)
        a_resource["run_id"] = run_id

        row_id = self._db.insert("Resources", a_resource)

        for variety in varieties:
            variety["resource_id"] = row_id
            self._db.insert("Varieties", variety)

    def _save_run(self, run, collection_id=None):
        _logger.debug("Save %r" % run)
        a_run = self._translate_from_run(run)
        a_run["collection_id"] = collection_id
        row_id = self._db.insert("Runs", a_run)
        for resource in run:
            self._save_resource(resource, run_id=row_id)

    def _save_collection(self, collection):
        _logger.debug("Save %r" % collection)
        a_coll = self._translate_from_collection(collection)

        row_id = self._db.insert("RunCollections", a_coll)
        for run in collection:
            self._save_run(run, collection_id=row_id)

    def save(self, obj, parent_id=None):
        """Tries to update or insert an object into the DB."""
        if isinstance(obj, Resource):
            self._save_resource(obj, run_id=parent_id)
        elif isinstance(obj, Run):
            self._save_run(obj, collection_id=parent_id)
        elif isinstance(obj, RunCollection):
            self._save_collection(obj)

    def save_all(self, obj_list):
        """Tries to update or insert the objects provided."""

        for obj in obj_list:
            self.save(obj)

    def load_resources(
        self,
        recursive=False,
        resource_conditions=[],
        variety_conditions=[],
        load_content=False,
    ):
        conditions = []
        values = []
        try:
            for cond, val in resource_conditions:
                conditions.append(cond)
                values.append(val)
        except ValueError:
            raise RuntimeError(
                "Error: resource_conditins requires tuples of 2 values in every condition."
            )

        row_list = self._db.select(
            ["id", "extension", "webpage"],
            [
                "Resources",
            ],
            conditions,
            values,
            None,
        )

        resource_list = []
        for row in row_list:
            resource_list.append(
                self._translate_to_resource(
                    row,
                    recursive=True,
                    variety_conditions=variety_conditions,
                    load_content=load_content,
                )
            )

        return resource_list

    def load_runs(
        self,
        recursive=False,
        run_conditions=[],
        resource_conditions=[],
        variety_conditions=[],
    ):
        conditions = []
        values = []
        try:
            for cond, val in run_conditions:
                conditions.append(cond)
                values.append(val)
        except ValueError:
            raise RuntimeError(
                "Error: run_conditions requires tuples of 2 values in every condition."
            )

        rows = self._db.select(
            ["id", "name", "collection_id"],
            [
                "Runs",
            ],
            conditions,
            values,
            None,
        )
        run_list = []
        for rrow in rows:
            run_list.append(
                self._translate_to_run(
                    rrow,
                    recursive=recursive,
                    resource_conditions=resource_conditions,
                    variety_conditions=variety_conditions,
                )
            )

        return run_list

    def load_collections(
        self,
        recursive=False,
        collection_conditions=[],
        run_conditions=[],
        resource_conditions=[],
        variety_conditions=[],
    ):
        """Loads RunCollections from the DB.

        If recursive is True, loads also all the objects inside.

        Parameters collection_conditions, run_conditions, resource_conditions and variety_conditions
        must be lists of tuples of 2 elements. These specify conditions that the object loaded must fullfil.

        Example 1:

            - collection_condition=[("name =", "no_vpn")]

            This will only load collections that have the name "no_vpn".

        Example 2:

            - collection_condition=[("name =", "no_vpn"),]
            - run_condition=[("name >", "1")]
            - resource_condition=[("webpage =", "buydomains-com")]

            This will only load collections that have the name "no_vpn", that contain runs with
            a name greater than "1" and with resources that belong to the webpage "buydomains-com".

            :returns: [RunCollection(),...]
        """
        conditions = []
        values = []
        try:
            for cond, val in collection_conditions:
                conditions.append(cond)
                values.append(val)
        except ValueError:
            raise RuntimeError(
                "Error: collection_conditins requires tuples of 2 values in every condition."
            )

        total_rows = self._db.select(
            ["id", "name"],
            [
                "RunCollections",
            ],
            conditions,
            values,
            ["name"],
        )

        result = []
        for crow in total_rows:
            result.append(
                self._translate_to_collection(
                    crow,
                    recursive=recursive,
                    run_conditions=run_conditions,
                    resource_conditions=resource_conditions,
                    variety_conditions=variety_conditions,
                )
            )

        return result


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
