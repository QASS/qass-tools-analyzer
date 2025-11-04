import json
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from .buffer_parser import InvalidFileError


@dataclass
class MockBuffer:
    """Mock buffer class that is able to parse JSON encoded files.
    All attributes in the JSON are added as fields in the object.

    .. note::
        Currently this only allows the mocking of header attributes

    Creating a Mock Metadata Object::

        # This object can either be created using the constructor
        from qass.tools.analyzer.testing import MockBuffer
        buffer = MockBuffer("/my/path/to/file", header_hash="0", process=1)

    Loading a file::

        # By writing the desired attributes to a json file
        import json
        from pathlib import Path

        from qass.tools.analyzer.testing import MockBuffer

        file = Path("testfile.json")
        with open("file", "w") as f:
            json.dump({"header_hash": "0", "process": 1})
        buffer = MockBuffer(file)
        # this step will load the json file into the dataclass
        with buffer:
            pass
    """

    def __init__(self, filepath: Union[Path, str], **kwargs):
        self.filepath = filepath
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __enter__(self):
        """
        Opens the file specified by ``self.filepath``, parses its JSON content,
        and populates the instance attributes with the loaded data. All key-value
        pairs from the JSON file are dynamically set as attributes on this instance.

        :returns: The instance itself with attributes populated from the file.
        :rtype: self
        :raises InvalidFileError: If the file is not a valid Buffer JSON file.
        :raises FileNotFoundError: If the specified filepath does not exist.
        :raises PermissionError: If there are insufficient permissions to read the file.

        .. note::
           This method is automatically called when entering a ``with`` statement.

        .. code-block:: python
            :linenos:
            with BufferObject() as buffer:
                # buffer attributes are now loaded from file
                print(buffer.data)
        """
        with open(self.filepath, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                raise InvalidFileError("Not a Buffer file")
        for key, value in data.items():
            setattr(self, key, value)
        return self

    def __exit__(self, *args, **kwargs):
        pass
