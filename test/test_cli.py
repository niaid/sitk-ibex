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
from click.testing import CliRunner
from sitkibex.cli import cli
import os.path
import pytest


def _data_files():
    """
    A dictionary of test data file names to full paths.
    """

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    file_dic = {}
    for f in os.listdir(data_dir):
        full_path = os.path.join(data_dir, f)
        if os.path.isfile(full_path):
            file_dic[f] = full_path

    return file_dic


data_files = _data_files()


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert not result.exception


def test_cli_reg_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["registration", "--help"])
    assert not result.exception


reg_args = [
    ["registration", data_files["panel1.nrrd"] + "@JOJO", data_files["panel2.nrrd"] + "@JOJO", "out.txt"],
    ["registration", data_files["panel1.nrrd"] + "@4", data_files["panel2.nrrd"] + "@4", "out.txt"],
    ["registration", data_files["panel1.nrrd"] + "@Ch5", data_files["panel2.nrrd"] + "@CH5", "out.txt"],
    ["registration", data_files["vpanel1.nrrd"] + "@JOJO", data_files["panel2.nrrd"] + "@CH5", "out.txt"],
    ["registration", data_files["vpanel1.nrrd"] + "@4", data_files["panel2.nrrd"] + "@CH5", "out.txt"],
]


@pytest.mark.parametrize("cli_args", reg_args)
def test_cli_reg(cli_args):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, cli_args)

    assert not result.exception


resample_args = [
    "resample {} {} -o test.nrrd".format(data_files["panel1.nrrd"], data_files["panel2.nrrd"]),
    "resample {} {}@Ch1 -o test.nrrd".format(data_files["panel1.nrrd"], data_files["panel2.nrrd"]),
    "resample --fusion {}@JOJO {}@JOJO -o test.nrrd".format(data_files["panel1.nrrd"], data_files["panel2.nrrd"]),
    "resample  --bin 2 --fusion --projection {}@1 {}@Ch1 -o test.png".format(
        data_files["panel1.nrrd"], data_files["panel2.nrrd"]
    ),
]


@pytest.mark.parametrize("cli_args", resample_args)
def test_cli_resample(cli_args):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, cli_args.split())
    assert not result.exception


def test_cli_resample_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["resample", "--help"])
    assert not result.exception
