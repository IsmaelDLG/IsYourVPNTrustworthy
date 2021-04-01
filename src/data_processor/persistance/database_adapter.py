import logging

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
        self.conn = connector.connect(host=host, user=user, passwd=password, db="vpntfg0")

    def close(self):
        """Closes the connection to the database.
        """

        self.conn.close()
    
    def initialize(self):
        """Initializes the database, creating tables if needed.
        """

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
                name VARCHAR(32), 
                hash VARCHAR(10000), 
                content MEDIUMBLOB
            );"""
        )

        _logger.debug("Database initialized")

    def __select(self, fields, tables, conditions, values, order):
        """Internal select function.
        """

        request = "SELECT "
        field_list = ", ".join(fields)
        request += field_list
        request += " FROM " + ", ".join(tables)
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
                    cond_list += " = %s)"
                if index < len(conditions) - 1:
                    cond_list += " AND "
            request += cond_list
        if order:
            request += " ORDER BY " + ", ".join(order)
        
        cursor = self.conn.cursor(dictionary=True)
        results = []
        try:
            if values:
                cursor.execute(request, tuple(values))
            else:
                cursor.execute(request)
        except Exception as error:
            _logger.exception(str(error))
            """
            if values:
                _logger.error(request % tuple(values))
            else:
                _logger.error(request)
            """
        else:
            for row in cursor.fetchall():
                result = {}
                for key in row.keys():
                    result[key] = row[key]
                    if row[key] == "NULL":
                        result[key] = None
                results.append(result)
            _logger.debug("SELECT REQUEST ON %s OK." % ", ".join(tables) + "\n-----------------")
        cursor.close()
        return results

    def select(self, fields, tables, conditions, values, order):
        """Calls the internal _select function. 
        """

        result = self.__select(fields, tables, conditions, values, order)
        return result
    
    def __update(self, table, fields, conditions, values):
        """Internal update fucntion.
        """

        if fields and len(fields) + len(conditions) != len(values):
            _logger.warning("Incorrect number of fields/conditions/values")
            return False
        request = "UPDATE " + table
        request += " SET " + fields[0] + " = %s"
        if len(fields) > 1:
            for index in range(1, len(fields)):
                request += ", " + fields[index] + " = %s"
        request += " WHERE " + conditions[0] + " = %s"
        if len(conditions) > 1:
            for index in range(1, len(conditions)):
                request += " AND " + conditions[index] + " = %s"
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except Exception as error:
            """
            _logger.error(request % tuple(values))
            """
            _logger.exception(str(error))
            cursor.close()
            return False
        else:
            _logger.debug("UPDATE REQUEST OK.\n-----------------")
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
        conditions.append("id")
        values.append(element["id"])
        result = self.__update(table, fields, conditions, values)

        return result

    def __insert(self, table, fields, values):
        """Creates a standard INSERT request. 
        """

        if fields and len(fields) != len(values):
            _logger.warning("Incorrect number of field/values")
            return -1
        request = "INSERT INTO " + table
        if fields:
            request += " (" + fields[0]
            if len(fields) > 1:
                for index in range(1, len(fields)):
                    request += ", " + fields[index]
            request += ")"
        request += " VALUES (%s"
        if len(values) > 1:
            for index in range(1, len(values)):
                request += ", %s"
        request += ")"
        request += " ON DUPLICATE KEY UPDATE "
        if fields:
            request += fields[0]+"=%s"
            if len(fields) > 1:
                for index in range(1, len(fields)):
                    request += ", " + fields[index] + "=%s"
        new_values = values.copy()
        for value in new_values:
            values.append(value)
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except Exception as error:
            """
            _logger.error(request % tuple(values))
            """
            _logger.exception(str(error))
            return -1
        else:
            self.conn.commit()
            row_id = cursor.lastrowid
            _logger.debug("INSERT REQUEST ON %s OK. Row_id: %i \n-----------------" % (table, row_id))
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

        request = "DELETE FROM " + table
        request += " WHERE " + conditions[0] + " = %s"
        if len(conditions) > 1:
            for index in range(1, len(conditions)):
                request += " AND " + conditions[index] + " = %s"
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(request, tuple(values))
        except MySQLdb.Error as error:
            """
            _logger.error(request % tuple(values))
            """
            _logger.error("SQL ERROR: " + str(error) + "\n-----------------")
            cursor.close()
            return False
        else:
            self.conn.commit()
            _logger.debug("DELETE REQUEST OK.\n-----------------")
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

    def _translate_to_resource(self, resource):
        """Translates an object from the database into a resource object.

        This method returns a Resource object.
        """

        row_list = self._db.select(["id", "name", "hash", "content"], ["Varieties",], ["resource_id"], [str(resource["id"])], None)
        variety_list = []
        for vrow in row_list:
            # Make string representation of array
            translated_hash = list(vrow["hash"][1:-2].split(" "))
            variety_list.append(Resource.Variety(vrow["name"], content=vrow["content"], hash=translated_hash))
        
        result = Resource(resource["extension"], resource["webpage"])
        result.add_varieties(variety_list)
        result.set_id(resource["id"])

        return result

    def _translate_from_resource(self, resource):
        """Translates resource(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to. 
        """

        resource_row = {
            'extension': resource.get_extension(),
            'webpage': resource.get_webpage()
        }
        # If this resource has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = resource.get_id()
        if not (an_id is None):
            resource_row['id'] = an_id

        variety_group = []

        for variety in resource.varieties:
            the_hash = variety.get_hash_string()
            if len(the_hash.split('\n')) > 1:
                raise RuntimeError("Hash is too big! Cannot be stored in the DB")
        
            variety_row = {
                'resource_id': resource.get_id(),
                'name': variety.get_name(),
                'hash': the_hash,
                'content': variety.get_content()
            }

            an_id = variety.get_id()
            if not (an_id is None):
                variety_row['id'] = an_id

            variety_group.append(variety_row)

        return resource_row, variety_group
    
    def _translate_to_run(self, run):
        """Translates a row from the DB into a Run object from the domain.
        """
    
        row_list = self._db.select(["id", "extension", "webpage"], ["Resources",], ["run_id"], [str(run["id"])], None)
        list_of_resources = []
        for rrow in row_list:
            list_of_resources.append(self._translate_to_resource(rrow))

        result = Run(run["name"], data=list_of_resources)
        result.set_id(run["id"])
        
        return result

    def _translate_from_run(self, run):
        """Translates  run(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to. 
        """

        row = {
            'name': run.get_name(),
        }
        # If this run has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = run.get_id()
        if not (an_id is None):
            row['id'] = an_id

        return row

    def _translate_from_collection(self, collection):
        """Translates  collection(s) object from the domain into database tuples.

        This method returns a dictionary with the elements and the tables they belong to. 
        """

        row = {
            'name': collection.get_name(),
        }
        # If this run has been creeated in domain, it will not have ID until the DB gives it to him
        an_id = collection.get_id()
        if an_id:
            row['id'] = an_id

        return row

    def _translate_to_collection(self, collection):
        """Translates a row from the DB into a RunCollection object from the domain.
        """

        rows = self._db.select(["id", "name", "comparison_threshold", "collection_id"], ["Runs",], ["collection_id"], [str(collection["id"])], None)
        run_list = []
        for rrow in rows:
                run_list.append(self._translate_to_run(rrow))
        
        res = RunCollection(collection["name"], data=run_list)
        res.set_id(collection["id"])
        
        return res       

    def _save_resource(self, resource, run_id = None):
        """Private method to update or insert resources in the DB.

        resources argument must be an iterable.
        """
        _logger.debug("Save %r" % resource)
        a_resource, varieties = self._translate_from_resource(resource)
        a_resource["run_id"] = run_id
        
        row_id = self._db.insert('Resources', a_resource)

        for variety in varieties:
            variety["resource_id"] = row_id
            self._db.insert('Varieties', variety)

    def _save_run(self, run, collection_id = None):
        _logger.debug("Save %r" % run)
        a_run = self._translate_from_run(run)
        a_run['collection_id'] = collection_id
        row_id = self._db.insert('Runs', a_run)
        for resource in run:
            self._save_resource(resource, run_id=row_id)
    
    def _save_collection(self, collection):
        _logger.debug("Save %r" % collection)
        a_coll = self._translate_from_collection(collection)
        
        row_id = self._db.insert('RunCollections', a_coll)
        for run in collection:
            self._save_run(run, collection_id=row_id)

    def save(self, obj):
        """Tries to update or insert an object into the DB.
        """
        if isinstance(obj, Resource):
            self._save_resource(obj)
        elif isinstance(obj, Run):
            self._save_run(obj)
        elif isinstance(obj, RunCollection):
            self._save_collection(obj)

    def save_all(self, obj_list):
        """Tries to update or insert the objects provided.
        """

        for obj in obj_list:
            self.save(obj)
    
    def load_collections(self, names=None, recursive=False):
        """Loads RunCollections from the DB. names can be None or a list of the collections you want to load.
        If recursive is True, loads also all the objects inside.
        """

        total_rows = []
        if not (names is None):
            for name in names:
                col_rows = self._db.select(["id", "name"], ["RunCollections",], ["name"], [name], ["name"])
                total_rows.extend(col_rows)

        result = []
        for crow in total_rows:
            result.append(self._translate_to_collection(crow))

        return result

        
                
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)