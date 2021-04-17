import logging
from time import sleep

from mysql import connector
from numpy import array, array2string
from numpy import uint64

from copy import deepcopy as copy

from config import (
    _DB_DATABASE,
    _DB_HOSTNAME,
    _DB_PASSWORD,
    _DB_USER,
    _VARIETIES_SIZE,
    _LOG_LEVEL,
)
from persistance import Resource, Run, RunCollection


class Database:

    variety_tables = list()

    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db = db_name
        self.conn = connector.connect(
            host=host, user=user, passwd=password, db="vpntfg0"
        )
        _logger.info(
            "Thread safety provided by connector is %i" % connector.threadsafety
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
                name VARCHAR(14) UNIQUE
            );"""
        )

        # This table holds in which run each appears.
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Runs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(14) UNIQUE,
                comparison_threshold DECIMAL(3,3),
                collection_id INT,
                FOREIGN KEY (collection_id) REFERENCES RunCollections (id) ON DELETE CASCADE);"""
        )

        # This table holds resources, which can be in multiple runs and have multiple varieties
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Resources (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                extension VARCHAR(20), 
                webpage VARCHAR(30),
                run_id INT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES Runs (id) ON DELETE CASCADE);"""
        )

        # # This table holds the different files found.
        # cursor.execute(
        #     """CREATE TABLE IF NOT EXISTS Varieties (
        #         id INT AUTO_INCREMENT PRIMARY KEY,
        #         resource_id INT NOT NULL,
        #         name VARCHAR(40),
        #         hash VARCHAR(10000),
        #         content MEDIUMBLOB,
        #         FOREIGN KEY (resource_id) REFERENCES Resources (id) ON DELETE CASCADE);"""
        # )

        # 'SELECT Table_name FROM information_schema.tables WHERE table_schema = "vpntfg0" AND Table_name LIKE "%Varieties%";'
        cursor.execute(
            'SELECT Table_name FROM information_schema.tables WHERE table_schema = "vpntfg0" AND Table_name LIKE "%Varieties_%" ORDER BY Table_name'
        )
        for row in cursor.fetchall():
            self.variety_tables.append(row[0])

        cursor.close()
        _logger.info("Variety tables are: %s" % self.variety_tables)

        _logger.info("Database initialized")

    def _match_variety_table(self, an_id):
        """Finds the corresponding variety table for the given number.

        Returns the index that indicates the position in the property variety_tables to use as table name.
        """

        i = 1
        found = False
        while not found:
            if i * _VARIETIES_SIZE > an_id:
                found = True
            else:
                i += 1

        return i - 1

    def __select(self, fields, tables, conditions, values, order):
        """Internal select function.

        Not ready to do joins in tables or to use separate intervals in where clauses."""

        start_table = 0
        end_table = -1
        for i in range(0, len(tables)):
            if tables[i] == "Varieties":
                tables.pop(i)
                for j in range(0, len(conditions)):
                    if conditions[j].startswith("resource_id"):
                        index = self._match_variety_table(values[j])
                        if conditions[j].endswith(" ="):
                            start_table = index
                            end_table = index + 1
                        elif conditions[j].endswith(" <") or conditions[j].endswith(
                            " <="
                        ):
                            end_table = index + 1
                        elif conditions[j].endswith(" >") or conditions[j].endswith(
                            " >="
                        ):
                            start_table = index

                tables.extend(self.variety_tables[start_table:end_table])

        request = "SELECT {fields} FROM {tables}{conditions}"

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

        for table in tables:
            end_request = " UNION ".join(
                [
                    request.format(
                        fields=", ".join(fields),
                        tables=table,
                        conditions=cond_list,
                    )
                    for table in tables
                ]
            )
        if order:
            ord_list = " ORDER BY {0}".format(", ".join(order))

            end_request = end_request + ord_list

        cursor = self.conn.cursor(dictionary=True)
        results = []
        _logger.debug("%r, %r" % (end_request, values * len(tables)))
        try:
            if values:
                cursor.execute(end_request, tuple(values * len(tables)))
            else:
                cursor.execute(end_request)
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

            aux_results = copy(results)
            for i in range(0, len(aux_results)):
                aux_results[i].pop("hash", None)
                aux_results[i].pop("content", None)

            _logger.debug(
                "SELECT REQUEST ON {0} OK. Results: {1}".format(
                    ", ".join(tables), aux_results
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

        tables = [
            table,
        ]
        if table == "Varieties":
            start_table = 0
            end_table = -1
            for i in range(0, len(tables)):
                if tables[i] == "Varieties":
                    tables.pop(i)
                    for j in range(0, len(conditions)):
                        if conditions[j].startswith("resource_id"):
                            index = self._match_variety_table(values[j])
                            if conditions[j].endswith(" ="):
                                start_table = index
                                end_table = index + 1
                            elif conditions[j].endswith(" <") or conditions[j].endswith(
                                " <="
                            ):
                                end_table = index + 1
                            elif conditions[j].endswith(" >") or conditions[j].endswith(
                                " >="
                            ):
                                start_table = index

                    tables = self.variety_tables[start_table:end_table]

        cursor = self.conn.cursor(dictionary=True)
        all_ok = True
        for table in tables:

            request = "UPDATE {table} SET {fields} WHERE {conditions}"
            request = request.format(
                table=table,
                fields=" = %s,".join(fields + ["0"])[0:-2],
                conditions=" %s".join(conditions + ["0"])[:-1],
            )
            try:
                cursor.execute(request, tuple(values))
            except Exception as error:
                _logger.exception(str(error))
                all_ok = False
            else:
                self.conn.commit()
                _logger.debug("UPDATE REQUEST ON %s OK." % table)

        cursor.close()
        return all_ok

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

        if table == "Varieties":
            index = 0
            found = False
            while not found and index < len(fields):
                if fields[index] == "resource_id":
                    found = True
                else:
                    index += index
            if found and values[index]:
                table_num = self._match_variety_table(int(values[index]))

                while not table_num < len(self.variety_tables):
                    # Create as many tables as needed to classify this variety properly
                    current_next = len(self.variety_tables) + 1
                    cursor = self.conn.cursor()

                    cursor.execute(
                        """CREATE TABLE Varieties_{0} (
                            id INT AUTO_INCREMENT PRIMARY KEY, 
                            resource_id INT NOT NULL, 
                            name VARCHAR(40), 
                            hash VARCHAR(10000), 
                            content MEDIUMBLOB,
                            FOREIGN KEY (resource_id) REFERENCES Resources (id) ON DELETE CASCADE
                        );""".format(
                            current_next
                        )
                    )

                    self.variety_tables.append("Varieties_{0}".format(current_next))
                    _logger.info(
                        "Created Varieties_{0} for it is not possible to insert more rows in the previous one".format(
                            current_next
                        )
                    )

                table = self.variety_tables[table_num]

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
        tables = [
            table,
        ]
        if table == "Varieties":
            start_table = 0
            end_table = -1
            for i in range(0, len(tables)):
                if tables[i] == "Varieties":
                    tables.pop(i)
                    for j in range(0, len(conditions)):
                        if conditions[j].startswith("resource_id"):
                            index = self._match_variety_table(values[j])
                            if conditions[j].endswith(" ="):
                                start_table = index
                                end_table = index + 1
                            elif conditions[j].endswith(" <") or conditions[j].endswith(
                                " <="
                            ):
                                end_table = index + 1
                            elif conditions[j].endswith(" >") or conditions[j].endswith(
                                " >="
                            ):
                                start_table = index

                    tables = self.variety_tables[start_table:end_table]

        # Slightly improved version
        all_ok = True
        cursor = self.conn.cursor(dictionary=True)

        for talbe in tables:
            request = "DELETE FROM {table} WHERE {conditions}"
            request = request.format(
                table=table, conditions=" %s AND".join(conditions + ["0"])[0:-5]
            )
            try:
                cursor.execute(request, tuple(values))
            except Exception as error:
                _logger.exception(str(error))
                all_ok = False
            else:
                self.conn.commit()
                _logger.debug("DELETE REQUEST ON {0} OK.".format(table))
        cursor.close()

        return all_ok

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
                variety.set_id(vrow["id"])
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
            }

            content = variety.get_content()

            if content != "NotLoaded":
                variety_row["content"] = content

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
            list_of_resources = self.load_resources_major(
                recursive=recursive,
                resource_conditions=conditions,
                variety_conditions=variety_conditions,
            )

        result = Run(run["name"], data=list_of_resources)
        result.set_id(run["id"])
        result.set_threshold(float(run["comparison_threshold"]))

        return result

    def _translate_from_run(self, run):
        """Translates  run(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to.
        """

        row = {
            "name": run.get_name(),
            "comparison_threshold": run.get_threshold(),
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

        a_resource, varieties = self._translate_from_resource(resource)
        a_resource["run_id"] = run_id
        row_id = self._db.insert("Resources", a_resource)
        if not isinstance(row_id, bool):
            resource.set_id(row_id)
        _logger.info("Save %r" % resource)

        for variety in varieties:
            variety["resource_id"] = row_id
            self._db.insert("Varieties", variety)

        return row_id

    def _save_run(self, run, collection_id=None):

        a_run = self._translate_from_run(run)
        a_run["collection_id"] = collection_id
        row_id = self._db.insert("Runs", a_run)
        if not isinstance(row_id, bool):
            run.set_id(row_id)
        _logger.info("Save %r" % run)
        for resource in run:
            self._save_resource(resource, run_id=row_id)

        return row_id

    def _save_collection(self, collection):
        a_coll = self._translate_from_collection(collection)

        row_id = self._db.insert("RunCollections", a_coll)
        if not isinstance(row_id, bool):
            collection.set_id(row_id)
        _logger.info("Save %r" % collection)
        for run in collection:
            self._save_run(run, collection_id=row_id)

        return row_id

    def save(self, obj, parent_id=None):
        """Tries to update or insert an object into the DB."""
        res = None
        if isinstance(obj, Resource):
            res = self._save_resource(obj, run_id=parent_id)
        elif isinstance(obj, Run):
            res = self._save_run(obj, collection_id=parent_id)
        elif isinstance(obj, RunCollection):
            res = self._save_collection(obj)
        return res

    def save_all(self, obj_list):
        """Tries to update or insert the objects provided."""

        for obj in obj_list:
            self.save(obj)

    def load_resources_minor(
        self,
        recursive=False,
        resource_conditions=[],
        variety_conditions=[],
        load_content=False,
    ):
        """Loads resources from database. Better when the set of resources to load is small (specific queries)."""

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

    def load_resources_major(
        self,
        recursive=False,
        resource_conditions=[],
        variety_conditions=[],
        load_content=False,
    ):
        """Loads resources from database. Better when the set of resources to load is big (runs)."""

        res_conditions = []
        res_values = []
        try:
            for cond, val in resource_conditions:
                res_conditions.append(cond)
                res_values.append(val)
        except ValueError:
            raise RuntimeError(
                "Error: resource_conditins requires tuples of 2 values in every condition."
            )

        res_row_list = self._db.select(
            ["id", "extension", "webpage"],
            [
                "Resources",
            ],
            res_conditions,
            res_values,
            ["id"],
        )

        var_row_list = []
        if recursive and len(res_row_list) > 0:
            min_res_id = res_row_list[0]["id"]
            max_res_id = res_row_list[-1]["id"]

            var_conditions = ["resource_id >=", "resource_id <="]
            var_values = [min_res_id, max_res_id]
            try:
                for cond, val in variety_conditions:
                    var_conditions.append(cond)
                    var_values.append(val)
            except ValueError:
                raise RuntimeError(
                    "Error: variety_conditins requires tuples of 2 values in every condition."
                )

            if not load_content:

                var_row_list = self._db.select(
                    ["id", "name", "hash", "resource_id"],
                    [
                        "Varieties",
                    ],
                    var_conditions,
                    var_values,
                    ["resource_id"],
                )
            else:
                var_row_list = self._db.select(
                    ["id", "name", "hash", "content", "resource_id"],
                    [
                        "Varieties",
                    ],
                    var_conditions,
                    var_values,
                    ["resource_id"],
                )

        index = 0
        result = []
        for res in res_row_list:

            finished = False
            varieties = []
            while not finished and index < len(var_row_list):
                if var_row_list[index]["resource_id"] == res["id"]:
                    translated_hash = list(var_row_list[index]["hash"][1:-2].split(" "))

                    variety = Resource.Variety(
                        content=var_row_list[index]["content"]
                        if "content" in var_row_list[index]
                        else "NotLoaded",
                        hash=translated_hash,
                    )
                    variety.set_name(var_row_list[index]["name"])
                    variety.set_id(var_row_list[index]["id"])
                    varieties.append(variety)

                    index += 1
                else:
                    finished = True

            aux = Resource(res["extension"], res["webpage"])
            aux.set_id(res["id"])
            aux.add_varieties(varieties)
            result.append(aux)

        return result

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
            ["id", "name", "collection_id", "comparison_threshold"],
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

    def find_matching_varieties(self, a_variety, conditions=[], limit=None):
        """Loads varieties from the database that match in name with the given variety. ANy toher conditions can be provided in conditions list."""

        var_conditions = [
            ("name =", a_variety.get_name()),
        ]
        var_conditions.extend(conditions)

        conditions = []
        values = []
        for cond, val in var_conditions:
            conditions.append(cond)
            values.append(val)

        row_list = []
        for table in self._db.variety_tables:
            rows = self._db.select(
                ["id", "name", "hash", "content"], [table], conditions, values, ["id"]
            )
            row_list.extend(rows)
            if not (limit is None) and len(row_list) >= limit:
                _logger.info("Limit for find_matching_resources reached")
                break

        variety_list = []
        for row in row_list:
            translated_hash = list(row["hash"][1:-2].split(" "))

            variety = Resource.Variety(
                content=row["content"],
                hash=translated_hash,
            )
            variety.set_name(row["name"])
            variety.set_id(row["id"])
            variety_list.append(variety)
        return variety_list

    def find_matching_resource(self, a_resource, run_id=None, recursive=False):
        res_conditions = [
            ("extension =", a_resource.get_extension()),
            ("webpage =", a_resource.get_webpage()),
        ]

        the_id = a_resource.get_id()

        if not (the_id is None):
            res_conditions.append(("id =", the_id))

        if not (run_id is None):
            res_conditions.append(("run_id =", run_id))

        stored_resources = self.load_resources_major(
            recursive=recursive, resource_conditions=res_conditions
        )
        _logger.debug("Stored Resources found: %r" % stored_resources)

        result = []

        tmp_run = Run("tmp", stored_resources)
        index = tmp_run.find_similar(a_resource)

        return tmp_run[index] if not (index is None) else None

    def find_matching_run(self, a_run, col_id=None, recursive=False):
        conditions = [
            ("name =", a_run.get_name()),
        ]

        the_id = a_run.get_id()

        if not (the_id is None):
            conditions.append(("id =", the_id))

        if not (col_id is None):
            conditions.append(("collection_id =", col_id))

        stored_runs = self.load_runs(
            recursive=recursive,
            run_conditions=conditions,
        )

        return stored_runs[0] if len(stored_runs) > 0 else None

    def find_matching_collection(self, a_coll, recursive=False):
        """Returns a list of matching collections. Else, returns None."""
        conditions = [
            ("name =", a_coll.get_name()),
        ]
        the_id = a_coll.get_id()

        if not (the_id is None):
            conditions.append(("id =", the_id))

        stored_collection = self.load_collections(
            recursive=recursive, collection_conditions=conditions
        )

        # name unique, so length is always 1
        if len(stored_collection) > 0:
            return stored_collection[0]
        else:
            return None


_logger = logging.getLogger(__name__)
_logger.setLevel(_LOG_LEVEL)
