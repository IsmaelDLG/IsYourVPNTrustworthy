import logging
from time import time
import numpy
from os.path import isfile, sep as separator
from copy import deepcopy as copy
from sys import getsizeof

from datasketch import MinHash


def _create_minhash(in_data):
    """Returns a minhash using in_data.

    If in_data is instance list, it assumes in_data represents the content of a file, line per line.
    Else, if in_data is isntance of str, it assumes in_data represents a path to a file.
    """

    if isinstance(in_data, set):
        a_minhash = MinHash(num_perm=256)
        for group in in_data:
            a_minhash.update(group)
        return a_minhash
    elif isinstance(in_data, str):
        with open(in_data, "rb") as fd:
            res = fd.readlines()
        return _create_minhash(set(res))


class Resource:
    class Variety:
        def __init__(self, filepath=None, content=None, hash=None):
            """Initializes Variety object.

            If content is None (the default). The class will try to use filepath to open a file and load it's content.
            If hash is set to a numpy array, it is used to initialize the MinHash. Else, the file is opened and a MinHash is created out of the contents.
            """

            self._id = None

            if filepath:
                filename = filepath.split(separator)[-1]
                self.name = ".".join(filename.split(".")[0:-1])

            if content:
                self.content = content
            else:
                try:
                    with open(filepath, "rb") as fd:
                        self.content = fd.read()
                except Exception as e:
                    _logger.error("Could not open file {0}".format(filepath))
                    _logger.exception(str(e))
                    self.content = None

            if isinstance(hash, list):
                self.hash = MinHash(num_perm=256, hashvalues=hash)
            else:
                if isfile(filepath):
                    self.hash = _create_minhash(filepath)
                else:
                    raise RuntimeError(
                        "File %s provided to create variety of resource is invalid!"
                        % file
                    )

        def get_hash_string(self):
            """Returns the hash of the vile as a string."""
            arraystr = numpy.array2string(
                self.hash.digest(), separator=" ", max_line_width=10000
            )
            translated_hash = list(arraystr[1:-2].split(" "))
            while "" in translated_hash:
                translated_hash.remove("")
            return " ".join(translated_hash)

        def get_id(self):
            """getter for private field _id."""

            return self._id

        def set_id(self, an_id):
            """setter for private field _id."""

            self._id = an_id

        def get_name(self):
            """Getter for name."""

            return self.name

        def set_name(self, other):
            """setter for field."""

            self.name = other

        def get_content(self):
            """Getter for content."""

            return self.content

        def set_content(self, other):
            """setter for field."""

            self.content = other

        def __repr__(self):
            return "Variety<{id}>".format(id=self._id)

        def __str__(self):
            return "Variety<{0}, {1}>".format(self.get_id(), self.get_name())

        def __sizeof___(self):
            return getsizeof(self.content) + getsizeof(self.hash) + getsizeof(self.name)

    def __init__(self, extension, webpage, file=None, a_hash=None):
        """Initializes Resource object with all its fields."""

        self._id = None
        self.extension = extension
        self.webpage = webpage
        self.varieties = list()
        if file:
            self.varieties.append(Resource.Variety(file, hash=a_hash))

    def __repr__(self):
        return "Resource<{id}>".format(id=self._id)

    def __str__(self):
        return "Resource<{id}, {extension}, {webpage}>".format(
            id=self._id, extension=self.extension, webpage=self.webpage
        )

    def get_id(self):
        """getter for private field _id."""

        return self._id

    def set_id(self, an_id):
        """setter for private field _id."""

        self._id = an_id

    def get_extension(self):
        """getter for field extension."""

        return self.extension

    def set_extension(self, an_ext):
        """setter for field  extenion."""

        self.extension = an_ext

    def get_webpage(self):
        """getter for field webpage."""

        return self.webpage

    def set_webpage(self, an_ext):
        """setter for field  extenion."""

        self.webpage = an_ext

    def compare(self, other):
        """Compares this resource with other. Returns max similarity found, that is a float number between 0 and 1, both included."""

        max_sim = 0.0
        for case in self.varieties:
            for target in other.varieties:
                sim = case.hash.jaccard(target.hash)

                if sim > max_sim:
                    max_sim = sim

        return max_sim

    def get_varieties(self):
        """getter for _varieties private attribute."""

        return self.varieties

    def add_varieties(self, varieties):
        """Adds the given list of varieties to the current resource."""

        self.varieties.extend(varieties)

    def __sizeof__(self):
        suma = getsizeof(self.extension) + getsizeof(self.webpage)
        for var in self.varieties:
            suma += getsizeof(var)

        return suma


class Run(list):

    _COMPARISON_TRESHOLD = 0.80
    _id = None

    def __init__(self, name, data=None):
        """Initialize object."""

        super(Run, self).__init__()

        self._name = name

        if data is not None:
            self._list = list(data)
        else:
            self._list = list()

    def get_id(self):
        """getter for private field _id."""

        return self._id

    def set_id(self, an_id):
        """setter for private field _id."""

        self._id = an_id

    def get_name(self):
        """Getter for _name private property."""

        return self._name

    def set_name(self, new_name):
        """Setter for _name private property."""

        self._name = new_name

    def __repr__(self):
        return "{0} <id: {1}, name: {2}>".format(
            self.__class__.__name__, self.get_id(), self.get_name()
        )

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item"""
        del self._list[ii]

    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._list[ii] = val

    def __str__(self):
        return str(self._list)

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._list.insert(ii, val)

    def append(self, val):
        self.insert(len(self._list), val)

    def __iter__(self):
        """Custom __iter__ method."""

        for elem in self._list:
            yield elem

    def __contains__(self, val: Resource):
        max_sim = 0
        for case in self._list:
            sim = case.compare(val)
            if max_sim < sim:
                max_sim = sim
            if (
                max_sim >= self._COMPARISON_TRESHOLD
                and case.extension == val.extension
                and case.webpage == val.webpage
            ):
                break
        return (
            max_sim >= self._COMPARISON_TRESHOLD
            and case.extension == val.extension
            and case.webpage == val.webpage
        )

    def find_similar(self, other: Resource):
        """Finds the resource in the collection that is most similar to the other adn returns it's index. If similarity treshold is not reached, returns None."""

        ret = None
        max_sim = 0
        index = 0
        for case in self._list:
            sim = case.compare(other)
            if max_sim < sim and sim >= self._COMPARISON_TRESHOLD:
                max_sim = sim
                ret = index
            index += 1

        return ret

    def intersection(self, other):
        """Makes the intersection of the given run and self, and returns a Run object with the common resources in both Runs."""
        result = Run()

        for resource in self._list:
            index = other.find_similar(resource)
            if not (index is None):
                result.append(other[index])

        return result

    def can_join(self, other):
        """Returns wheter the two Run (self, and other) can be joined or not."""

        joined = True

        if not (self.get_id() is None) and not (other.get_id() is None):
            if self.get_id() != other.get_id():
                joined = False
        elif self.get_name() != other.get_name():
            joined = False

        return joined

    def join(self, other, compatible=False):
        """Attempts joining self with other. If compatible is True, they will only joined if they have the same id or name."""

        joined = True

        if compatible:
            joined = self.can_join(other)

        if joined:
            assert isinstance(other, Run)
            _logger.debug("Resources in run from DB: %r" % self._list)
            for res in other:
                index = self.find_similar(res)
                if not (index is None):
                    similarity = self._list[index].compare(res)
                    _logger.debug(
                        "Similarity between %r and %r is %f"
                        % (self._list[index], res, similarity)
                    )
                    # Si similarity es 1, son el mateix i no hem de fer res
                    if similarity >= self._COMPARISON_TRESHOLD and similarity < 0.99:
                        _logger.debug(
                            "Joining resources %r and %r" % (self._list[index], res)
                        )
                        self._list[index].add_varieties(res.get_varieties())
                    elif similarity >= 0.99:
                        _logger.debug("Coincidence found in %r and %r" % (self._list[index], res))
                else:
                    self.append(res)
                    _logger.debug(
                        "No similar resource found in run. Adding %r to %r"
                        % (res, self)
                    )

        _logger.debug("%r joined with %r" % (self, other))
        return joined

    def __sizeof__(self):
        suma = getsizeof(self._name)

        for x in self._list:
            suma += getsizeof(x)

        return suma


class RunCollection(list):

    _id = None

    def __init__(self, name, data=None):
        """Initialize object."""

        super(RunCollection, self).__init__()

        self._name = name

        if not (data is None):
            self._list = list(data)
        else:
            self._list = list()

    def get_id(self):
        """getter for private field _id."""

        return self._id

    def set_id(self, an_id):
        """setter for private field _id."""

        self._id = an_id

    def get_name(self):
        """Getter for _name private property."""

        return self._name

    def set_name(self, new_name):
        """Setter for _name private property."""

        self._name = new_name

    def get_runs(self):
        """Getter for _runs private property."""

        return self._list

    def set_runs(self, new_runs):
        """Setter for _list private property."""

        self._list = new_runs

    def __repr__(self):
        return "{0} <id: {1}, name: {2}, length: {3}>".format(
            self.__class__.__name__, self.get_id(), self.get_name(), len(self._list)
        )

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item"""

        del self._list[ii]

    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._list[ii] = val

    def __str__(self):
        return str(self._list)

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._list.insert(ii, val)

    def append(self, val):
        self.insert(len(self._list), val)

    def __iter__(self):
        """Custom __iter__ method."""

        for elem in self._list:
            yield elem

    def __contains__(self, name: str):
        """Returns True if the run is in the run list."""

        found = False

        for case in self._list:
            found = case.get_name() == name
            if found:
                break
        return found

    def constant_resources(self):
        # Intersection of all sets
        data = copy(self._list)

        # More efficient for we use last intersection to calc next. Smaller sets.
        res = data.next()
        for run in data:
            res = res.intersection(run)

        return aux

    def max_resources_per_run(self):
        ret = None
        for x in self._list:
            n_resources = len(x)
            if ret is None:
                ret = n_resources
            elif n_resources > ret:
                ret = n_resources

        return ret

    def min_resources_per_run(self):
        ret = None
        for x in self._list:
            n_resources = len(x)
            if ret is None:
                ret = n_resources
            elif n_resources < ret:
                ret = n_resources

    def avg_resources_per_run(self):
        suma = 0

        for x in self._list:
            suma += n_resources

        return int(suma / len(data))

    def can_join(self, other):
        """Returns wheter the two RunCollection (self, and other) can be joined or not."""

        result = True
        if not (self.get_id() is None) and not (other.get_id() is None):
            if self.get_id() != other.get_id():
                result = False
        elif self.get_name() != other.get_name():
            result = False

        return result

    def join(self, other, compatible=False):
        """Attempts joining self with other. If compatible is True, they will only joined if they have the same id or name."""

        joined = True

        if compatible:
            joined = self.can_join(other)

        if joined:
            for selfrun in self.get_runs():
                for otherrun in other.get_runs():
                    selfrun.join(otherrun, compatible)
        _logger.debug("%r joined with %r" % (self, other))
        return joined

    def __sizeof__(self):
        suma = getsizeof(self._name)
        for x in self._list:
            suma += getsizeof(x)

        return suma


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
