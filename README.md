# CircuitPython Manager

[![PyPI](https://img.shields.io/pypi/v/circman.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/circman.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/circman)][python version]
[![License](https://img.shields.io/pypi/l/circman)][license]

[![Read the documentation at https://circman.readthedocs.io/](https://img.shields.io/readthedocs/circman/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/rbedia/circman/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/rbedia/circman/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/circman/
[status]: https://pypi.org/project/circman/
[python version]: https://pypi.org/project/circman
[read the docs]: https://circman.readthedocs.io/
[tests]: https://github.com/rbedia/circman/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/rbedia/circman
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

CircuitPython Manager helps with deploying projects to CircuitPython devices.

## Features

- Automatically detects CircuitPython device path.
- Backs up the CircuitPython device before deploying to allow recovery.
- Simple command to restore a backup to the CircuitPython device in case something goes wrong.

## Requirements

- Linux. May work elsewhere but not tested.

## Installation

You can install _CircuitPython Manager_ via [pip] from [PyPI]:

```console
$ pip install circman
```

## Quick Start

Connect your CircuitPython device to your computer using USB and wait for the
mount to appear.

Change to the directory of your CircuitPython project. The default is for the
project source code to be in "src/" relative to the project directory.

Then run the deploy.

~~~console
$ circman deploy
~~~

A backup of the CircuitPython device will be created and then the project source code will be copied to the CircuitPython device.

If you need to restore the code from before the deploy use the restore command.

~~~console
$ circman restore
~~~

To list all available backups:

~~~console
$ circman list
~~~

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_CircuitPython Manager_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

Device path detection code (`find_device()`) was copied from Adafruit's [circup] project.

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[circup]: https://github.com/adafruit/circup
[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/rbedia/circman/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/rbedia/circman/blob/main/LICENSE
[contributor guide]: https://github.com/rbedia/circman/blob/main/CONTRIBUTING.md
[command-line reference]: https://circman.readthedocs.io/en/latest/usage.html
