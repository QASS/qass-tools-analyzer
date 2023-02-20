Changelog
*********
All notable changes to this project will be documented in this file simultaneously to implemented Git pipelines.

Unreleased
""""""""""
Planned changes for next releases will be noted here. If you have any suggestions, please contact: ewiebelitz@qass.net, nosmers@qass.net, cradek@qass.net.

buffer_metadata_cache
~~~~~~~~~~~~~~~~~~~~~
* More convenient interface to retrieve .. py:class:: BufferMetadata objects
* Interface with the Analyzer Database

2.2
***
:Date: February 20, 2023
:Contributor: Nicklas Osmers

New Features
------------
* It's now possible to retrieve the declarative_base of the .. py:class:: BufferMetadataCache by using .. py:function:: get_declarative_base.

    Example:

    .. code-block:: python
        :linenos:
        
        from qass.tools.analyzer.buffer_metadata_cache import get_declarative_base

        Base = get_declarative_base()
        class MyNewTableMapping(Base):
            __tablename__ = "my_new_table_mapping"
            # ...

* The .. py:method:: BufferMetadataCache.create_session() will now create all tables that are created with it's declarative_base.
* Add more docstrings