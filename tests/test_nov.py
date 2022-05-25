"""Tests for Net Operational Value calculations.

:author:   Chris R. Vernon
:email:    chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

import numpy as np

from cerf.nov import NetOperationalValue


class TestNov(unittest.TestCase):
    """Tests for the NOV calculations."""

    # inputs as they would come from GCAM and input sources
    DISCOUNT_RATE = 0.05  # fraction
    lifetime_yrs = 60  # years
    unit_size_mw = 1350  # megawatt
    CAPACITY_FACTOR_FRACTION = 0.9  # fraction
    variable_om_esc_rate_fraction = -0.00104311614063357  # fraction
    fuel_price_esc_rate_fraction = 0.04639  # fraction
    carbon_tax_esc_rate_fraction = 0.0  # fraction
    variable_om_usd_per_mwh = 2.09812782440284  # $/MWh
    heat_rate_btu_per_kWh = 10246.19999999998  # Btu/kWh
    fuel_price_usd_per_mmbtu = 0.712809999999999  # $/GJ gets converted to $/MBtu in code
    carbon_tax_usd_per_ton = 0.0  # $/ton
    CARBON_CAPTURE_RATE_FRACTION = 0.0  # fraction
    fuel_co2_content_tons_per_btu = 0.0  # tons/MWh gets converted to tons/Btu in code
    LMP_ARR = np.array([66.95609874])  # $/MWh

    # expected values
    EXPECTED_ANNUITY_FACTOR = 0.05282818452724236
    EXPECTED_LF_VOM = 0.9819019248539469
    EXPECTED_LF_FUEL = 2.8587075325530398
    EXPECTED_LF_CARBON = 0.999999999999999

    # difference in expected values when evaluating under different conditions
    EXPECTED_NOV_NOCARBON_NOLEAP = np.array([1793081990.25871])
    EXPECTED_NOV_NOCARBON_LEAP = np.array([1797994543.65668])
    EXPECTED_NOV_WITHCARBON_NOLEAP = np.array([1791838770.04080])

    @classmethod
    def instantiate_nov(cls, target_year, carbon_tax_usd_per_ton, fuel_co2_content_tons_per_btu, carbon_capture_rate_fraction, consider_leap_year):
        """Instantiate NOV class with test values.  The additional parameters can be passed to
        test NOV under different carbon conditions."""

        return NetOperationalValue(discount_rate=cls.DISCOUNT_RATE,
                                   lifetime_yrs=cls.lifetime_yrs,
                                   unit_size_mw=cls.unit_size_mw,
                                   capacity_factor_fraction=cls.CAPACITY_FACTOR_FRACTION,
                                   variable_om_esc_rate_fraction=cls.variable_om_esc_rate_fraction,
                                   fuel_price_esc_rate_fraction=cls.fuel_price_esc_rate_fraction,
                                   carbon_tax_esc_rate_fraction=cls.carbon_tax_esc_rate_fraction,
                                   variable_om_usd_per_mwh=cls.variable_om_usd_per_mwh,
                                   heat_rate_btu_per_kWh=cls.heat_rate_btu_per_kWh,
                                   fuel_price_usd_per_mmbtu=cls.fuel_price_usd_per_mmbtu,
                                   carbon_tax_usd_per_ton=carbon_tax_usd_per_ton,
                                   carbon_capture_rate_fraction=carbon_capture_rate_fraction,
                                   fuel_co2_content_tons_per_btu=fuel_co2_content_tons_per_btu,
                                   lmp_arr=cls.LMP_ARR,
                                   target_year=target_year,
                                   consider_leap_year=consider_leap_year)

    def test_nocarbon_noleap_nov(self):
        """Test NOV outcome with no carbon and no leap year."""

        # create a no carbon, no leap year run
        econ = self.instantiate_nov(target_year=2010,  # four digit year
                                    carbon_tax_usd_per_ton=0.0,  # $/ton
                                    fuel_co2_content_tons_per_btu=0.0,  # tons/MWh gets converted to tons/Btu
                                    carbon_capture_rate_fraction=0.0,  # fraction
                                    consider_leap_year=False
                                    )

        genenration, operating_cost, nov_tech_arr = econ.calc_nov()

        # test the calculation of annuity factor
        self.assertEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor)

        # test the calculation of the levelization factor for variable OM
        self.assertEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom)

        # test the calculation of the levelization factor for fuel
        self.assertEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel)

        # test the calculation of the levelization factor for carbon
        self.assertEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon)

        # test NOV
        np.testing.assert_almost_equal(nov_tech_arr, TestNov.EXPECTED_NOV_NOCARBON_NOLEAP, decimal=4)

    def test_nocarbon_leap_nov(self):
        """Test NOV outcome with no carbon and on a leap year."""

        # create a no carbon, leap year run
        econ = self.instantiate_nov(target_year=2012,  # four digit year
                                    carbon_tax_usd_per_ton=0.0,  # $/ton
                                    fuel_co2_content_tons_per_btu=0.0,  # tons/MWh gets converted to tons/Btu
                                    carbon_capture_rate_fraction=0.0,  # fraction
                                    consider_leap_year=True
                                    )
        genenration, operating_cost, nov_tech_arr = econ.calc_nov()

        # test the calculation of annuity factor
        self.assertEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor)

        # test the calculation of the levelization factor for variable OM
        self.assertEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom)

        # test the calculation of the levelization factor for fuel
        self.assertEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel)

        # test the calculation of the levelization factor for carbon
        self.assertEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon)

        # test NOV
        np.testing.assert_almost_equal(nov_tech_arr, TestNov.EXPECTED_NOV_NOCARBON_LEAP, decimal=4)

    def test_with_carbon_noleap_nov(self):
        """Test NOV outcome with carbon and not on a leap year."""

        # create a no carbon, leap year run
        econ = self.instantiate_nov(target_year=2010,  # four digit year
                                    carbon_tax_usd_per_ton=10.0,  # $/ton
                                    fuel_co2_content_tons_per_btu=1.2,  # tons/MWh gets converted to tons/Btu
                                    carbon_capture_rate_fraction=0.05,  # fraction
                                    consider_leap_year=False
                                    )
        genenration, operating_cost, nov_tech_arr = econ.calc_nov()

        # test the calculation of annuity factor
        self.assertEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor)

        # test the calculation of the levelization factor for variable OM
        self.assertEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom)

        # test the calculation of the levelization factor for fuel
        self.assertEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel)

        # test the calculation of the levelization factor for carbon
        self.assertEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon)

        # test NOV
        np.testing.assert_almost_equal(nov_tech_arr, TestNov.EXPECTED_NOV_WITHCARBON_NOLEAP, decimal=4)


if __name__ == '__main__':
    unittest.main()
