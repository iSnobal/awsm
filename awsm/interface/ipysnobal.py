import logging
from datetime import timedelta

import numpy as np
import pandas as pd

from awsm.interface import pysnobal_io
from awsm.interface.ingest_data import StateUpdater
from awsm.interface.smrf_connector import SMRFConnector
from pysnobal import ipysnobal
from pysnobal.c_snobal import snobal

C_TO_K = 273.16
FREEZE = C_TO_K


# Kelvin to Celsius
def K_TO_C(x):
    return x - FREEZE


def check_range(value, min_val, max_val, descrip):
    """
    Check the range of the value
    Args:
        value:  value to check
        min_val: minimum value
        max_val: maximum value
        descrip: short description of input

    Returns:
        True if within range
    """
    if (value < min_val) or (value > max_val):
        raise ValueError(
            "%s (%f) out of range: %f to %f", descrip, value, min_val, max_val
        )
    pass


class PySnobal:
    FORCING_VARIABLES = frozenset(
        [
            "thermal",
            "air_temp",
            "vapor_pressure",
            "wind_speed",
            "net_solar",
            "soil_temp",
            "precip",
            "percent_snow",
            "snow_density",
            "precip_temp",
        ]
    )

    def __init__(self, myawsm):
        """
        PySnobal class to run pysnobal.

        Args:
            myawsm (AWSM): AWSM class instance
        """

        self._logger = logging.getLogger(__name__)
        self.awsm = myawsm
        self.smrf = None
        self.force = None
        self._logger.debug("Initialized PySnobal")

    @property
    def data_time_step(self):
        return self.time_step_info[0]["time_step"]

    @property
    def init_zeros(self):
        return np.zeros_like(self.awsm.topo.dem)

    @property
    def init_ones(self):
        return np.ones_like(self.awsm.topo.dem)

    def initialize_updater(self):
        """
        Initialize the StateUpdater for the simulation
        """

        if self.awsm.update_depth:
            self.updater = StateUpdater(self.awsm)
        else:
            self.updater = None

    def initialize_ipysnobal(self):
        """Initialize iPysnobal. Performs the following:

        1. Create a configuration to pass to iPysnobal based on the configuration file.
        2. Create the time step info for mass and time thresholds.
        3. Initialize the output record dictionary for storing results
        4. Create the output files
        """

        # parse the input arguments
        self.get_args()

        # get the time step info
        self.params, self.time_step_info = ipysnobal.get_timestep_info(
            self.options["constants"], self.options
        )

        # mass thresholds for run time steps
        self.time_step_info[ipysnobal.NORMAL_TIMESTEP]["threshold"] = (
            self.awsm.mass_thresh[0]
        )
        self.time_step_info[ipysnobal.MEDIUM_TIMESTEP]["threshold"] = (
            self.awsm.mass_thresh[1]
        )
        self.time_step_info[ipysnobal.SMALL_TIMESTEP]["threshold"] = (
            self.awsm.mass_thresh[2]
        )

        # get init params
        self.init = self.awsm.model_init.init

        self.output_rec = ipysnobal.initialize(self.init
        )

        # create the output files
        pysnobal_io.output_files(
            self.options, self.init, self.awsm.start_date, self.awsm
        )

        self.time_since_out = 0.0
        self.start_step = 0
        step_time = self.start_step * self.data_time_step

        self.set_current_time(step_time, self.time_since_out)

    def get_args(self):
        """
        Parse the configuration file and returns a dictionary called options.
        Options contains the following keys:

        * z - site elevation (m)
        * t - time steps: data [normal, [,medium [,small]]] (minutes)
        * m - snowcover's maximum h2o content as volume ratio,
        * d - maximum depth for active layer (m),
        * s - snow properties input data file,
        * h - measurement heights input data file,
        * p - precipitation input data file,
        * i - input data file,
        * I - initial conditions
        * o - optional output data file,
        * O - how often output records written (data, normal, all),
        * c - continue run even when no snowcover,
        * K - accept temperatures in degrees K,
        * T - run time steps' thresholds for a layer's mass (kg/m^2)

        To-do: take all the rest of the default and check ranges for the
        input arguments, i.e. rewrite the rest of getargs.c

        """

        # make blank config and fill with corresponding sections
        config = {}

        config["output"] = {
            "frequency": self.awsm.output_freq,
            "location": self.awsm.path_output,
            "nthreads": self.awsm.ipy_threads,
            "output_mode": "data",
            "out_filename": None,
        }

        config["constants"] = self.read_config_constants()

        # ------------------------------------------------------------------------
        # read in the time and ensure a few things
        check_range(self.awsm.time_step, 1.0, 3 * 60, "input data's time step")
        if (self.awsm.time_step > 60) and (self.awsm.time_step % 60 != 0):
            raise ValueError(
                """Data time step > 60 min must be multiple """
                """of 60 min (whole hours)"""
            )

        start_date = self.awsm.start_date

        # create a date time range
        date_time = list(
            pd.date_range(
                start_date,
                self.awsm.end_date,
                freq=timedelta(minutes=config["constants"]["time_step"]),
            )
        )

        config["time"] = {
            "start_date": start_date,
            "end_date": self.awsm.end_date,
            "time_step": self.awsm.time_step,
            "date_time": date_time,
        }
        self.date_time = date_time

        # add to constant sections for time_step_info calculation
        config["constants"]["time_step"] = self.awsm.time_step

        config["inputs"] = {
            "point": None,
            "input_type": self.awsm.ipy_init_type,
            "soil_temp": self.awsm.soil_temp,
        }

        self.options = config

    def read_config_constants(self):
        """Read the configuration and set the constants for iPysnobal.
        These are similar to the arguments that are passed to iSnobal.

        Returns:
            dict: constant values for iSnobal
        """

        constants = {
            "time_step": 60,
            "max-h2o": 0.01,
            "c": True,
            "K": True,
            "mass_threshold": self.awsm.mass_thresh[0],
            "time_z": 0,
            "max_z_s_0": self.awsm.active_layer,
            "z_u": 5.0,
            "z_t": 5.0,
            "z_g": 0.5,
            "relative_heights": True,
        }

        # read in the constants
        c = {}
        for v in self.awsm.config["ipysnobal constants"]:
            c[v] = float(self.awsm.config["ipysnobal constants"][v])
        constants.update(c)  # update the default with any user values

        return constants

    def do_update(self, first_step):
        """If there is an update the the give time step, update the model state

        Returns:
            int: flag if the first step changed
        """

        if self.updater is not None:
            if self.time_step in self.updater.update_dates:
                self.output_rec = self.updater.do_update_pysnobal(
                    self.output_rec, self.time_step
                )
                first_step = 1

        return first_step

    @staticmethod
    def convert_temperatures(data: dict) -> dict:
        """
        Convert temperatures in dictionary from Celsius to kelvin

        Args:
            data : dict
                Dictionary of forcing variables

        Returns:
            Original dictionary with converted temperatures
        """
        data["T_a"] = data["T_a"] + FREEZE
        data["T_pp"] = data["T_pp"] + FREEZE
        data["T_g"] = data["T_g"] + FREEZE

        return data

    def get_timestep_inputs(self) -> dict:
        """
        Get all the forcing variable data from SMRF from the netCDF files.

        Returns:
            dict: dict of input values for all forcing variables
        """

        data = self.awsm.smrf_connector.get_timestep_netcdf(self.time_step)

        return self.convert_temperatures(data)

    def set_current_time(self, step_time, time_since_out):
        """Set the current time and time since out

        Args:
            step_time (int): current time as integer from start
            time_since_out (int): time since out for the model results
        """

        self.output_rec["current_time"] = step_time * self.init_ones
        self.output_rec["time_since_out"] = time_since_out * self.init_ones

    def do_data_tstep(self, first_step):
        """
        Run iSnobal over the grid

        Args:
            first_step (int): flag if first step or not

        Raises:
            ValueError: catch error in iSnobal
        """

        rt = snobal.do_tstep_grid(
            self.input1,
            self.input2,
            self.output_rec,
            self.time_step_info,
            self.options["constants"],
            self.params,
            first_step=first_step,
            nthreads=self.awsm.ipy_threads,
        )

        if rt != -1:
            raise ValueError(
                "ipysnobal error on time step {}, pixel {}".format(
                    self.time_step, rt
                )
            )

    def run_full_timestep(self):
        """
        Run the full timestep for iPysnobal. Includes getting the input,
        running iPysnobal for the timestep, copying the input data and
        outputting the results if needed.
        """

        self._logger.info(
            "running iPysnobal for timestep: {}".format(self.time_step)
        )

        self.input2 = self.get_timestep_inputs()

        first_step = self.step_index
        first_step = self.do_update(first_step)

        self.do_data_tstep(first_step)

        self.input1 = self.input2.copy()

        self.output_timestep()

        self._logger.info(
            "Finished iPysnobal timestep: {}".format(self.time_step)
        )

    def output_timestep(self):
        """
        Output the time step if on the right frequency.
        Uses the hour of the current processed time step and will always
        save output at midnight (00:00) due to the multiplication by the hour.
        Also saves the output of the last time step for reinitialization
        when started the next time.
        """
        out_freq = (
            self.time_step.hour * self.data_time_step / 3600.0
        ) % self.options["output"]["frequency"] == 0

        last_time_step = self.time_step == self.date_time[-1]

        if out_freq or last_time_step:
            self._logger.info("iPysnobal outputting {}".format(self.time_step))
            pysnobal_io.output_timestep(
                self.output_rec,
                self.time_step,
                self.options,
                self.awsm.pysnobal_output_vars,
            )

            self.output_rec["time_since_out"] = self.init_zeros

    def load_previous_day(self):
        """
        Load the last time step from the previous day
        """
        previous_day = self.date_time[0] - timedelta(hours=1)
        # Temporarily set back to the previous day
        previous_start_date = self.awsm.start_date
        previous_end_date = self.awsm.end_date
        self.awsm.start_date = previous_day
        self.awsm.end_date = previous_day
        self.awsm.set_path_output()
        # SMRF connector to load previous day data
        smrf_previous_day = SMRFConnector(self.awsm)
        smrf_previous_day.open_netcdf_files()

        # Read data
        self.input1 = smrf_previous_day.get_timestep_netcdf(previous_day)
        self.input1 = self.convert_temperatures(self.input1)

        smrf_previous_day.close_netcdf_files()
        del smrf_previous_day
        # Set back to original dates
        self.awsm.start_date = previous_start_date
        self.awsm.end_date = previous_end_date
        self.awsm.set_path_output()

    def load_first_timestep_inputs(self):
        """
        When run on the first day of the simulation year (10/01), take the 0
        hour as the initial hour. Other cases include starting on a non-zero
        hour. When starting on the zero hour during the simulation year, look
        back to the previous day.
        """
        self._logger.info("  * Getting inputs for first timestep")

        if (
            self.date_time[0].hour == 0
            and self.awsm.model_init.init_file is not None
        ):
            self._logger.debug("  => from previous day")
            self.load_previous_day()
            # Open the files for all future time steps
            self.force = self.awsm.smrf_connector.open_netcdf_files()
        else:
            self._logger.debug("  => from first time step")
            self.force = self.awsm.smrf_connector.open_netcdf_files()
            # Load and remove the first step so it won't get run by PySnobal
            self.time_step = self.date_time.pop(0)
            self.input1 = self.get_timestep_inputs()

    def run_ipysnobal(self):
        """
        Function to run PySnobal from netcdf forcing data.
        """

        self._logger.info("Initializing PySnobal from netcdf files:")
        self.initialize_ipysnobal()

        self.load_first_timestep_inputs()

        self.initialize_updater()

        self._logger.info(
            f"Starting PySnobal for {len(self.date_time)} time steps"
        )

        for self.step_index, self.time_step in enumerate(self.date_time, 1):
            self.run_full_timestep()

        # close input files
        if self.awsm.forcing_data_type == "netcdf":
            self.awsm.smrf_connector.close_netcdf_files()

        self.options["output"]["snow"].close()
        self.options["output"]["em"].close()
        self._logger.debug("PySnobal finished.")
