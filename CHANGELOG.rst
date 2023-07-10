Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


[0.3.0] - 2023-07-10
--------------------

Added
~~~~~

* bulk operating for `add` and `delete` operations

Fixed
~~~~~

* adds `check_resource_identifier_object` check on parser to check update operation correctly


[0.2.0] - 2023-07-06
--------------------

Added
~~~~~

* to-one relationship update
* to-many relationship update

Fixed
~~~~~

* fixes some json pointers for some parse errors


Changed
~~~~~~~

* implemented custom exception classes to simplify code
* uses constant string values to reduce code duplications

[0.1.0] - 2023-07-04
--------------------

Added
~~~~~

* sequential handling for add, update and remove operation code
* detailed error responses with indexed source pointing
