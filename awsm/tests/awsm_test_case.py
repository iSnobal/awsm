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
    and store as the base config. Also removes the output directory upon tear down.
    """

    # This matches the significant digits set in output files.
    # See :data:`awsm.interface.pysnobal_io.LEAST_SIGNIFICANT_DIGITS`
    VARIABLE_TOLERANCE = 0.0001

    BASE_INI_FILE_NAME = "config.ini"

    test_dir = Path(awsm.__file__).parent.joinpath("tests")
    basin_dir = test_dir.joinpath("basins", "RME")
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)
    netcdf_comparison_failed = False

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

    def setUp(self):
        super().setUp()
        self.__class__.netcdf_comparison_failed = False

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
        if not cls.netcdf_comparison_failed:
            if hasattr(cls, "output_dir") and os.path.exists(cls.output_dir):
                shutil.rmtree(cls.output_dir, ignore_errors=True)

    def compare_netcdf_files(self, output_file, output_variables: list) -> None:
        """
        Compare two netcdf files to ensure that the list of variables are identical.
        The tests will also compare the attributes of each variable and ensure that
        the values are exact

        Args:
            output_file : str
                The name of the NetCDF file to compare.
            output_variables : list
                The list of variable names in the NetCDF file to compare beyond the default
                variables ("time", "x", "y").

        Raises
        ------
        AssertionError
            If a mismatch is detected between the gold standard and the test file,
            including missing variables, missing attributes, and value mismatches.
        """

        gold = nc.Dataset(self.gold_dir.joinpath(output_file))
        gold.set_always_mask(False)

        test = nc.Dataset(self.output_path.joinpath(output_file))
        test.set_always_mask(False)

        try:
            variables = ["time", "x", "y"] + output_variables
            for var_name in variables:
                # Check attribute existence
                assert var_name in test.variables, (
                    f"Variable: {var_name} not found in test output file"
                )

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

                # Only compare the actual values and not the dimensions
                if var_name in output_variables:
                    for time_slice in range(len(gold.variables[var_name])):
                        np.testing.assert_allclose(
                            gold.variables[var_name][time_slice, ...],
                            test.variables[var_name][time_slice, ...],
                            rtol=self.VARIABLE_TOLERANCE,
                            err_msg=f"Variable: {var_name} at time slice {time_slice} did not match gold standard",
                        )
        except AssertionError:
            self.__class__.netcdf_comparison_failed = True
            raise
        finally:
            gold.close()
            test.close()
