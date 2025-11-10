import os
import shutil
import unittest
from copy import deepcopy
from pathlib import Path

import netCDF4 as nc
import numpy as np
from inicheck.tools import get_user_config

import awsm


class AWSMTestCase(unittest.TestCase):
    """
    The base test case for AWSM that will load in the configuration file
    and store as the base config. Also will remove the output
    directory upon tear down.
    Runs the short simulation over reynolds mountain east
    """

    DIST_VARIABLES = frozenset(
        [
            "air_temp",
            "cloud_factor",
            "precip",
            "thermal",
            "vapor_pressure",
            "wind",
        ]
    )

    BASE_INI_FILE_NAME = "config.ini"

    test_dir = Path(awsm.__file__).parent.joinpath("tests")
    basin_dir = test_dir.joinpath("basins", "RME")
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)

    @property
    def dist_variables(self):
        if self._dist_variables is None:
            self._dist_variables = list(self.DIST_VARIABLES)
        return self._dist_variables

    @property
    def base_config(self):
        return self.base_config_copy()

    @classmethod
    def base_config_copy(cls):
        return deepcopy(cls._base_config)

    @classmethod
    def load_base_config(cls):
        cls._base_config = get_user_config(cls.config_file, modules=["smrf", "awsm"])

    @classmethod
    def configure(cls):
        cls.run_config = cls.base_config_copy()

    @classmethod
    def setUpClass(cls):
        cls.load_base_config()
        cls.create_output_dir()
        cls.configure()

    @classmethod
    def tearDownClass(cls):
        cls.remove_output_dir()
        delattr(cls, "output_dir")

    @classmethod
    def create_output_dir(cls):
        folder = os.path.join(cls._base_config.cfg["paths"]["path_dr"])

        # Remove any potential files to ensure fresh run
        if os.path.isdir(folder):
            shutil.rmtree(folder)

        os.makedirs(folder)
        cls.output_dir = Path(folder)

    @classmethod
    def remove_output_dir(cls):
        if hasattr(cls, "output_dir") and os.path.exists(cls.output_dir):
            shutil.rmtree(cls.output_dir)

    def setUp(self):
        self._dist_variables = None

    def compare_hrrr_gold(self):
        """
        Compare the model results with the gold standard
        """
        [
            self.compare_netcdf_files(file_name.name)
            for file_name in self.gold_dir.glob("*.nc")
        ]

    def compare_netcdf_files(self, output_file, variable):
        """
        Compare two netcdf files to ensure that they are identical. The
        tests will compare the attributes of each variable and ensure that
        the values are exact
        """

        gold = nc.Dataset(self.gold_dir.joinpath(output_file))
        gold.set_always_mask(False)

        test = nc.Dataset(self.output_path.joinpath(output_file))
        test.set_always_mask(False)

        # just compare the variable desired with time,x,y
        variables = ["time", "x", "y", variable]
        for var_name in variables:
            # Check attribute existence
            assert var_name in test.variables, (
                f"Variable: {var_name} not found in test output file"
            )

            # Compare the dimensions of gold are still in the tests
            # The test will have 'description' and 'long_name' additionally
            self.assertTrue(
                np.all(
                    np.isin(
                        gold.variables[var_name].ncattrs(),
                        test.variables[var_name].ncattrs(),
                    )
                ),
                "Missing variable attribute. "
                f" Gold: {gold.variables[var_name].ncattrs()}"
                f" Test: {test.variables[var_name].ncattrs()}",
            )

            # Note: With the change to only store four significant digits for
            #       SMRF outputs, the test files started to deviate a lot more
            #       to current gold files through propagation of floating point
            #       differences. This bumped the atol and rtol values up. SMRF PR#10
            tolerances = dict(rtol=0.015, atol=0.01)
            if var_name == "cold_content":
                # Cold content was the only variable that showed higher magnitude
                tolerances["rtol"] = 0.04

            if var_name == variable:
                for time_slice in range(len(gold.variables[var_name])):
                    np.testing.assert_allclose(
                        gold.variables[var_name][time_slice][time_slice, ...],
                        test.variables[var_name][time_slice][time_slice, ...],
                        **tolerances,
                        err_msg=f"Variable: {var_name} at time slice {time_slice} did not match gold standard",
                    )
            else:
                np.testing.assert_allclose(
                    gold.variables[var_name][:],
                    test.variables[var_name][:],
                    **tolerances,
                    err_msg=f"Variable: {var_name} did not match gold standard",
                )

        gold.close()
        test.close()
