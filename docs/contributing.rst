Contributing
============

The pull requests, bug reports, feature suggestions or even demo use cases contributed by the pyircbot community are all
highly appreciated and a valuable asset to the project.

This document outlines best practices and conditions for contributing changes pyircbot.


Sending a Pull Request
----------------------

The pyircbot project does have a couple rules for pull requests:


Where
  While pyircbot's main git repository is hosted on a private server, PRs are welcome on the
  `github mirror <https://github.com/dpedu/pyircbot>`_ of the project.


Linting
  Pyircbot's codebase is linted with flake8. The configuration arguments for flake8 are: ``--max-line-length 120
  --ignore E402,E712,E731,E211 --select E,F``. TODO add a flake8 config file to the repo so these args are codified.


Python versions
  Pyircbot supports the two latest versions of python 3. At present, this is Python 3.6 and 3.7. All changes must be
  compatible with these versions. Using compatibility modules or checking the version at runtime is discouraged; the
  code should be written in a fashion that is interoperable.


Dependencies
  The core of pyircbot - that is, the bot runtime itself and the basic modules needed to operate it - `PingResponder`
  and `Services` - have no dependencies outside python's standard library of modules. All changes must not change this
  condition. The use of 3rd party dependencies in pyircbot modules is allowed, provided the versions used do not
  conflict with modules already in use.

  All 3rd party dependencies must be installable via Pip with no extra setup required (e.g. OS-level packages), with
  some exceptions:

  - Requiring ``git`` for pip links directly to repositories is permitted.

  - Requiring a C/C++ compiler available on the system as well as python headers which are typically required for
    libraries with C/C++ or other native language extensions is permitted. However, requiring additional headers or
    shared libraries is prohibited, unless:

  - Many operating systems provide a ``python3-pip`` or similar package that depends on many other packages that violate
    the above rules, such as openssl headers or sqlite shared libraries. Pyircbot's preferred platform is Ubuntu Bionic,
    and any dependencies of such a package are permitted.

  - These rules apply to code dependencies only, and do not apply to external *services* such as MySQL.

  Modules that require setup or dependencies beyond these rules will not be accepted into the core module set. The
  recommended approach to use such a module is via the ``usermodules`` config directive.

  No set of rules will handle all cases, and discussion or defending a change that violates these rules is encouraged.


Tests
  Please consider the test suite when submitting changes affecting the core runtime and existing modules. Reduction of
  coverage is acceptable, but breaking or removing tests is not. Changes submitted with updated or new tests will
  be fast-tracked.


Contributors to Pyircbot
------------------------

Any change submitted to pyircbot is highly appreciated.

Our contributors, in no particular order:

- `@ollien <https://github.com/ollien>`_ ❤️
- `@medmr1 <https://github.com/medmr1>`_ ❤️
- `@dpedu <https://github.com/dpedu>`_ ❤️
