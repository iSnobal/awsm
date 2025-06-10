import unittest
from unittest.mock import MagicMock, patch
import datetime
import pytz
import os

import pandas as pd

from awsm.cli import (
    output_for_date, set_previous_day_outputs, set_single_day, mod_config,
    run_awsm_daily, DATE_FORMAT, DATE_TIME_FORMAT, DAY_HOURS,
)

class TestOutputForDate(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.cfg = {
            'time': {
                'time_zone': 'UTC'
            },
            'paths': {
                'path_dr': '/data/output',
                'basin': 'test_basin',
                'project_name': 'test_project'
            }
        }

    @patch('smrf.utils.utils.water_day')
    def test_output_for_date(self, mock_water_day):
        test_date = datetime.datetime(2023, 4, 15, 12, 0)
        mock_water_day.return_value = (197, 2023)

        result = output_for_date(self.mock_config, test_date)

        expected_path = os.path.join(
            '/data/output',
            'test_basin',
            'wy2023',
            'test_project',
            f'run{test_date.strftime(DATE_FORMAT)}'
        )
        self.assertEqual(result, expected_path)
        mock_water_day.assert_called_once()
        # Check that tzinfo is set to UTC
        called_date = mock_water_day.call_args[0][0]
        self.assertEqual(called_date.tzinfo, pytz.UTC)

    @patch('smrf.utils.utils.water_day')
    def test_output_for_date_path_format(self, mock_water_day):
        test_date = datetime.datetime(2020, 1, 2, 3, 4)
        mock_water_day.return_value = (94, 2020)

        result = output_for_date(self.mock_config, test_date)

        self.assertTrue(result.endswith('run20200102'))
        self.assertIn('wy2020', result)
        self.assertIn('test_basin', result)
        self.assertIn('test_project', result)

class TestSetPreviousDayOutputs(unittest.TestCase):
    @patch('awsm.cli.output_for_date')
    def test_set_previous_day_outputs_sets_paths(self, mock_output_for_date):

        mock_config = MagicMock()
        mock_config.raw_cfg = {
            'files': {},
            'precip': {}
        }
        start_date = pd.Timestamp('2023-04-16 00:00')
        prev_day = start_date - pd.to_timedelta(1, unit='D')
        prev_output_path = '/path/to/previous_output'
        mock_output_for_date.return_value = prev_output_path

        result_config = set_previous_day_outputs(mock_config, start_date)

        mock_output_for_date.assert_called_once_with(mock_config, prev_day)
        self.assertEqual(
            mock_config.raw_cfg['files']['init_file'],
            os.path.join(prev_output_path, 'snow.nc')
        )
        self.assertEqual(
            mock_config.raw_cfg['precip']['storm_days_restart'],
            os.path.join(prev_output_path, 'storm_days.nc')
        )
        self.assertIs(result_config, mock_config)

class TestSetSingleDay(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.raw_cfg = {
            'time': {}
        }

    def test_set_single_day_with_datetime(self):
        start_date_dt = pd.Timestamp('2022-12-01 05:00')
        config, returned_start_date = set_single_day(self.mock_config, start_date_dt)

        expected_start = pd.to_datetime(start_date_dt)
        expected_end = expected_start + DAY_HOURS

        self.assertEqual(
            config.raw_cfg['time']['start_date'],
            expected_start.strftime(DATE_TIME_FORMAT)
        )
        self.assertEqual(
            config.raw_cfg['time']['end_date'],
            expected_end.strftime(DATE_TIME_FORMAT)
        )
        self.assertEqual(returned_start_date, expected_start)

    def test_set_single_day_returns_same_config_instance(self):
        start_date = '2021-07-10'
        config, _ = set_single_day(self.mock_config, start_date)
        self.assertIs(config, self.mock_config)


class TestModConfig(unittest.TestCase):
    @patch('awsm.cli.apply_and_cast_variables')
    def setUp(self, mock_apply_and_cast):
        config = {
            'time': {
                'start_date': '2023-01-01 00:00',
                'end_date': '2023-01-02 00:00'
            },
            'files': {},
            'grid': {},
            'awsm master': {},
        }
        self.config = MagicMock()
        self.config.raw_cfg = config

        # Configure mocks
        self.mock_apply_and_cast = mock_apply_and_cast
        mock_apply_and_cast.side_effect = lambda config: config

    @patch('awsm.cli.parse_config')
    def test_mod_config_no_previous_no_threshold(self, mock_parse_config):
        mock_parse_config.return_value = self.config

        start = pd.Timestamp('2023-01-03 00:00')
        end = pd.Timestamp('2023-01-03 23:00')

        config = mod_config(
            self.config,
            start,
            no_previous=True,
            threshold=False,
            medium_threshold=25
        )

        self.assertEqual(
            config.raw_cfg['time']['start_date'],
            start.strftime(DATE_TIME_FORMAT)
        )
        self.assertEqual(
            config.raw_cfg['time']['end_date'],
            end.strftime(DATE_TIME_FORMAT)
        )
        # No previous
        self.assertEqual(
            config.raw_cfg['files']['init_type'],
            None
        )
        self.assertEqual(
            config.raw_cfg['files']['init_file'],
            None
        )
        # No Threshold
        self.assertEqual(
            config.raw_cfg['grid'],
            {}
        )

    @patch('awsm.cli.set_previous_day_outputs')
    @patch('awsm.cli.parse_config')
    def test_mod_config_with_previous_no_threshold(
        self, mock_parse_config, mock_previous_outputs
    ):
        mock_parse_config.return_value = self.config
        mock_previous_outputs.return_value = self.config

        start = pd.Timestamp('2023-01-03 00:00')
        end = pd.Timestamp('2023-01-03 23:00')

        config = mod_config(
            self.config,
            start,
            no_previous=False,
            threshold=False,
            medium_threshold=25
        )

        self.assertEqual(
            config.raw_cfg['time']['start_date'],
            start.strftime(DATE_TIME_FORMAT)
        )
        self.assertEqual(
            config.raw_cfg['time']['end_date'],
            end.strftime(DATE_TIME_FORMAT)
        )
        mock_previous_outputs.assert_called_once()

    @patch('awsm.cli.output_for_date')
    @patch('awsm.cli.set_previous_day_outputs')
    @patch('awsm.cli.parse_config')
    def test_mod_config_with_previous_and_threshold(
        self, mock_parse_config, mock_previous_outputs, mock_output_for_date
    ):
        mock_parse_config.return_value = self.config
        mock_previous_outputs.return_value = self.config
        mock_output_for_date.return_value = '/path/to/previous'

        start = pd.Timestamp('2023-01-03 00:00')
        end = pd.Timestamp('2023-01-03 23:00')

        config = mod_config(
            self.config,
            start,
            no_previous=False,
            threshold=True,
            medium_threshold=25
        )

        self.assertEqual(
            config.raw_cfg['time']['start_date'],
            start.strftime(DATE_TIME_FORMAT)
        )
        self.assertEqual(
            config.raw_cfg['time']['end_date'],
            end.strftime(DATE_TIME_FORMAT)
        )
        mock_previous_outputs.assert_called_once()
        mock_output_for_date.assert_called_once()
        self.assertEqual(
            config.raw_cfg['grid']['thresh_medium'],
            25
        )
        self.assertEqual(
            config.raw_cfg['awsm master']['run_smrf'],
            False
        )

class TestRunAwsmDaily(unittest.TestCase):
    @patch('awsm.cli.apply_and_cast_variables')
    def setUp(self, mock_apply_and_cast):
        config = {
            'time': {
                'start_date': pd.to_datetime('2023-01-01 00:00'),
                'end_date': pd.to_datetime('2023-01-04 23:00')
            },
        }
        self.config = MagicMock()
        self.config.raw_cfg = config

        # Configure mocks
        self.mock_apply_and_cast = mock_apply_and_cast
        mock_apply_and_cast.side_effect = lambda config: config

    @patch('awsm.cli.run_awsm')
    @patch('awsm.cli.set_previous_day_outputs')
    @patch('awsm.cli.parse_config')
    def test_run_multiple_days(
        self, mock_parse_config, mock_previous_outputs, mock_run_awsm
    ):
        mock_parse_config.return_value = self.config
        mock_previous_outputs.side_effect = lambda config, day: config

        run_awsm_daily(self.config)

        assert mock_run_awsm.call_count == 4
        for index, arguments in enumerate(mock_previous_outputs.call_args_list):
            date = arguments[0][1]
            self.assertEqual(
                date,
                self.config.raw_cfg['time']['start_date'] + pd.Timedelta(days=index)
            )