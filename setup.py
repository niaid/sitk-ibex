#
#  Copyright Bradley Lowekamp
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from setuptools import setup, find_packages

with open("README.rst", "r") as fp:
    long_description = fp.read()

with open("requirements.txt", "r") as fp:
    requirements = list(filter(bool, (line.strip() for line in fp)))

with open("requirements-dev.txt", "r") as fp:
    dev_requirements = list(filter(bool, (line.strip() for line in fp)))


setup(
    name="sitkibex",
    use_scm_version={"local_scheme": "dirty-tag"},
    author=["Bradley Lowekamp"],
    author_email="bioinformatics@niaid.nih.gov",
    description="Image registration for iterative fluorescence microscopy",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/niaid/sitk-ibex",
    packages=find_packages(exclude=("test",)),
    license="Apache 2.0",
    entry_points={"console_scripts": ["sitkibex = sitkibex.cli:cli"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
    install_requires=requirements,
    tests_require=dev_requirements,
    setup_requires=["setuptools_scm"],
)
