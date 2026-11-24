# -*- coding: utf-8 -*-
"""
CustomSMRFConnector: Inserts a canopy interception correction between
SMRF output and iSnobal input by modifying precip.nc before it is read.
Processes one timestep at a time to avoid loading the full interception
file (18GB) into memory.
"""

import os
import logging
import xarray as xr
import numpy as np
import pandas as pd
import netCDF4 as nc_raw
import cftime
from awsm.interface.smrf_connector import SMRFConnector


class CustomSMRFConnector(SMRFConnector):
    """Extended SMRF connector with precipitation correction for canopy interception"""

    def __init__(self, awsm):
        super().__init__(awsm)
        self.interception_file = '/uufs/chpc.utah.edu/common/home/skiles-group1/yijing/hourly_interception_FSM2_2018_19.nc'
        self._logger = logging.getLogger(__name__)

    def run_smrf(self):
        """
        Run SMRF normally, then correct precip.nc before iSnobal reads it.
        """
        # Step 1: Run SMRF to generate all outputs (including precip.nc)
        super().run_smrf()

        # Step 2: Apply interception correction immediately after SMRF finishes
        self._apply_interception_correction()

    def _apply_interception_correction(self):
        """
        Subtract canopy interception from SMRF-generated precip.nc and
        overwrite the file in place. Processes one timestep at a time to
        avoid loading the full 18GB interception file into memory.
        """
        precip_path = os.path.join(self.output_path, 'precip.nc')
        backup_path = precip_path.replace('precip.nc', 'precip_original.nc')

        if not os.path.exists(precip_path):
            self._logger.error(f'precip.nc not found at: {precip_path}')
            raise FileNotFoundError(f'precip.nc not found at: {precip_path}')

        self._logger.info(f'Applying canopy interception correction to: {precip_path}')

        # Stage 1: Read full precip dataset into memory and close file handle
        with xr.open_dataset(precip_path) as ds_precip:
            ds_loaded = ds_precip.load().copy(deep=True)

        # Stage 2: Process one timestep at a time from the interception file
        # Open interception file once and read each timestep individually
        # to avoid loading the full 18GB into memory
        with nc_raw.Dataset(self.interception_file) as nc_inter:
            # Read time axis and decode to cftime objects
            times_inter = nc_raw.num2date(
                nc_inter['time'][:],
                units=nc_inter['time'].units,
                calendar=nc_inter['time'].calendar
            )

            # Build a lookup dict: 'YYYY-MM-DDTHH' -> index in interception file
            inter_time_index = {
                f'{t.year:04d}-{t.month:02d}-{t.day:02d}T{t.hour:02d}': i
                for i, t in enumerate(times_inter)
            }

            n_matched = 0
            for t in ds_loaded['precip'].time.values:
                # Convert precip timestep to the same string format
                ts = pd.Timestamp(t)
                key = ts.strftime('%Y-%m-%dT%H')

                if key not in inter_time_index:
                    # No interception data for this timestep, skip
                    continue

                idx = inter_time_index[key]

                # Read only this one timestep from the interception file
                # Dimension order in file is (time, y, x)
                intercept_slice = nc_inter['intercepted_snow'][idx, :, :]

                # precip.nc has shape (time, y, x)
            
                intercept_2d = np.array(intercept_slice)  # no transpose needed

                # Apply correction
                precip_slice = ds_loaded['precip'].sel(time=t).values  # shape: (y, x)
                corrected = np.clip(precip_slice - intercept_2d, 0, None)
                ds_loaded['precip'].loc[dict(time=t)] = corrected
                n_matched += 1

        if n_matched == 0:
            self._logger.error('No overlapping timesteps found after processing!')
            raise ValueError('No overlapping timesteps found.')

        self._logger.info(f'Corrected {n_matched} timesteps')

        # Stage 3: All file handles closed - safe to rename and write
        os.rename(precip_path, backup_path)
        self._logger.info(f'Original precip.nc backed up to: {backup_path}')

        ds_loaded.to_netcdf(precip_path)
        self._logger.info('Corrected precip.nc written successfully')