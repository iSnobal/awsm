import argparse
import copy
import os

import pandas as pd
import pytz
from inicheck.tools import get_user_config, cast_all_variables
from smrf.utils import utils

from awsm.framework.framework import run_awsm

DATE_FORMAT = '%Y%m%d'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M'
DAY_HOURS = pd.to_timedelta(23, unit='h')


def output_for_date(config, date):
    """
    Get absolute folder path for model output of a date

    Parameters
    ----------
    config: UserConfig
        Parsed user config holding path information
    date : datetime
        Date to generate path for

    Returns
    -------
    str
        Absolute path to output folder
    """
    # Get the water year
    tzinfo = pytz.timezone(config.cfg['time']['time_zone'])
    wy = utils.water_day(date.replace(tzinfo=tzinfo))[1]

    # Get base output location
    paths = config.cfg['paths']
    base_output = os.path.join(
        paths['path_dr'],
        paths['basin'],
        'wy{}'.format(wy),
        paths['project_name'],
    )

    return os.path.join(
        base_output,
        f'run{format(date.strftime(DATE_FORMAT))}',
    )


def set_previous_day_outputs(config, start_date):
    """
    Set the previous day output for snow and storm days in the config

    Parameters
    ----------
    config : UserConfig
        Parsed user config holding path information
    start_date : datetime
        Date to generate path for

    Returns
    -------
    UserConfig
        Updated user config with previous day output paths set
    """
    prev_day = start_date - pd.to_timedelta(1, unit='D')
    previous_output = output_for_date(config, prev_day)

    # Snow state variables
    config.raw_cfg['files']['init_file'] = os.path.join(
        previous_output, 'snow.nc'
    )
    # Snowfall days
    config.raw_cfg['precip']['storm_days_restart'] = os.path.join(
        previous_output, 'storm_days.nc'
    )

    return config


def apply_and_cast_variables(config):
    """
    Apply recipes and cast all variables in the config

    Parameters
    ----------
    config : UserConfig
        Parsed user config to apply recipes and cast variables

    Returns
    -------
    UserConfig
        Updated user config with applied recipes and cast variables
    """
    config.apply_recipes()
    return cast_all_variables(config, config.mcfg)


def parse_config(config_file):
    """
    Create config instance and parse all values for AWSM and SMRF

    Parameters
    ----------
    config_file : str
        Full path to .ini file

    Returns
    -------
    UserConfig
        Parsed user config (.ini file) to use for the model run
    """
    config = get_user_config(config_file, modules=['smrf', 'awsm'])

    return apply_and_cast_variables(config)


def set_single_day(config, start_date):
    """
    Set the start and end date for a single day run

    Parameters
    ----------
    config : UserConfig
        Parsed user config holding path information
    start_date : str
        Day to run

    Returns
    -------
    Tupel of UserConfig and start_date
    """
    start_date = pd.to_datetime(start_date)
    end_date = start_date + DAY_HOURS

    config.raw_cfg['time']['start_date'] = start_date.strftime(DATE_TIME_FORMAT)
    config.raw_cfg['time']['end_date'] = end_date.strftime(DATE_TIME_FORMAT)

    return config, start_date


def mod_config(
    config_file, start_date, no_previous, threshold, medium_threshold
):
    """
    Modify the configuration file to run for a single day

    Parameters
    ----------
    config_file : str
        Full path to .ini file
    start_date : str
        Day to run
    no_previous : bool
        Should the previous day be used to initialize the model
    threshold : bool
        Run model with different mass threshold
    medium_threshold : int
        Medium mass threshold value

    Returns
    -------
    UserConfig
        Updated config to use for the model run
    """
    config = parse_config(config_file)
    config, start_date = set_single_day(config, start_date)

    if no_previous:
        # Run without initialization from previous day
        config.raw_cfg['files']['init_type'] = None
        config.raw_cfg['files']['init_file'] = None
    else:
        config = set_previous_day_outputs(config, start_date)

    if threshold:
        config.raw_cfg['grid']['thresh_medium'] = medium_threshold
        print(
            f"** Running model with medium mass theshold of: {medium_threshold}"
        )
        # No need to run SMRF again when changing the mass threshold for iSnobal
        config.raw_cfg['awsm master']['run_smrf'] = False

        # Remove files from previous runs before attempting a re-run
        current_day_output = output_for_date(config, start_date)

        snow_nc = os.path.join(current_day_output, 'snow.nc')
        if os.path.exists(snow_nc):
            os.remove(snow_nc)

        em_nc = os.path.join(current_day_output, 'em.nc')
        if os.path.exists(em_nc):
            os.remove(em_nc)

    return apply_and_cast_variables(config)


def run_awsm_daily(config_file):
    """
    Run each day seperately. Calls run_awsm
    """
    config = parse_config(config_file)

    # Days to loop over
    start_day = pd.to_datetime(
        config.raw_cfg['time']['start_date'].strftime(DATE_FORMAT)
    )
    end_day = pd.to_datetime(
        config.raw_cfg['time']['end_date'].strftime(DATE_FORMAT)
    )

    # Daily runs
    while start_day <= end_day:
        new_config = copy.deepcopy(config)
        new_config, start_day = set_single_day(new_config, start_day)

        new_config = set_previous_day_outputs(new_config, start_day)
        new_config = apply_and_cast_variables(new_config)

        # Run awsm for the day
        run_awsm(new_config)

        start_day += pd.to_timedelta(1, unit='D')


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Run AWSM for a single day'
    )

    parser.add_argument(
        '-c', '--config-file',
        required=True,
        help='Config file that will be modified for the current run date'
    )
    parser.add_argument(
        '-sd', '--start_date',
        required=False,
        default=None,
        help='start date for run'
    )
    parser.add_argument(
        "-np", "--no_previous",
        action="store_true",
        default=False,
        help="Doesn't need to find a previous snow state "
             "from directory structure"
    )
    parser.add_argument(
        '-t', '--threshold',
        action="store_true",
        default=False,
        help='Run iSnobal with different mass threshold'
    )
    parser.add_argument(
        '-mt', '--medium-threshold',
        type=int,
        default=25,
        help='Medium mass threshold. Default: 25'
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    # Run a single day only when given a start date via parameters
    if args.start_date is not None:
        # set dates and paths
        new_config = mod_config(
            args.config_file,
            args.start_date,
            args.no_previous,
            args.threshold,
            args.medium_threshold,
        )

        run_awsm(new_config)
    else:
        run_awsm_daily(args.config_file)


if __name__ == '__main__':
    main()
