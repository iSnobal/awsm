import os
from inicheck.tools import cast_all_variables

from awsm.framework.framework import run_awsm
from awsm.tests.awsm_test_case_lakes import AWSMTestCaseLakes


class TestLakesLidarUpdate(AWSMTestCaseLakes):
    """
    Testing using Lakes:
        - ipysnobal
        - initialize from snow.nc
        - loading from netcdf
        - lidar updates
    """

    @classmethod
    def configure(cls):
        config = cls.base_config_copy()

        adj_config = {
            "update depth": {
                "update": True,
                "update_file": "./topo/lidar_depths.nc",
                "buffer": 400,
                "flight_numbers": 1,
                "update_change_file": "output/lakes/wy2020/lakes_gold/run20191001_20191001/model_lidar_change.nc",  # noqa
            }
        }
        config.raw_cfg.update(adj_config)

        config.apply_recipes()
        cls.run_config = cast_all_variables(config, config.mcfg)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold_dir = cls.basin_dir.joinpath("gold_hrrr_update")

        cls.gold_em = os.path.join(cls.gold_dir, "em.nc")
        cls.gold_snow = os.path.join(cls.gold_dir, "snow.nc")

        cls.output_path = cls.basin_dir.joinpath(
            "output/lakes/wy2020/lakes_gold/run20191001_20191001"
        )

        run_awsm(cls.run_config, testing=True)

    def test_snow_nc(self):
        self.compare_netcdf_files(
            "snow.nc",
            [
                "thickness",
                "snow_density",
                "specific_mass",
                "liquid_water",
                "temp_surf",
                "temp_lower",
                "temp_snowcover",
                "thickness_lower",
                "water_saturation",
            ],
        )

    def test_em_nc(self):
        self.compare_netcdf_files(
            "em.nc",
            [
                "net_rad",
                "sensible_heat",
                "latent_heat",
                "snow_soil",
                "precip_advected",
                "sum_EB",
                "evaporation",
                "snowmelt",
                "SWI",
                "cold_content",
            ],
        )

    def test_model_change_nc(self):
        self.compare_netcdf_files(
            "model_lidar_change.nc",
            [
                "depth_change",
                "rho_change",
                "swe_change",
            ],
        )
