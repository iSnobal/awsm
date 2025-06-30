from unittest.mock import MagicMock, call, patch

import pandas as pd
from inicheck.tools import cast_all_variables

import awsm
from awsm.framework.framework import AWSM
from awsm.interface.ipysnobal import PySnobal
from awsm.tests.awsm_test_case_lakes import AWSMTestCaseLakes


class TestPySnobal(AWSMTestCaseLakes):
    """
    Testing using Lakes:
        - ipysnobal
        - initialize from init.nc file
        - loading from netcdf
    """

    def setUp(self):
        super().setUp()

        self.run_config.raw_cfg['time']['start_date'] = '2019-10-01 00:00'
        self.run_config.raw_cfg['files']['init_type'] = 'netcdf'

        self.run_config.apply_recipes()
        run_config = cast_all_variables(self.run_config, self.run_config.mcfg)
        awsm_run = AWSM(run_config, testing=True)
        self.subject = PySnobal(awsm_run)
        self.subject.initialize_ipysnobal()

    @patch("awsm.interface.ipysnobal.SMRFConnector")
    @patch("copy.deepcopy")
    def test_load_previous_day_attributes(self, mock_copy, mock_smrf):
        awsm_copy = MagicMock()
        mock_copy.return_value = awsm_copy

        self.subject.load_previous_day()

        # Comparing the str here since the AWSM time is created via pandas
        # date_range and has an 'freq' attribute
        previous_day = str(pd.Timestamp("2019-09-30 23:00:00+0000"))

        assert str(awsm_copy.start_date) == previous_day
        assert str(awsm_copy.end_date) == previous_day
        assert call.set_path_output() in awsm_copy.method_calls
        mock_smrf.assert_called_once_with(awsm_copy)

    @patch.object(
        awsm.interface.smrf_connector.SMRFConnector, "get_timestep_netcdf"
    )
    @patch("netCDF4.Dataset")
    def test_load_previous_day_file_loading(self, mock_nc_file, _mock_smrf):
        self.subject.load_previous_day()
        # Grab the last two path elements for each openend file
        opened_files = [
            "/".join(file[0][0].rsplit("/", 2)[-2:])
            for file in mock_nc_file.call_args_list
        ]
        previous_day = "20190930"

        for forcing_data in PySnobal.FORCING_VARIABLES:
            if forcing_data == "soil_temp":
                # Soil temperature is a constant value, not a file
                continue

            file_path = f"run{previous_day}_{previous_day}/{forcing_data}.nc"
            assert file_path in opened_files, (
                f"File {file_path} not found in opened files: {opened_files}"
            )

    @patch("netCDF4.Dataset")
    @patch.object(awsm.interface.ipysnobal.SMRFConnector, "get_timestep_netcdf")
    def test_load_previous_day_data_loading(
        self, mock_smrf_connector, _mock_nc_file
    ):
        mock_data = MagicMock()
        mock_smrf_connector.return_value = mock_data

        self.subject.load_previous_day()

        assert str(mock_smrf_connector.call_args[0][0]) == (
            str(pd.Timestamp("2019-09-30 23:00:00+0000"))
        )
        assert self.subject.input1 == mock_data

    @patch("netCDF4.Dataset")
    @patch.object(awsm.interface.ipysnobal.SMRFConnector, "get_timestep_netcdf")
    @patch.object(awsm.interface.ipysnobal.PySnobal, "convert_temperatures")
    def test_load_previous_day_temperature_convert(
        self, mock_temperature, mock_smrf_connector, _mock_nc_file
    ):
        mock_data = MagicMock()
        mock_smrf_connector.return_value = mock_data

        self.subject.load_previous_day()

        mock_temperature.assert_called_once_with(mock_data)

    @patch('awsm.interface.ipysnobal.SMRFConnector')
    def test_load_previous_day_file_close(self, mock_smrf_connector):
        self.subject.load_previous_day()

        assert call().close_netcdf_files() in mock_smrf_connector.mock_calls

    @patch("netCDF4.Dataset")
    @patch.object(awsm.interface.ipysnobal.PySnobal, "load_previous_day")
    def test_load_first_timestep_inputs_previous_day(
        self, mock_load_day, _mock_nc
    ):
        self.subject.date_time = [
            pd.Timestamp('2019-10-01 00:00')
        ]
        self.subject.awsm.model_init.init_file = MagicMock()

        self.subject.load_first_timestep_inputs()

        mock_load_day.assert_called_once()

    @patch("netCDF4.Dataset")
    @patch.object(awsm.interface.ipysnobal.PySnobal, "get_timestep_inputs")
    def test_load_first_timestep_inputs_first_timestep(
        self, mock_timestamp, _mock_nc
    ):
        self.subject.date_time = [
            pd.Timestamp('2019-10-01 00:00')
        ]
        self.subject.awsm.model_init.init_file = None

        assert len(self.subject.date_time) == 1

        self.subject.load_first_timestep_inputs()

        mock_timestamp.assert_called_once()
        assert len(self.subject.date_time) == 0

    @patch("netCDF4.Dataset")
    @patch.object(awsm.interface.ipysnobal.PySnobal, "get_timestep_inputs")
    def test_load_first_timestep_inputs_non_zero_hour(
        self, mock_timestamp, _mock_nc
    ):
        self.subject.date_time = [
            pd.Timestamp('2019-10-01 06:00')
        ]
        self.subject.awsm.model_init.init_file = MagicMock()

        assert len(self.subject.date_time) == 1

        self.subject.load_first_timestep_inputs()

        mock_timestamp.assert_called_once()
        assert len(self.subject.date_time) == 0
