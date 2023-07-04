import os
import re
from subprocess import check_call

from setuptools import setup
from setuptools.command.build import build


class pre_build(build):

    def run(self):
        check_call("python manage.py compilemessages".split())
        build.run(self)


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]",
                     init_py, re.MULTILINE).group(1)


version = get_version("atomic_operations")

setup(
    cmdclass={
        'pre_build': pre_build
    },
    version=version,
    install_requires=[
        "djangorestframework-jsonapi>=6.0.0"
    ]
)
