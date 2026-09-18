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
    def instantiate_nov(cls, target_year, carbon_tax_usd_per_ton, fuel_co2_content_tons_per_btu,
                        carbon_capture_rate_fraction, consider_leap_year):
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
        self.assertAlmostEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor, places=12)

        # test the calculation of the levelization factor for variable OM
        self.assertAlmostEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom, places=12)

        # test the calculation of the levelization factor for fuel
        self.assertAlmostEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel, places=12)

        # test the calculation of the levelization factor for carbon
        self.assertAlmostEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon, places=12)

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
        self.assertAlmostEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor, places=12)

        # test the calculation of the levelization factor for variable OM
        self.assertAlmostEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom, places=12)

        # test the calculation of the levelization factor for fuel
        self.assertAlmostEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel, places=12)

        # test the calculation of the levelization factor for carbon
        self.assertAlmostEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon, places=12)

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
        self.assertAlmostEqual(TestNov.EXPECTED_ANNUITY_FACTOR, econ.annuity_factor, places=12)

        # test the calculation of the levelization factor for variable OM
        self.assertAlmostEqual(TestNov.EXPECTED_LF_VOM, econ.lf_vom, places=12)

        # test the calculation of the levelization factor for fuel
        self.assertAlmostEqual(TestNov.EXPECTED_LF_FUEL, econ.lf_fuel, places=12)

        # test the calculation of the levelization factor for carbon
        self.assertAlmostEqual(TestNov.EXPECTED_LF_CARBON, econ.lf_carbon, places=12)

        # test NOV
        np.testing.assert_almost_equal(nov_tech_arr, TestNov.EXPECTED_NOV_WITHCARBON_NOLEAP, decimal=4)


class TestFinancialFactorLimits(unittest.TestCase):
    """Degenerate-input handling for the annuity and levelization factors."""

    D = 0.05
    N = 60

    def test_escalation_equal_to_discount_rate_does_not_raise(self):
        """esc == discount gives k == 1 and previously raised ZeroDivisionError."""

        econ = TestNov.instantiate_nov(target_year=2010, carbon_tax_usd_per_ton=0.0,
                                       fuel_co2_content_tons_per_btu=0.0, carbon_capture_rate_fraction=0.0,
                                       consider_leap_year=False)

        # override all three escalation rates to equal the discount rate and recompute
        econ.variable_cost_esc = econ.fuel_esc = econ.carbon_esc = econ.discount_rate
        lf = econ.calc_levelization_factor_fuel()

        self.assertTrue(np.isfinite(lf))
        self.assertAlmostEqual(lf, econ.lifetime_yrs * econ.annuity_factor, places=12)
        self.assertAlmostEqual(econ.calc_levelization_factor_vom(), lf, places=15)
        self.assertAlmostEqual(econ.calc_levelization_factor_carbon(), lf, places=15)

        # NOV itself must be finite
        _, _, nov = econ.calc_nov()
        self.assertTrue(np.all(np.isfinite(nov)))

    def test_levelization_factor_is_continuous_at_the_limit(self):
        """The k == 1 branch must agree with the general formula as esc -> discount from both sides.

        LF has a finite, non-zero slope with respect to the escalation rate at the limit (about n^2 * AF / 2
        in k, i.e. ~90 per unit escalation for n=60), so the general formula evaluated at esc = d + eps
        differs from the limit by O(eps). Continuity means that difference must shrink proportionally with
        eps and vanish as eps -> 0, so the tolerance scales with |eps| and is much larger than the slope.
        """

        af = NetOperationalValue.annuity_factor_from(self.D, self.N)
        limit = NetOperationalValue.levelization_factor_from(self.D, self.D, self.N, af)

        # bound on |dLF/d(esc)| near k = 1; generous relative to the true slope (~92 for n=60, d=0.05)
        slope_bound = self.N ** 2 * af

        previous_error = None
        for eps in (1e-4, 1e-6, 1e-8):
            for sign in (1.0, -1.0):
                near = NetOperationalValue.levelization_factor_from(self.D + sign * eps, self.D, self.N, af)
                error = abs(near - limit)
                self.assertLess(error, slope_bound * eps, msg=f"discontinuity at eps={sign * eps}")

            # error must decrease as eps decreases (approaching the limit, not a jump)
            if previous_error is not None:
                self.assertLess(error, previous_error)
            previous_error = error

    def test_zero_discount_rate_annuity_factor(self):
        """d == 0 previously raised ZeroDivisionError; the limit is 1 / n."""

        af = NetOperationalValue.annuity_factor_from(0.0, self.N)
        self.assertAlmostEqual(af, 1.0 / self.N, places=15)

        # continuity from above: dAF/dd at d=0 is (n+1)/(2n) ~ 0.5, so error is O(eps); use tolerance of 1 * eps
        for eps in (1e-4, 1e-6, 1e-8):
            self.assertLess(abs(NetOperationalValue.annuity_factor_from(eps, self.N) - af), eps)

        # with zero escalation as well, every year is weighted equally: LF == 1
        lf = NetOperationalValue.levelization_factor_from(0.0, 0.0, self.N, af)
        self.assertAlmostEqual(lf, 1.0, places=12)

    def test_general_case_unchanged(self):
        """Non-degenerate inputs must still reproduce the historical expected values exactly."""

        af = NetOperationalValue.annuity_factor_from(TestNov.DISCOUNT_RATE, TestNov.lifetime_yrs)
        self.assertAlmostEqual(af, TestNov.EXPECTED_ANNUITY_FACTOR, places=12)

        lf_fuel = NetOperationalValue.levelization_factor_from(TestNov.fuel_price_esc_rate_fraction,
                                                               TestNov.DISCOUNT_RATE, TestNov.lifetime_yrs, af)
        self.assertAlmostEqual(lf_fuel, TestNov.EXPECTED_LF_FUEL, places=12)

    def test_interconnection_uses_same_annuity_factor(self):
        """IC and NOV must agree on the annuity factor, including at d == 0."""

        from cerf.interconnect import Interconnection

        for d in (0.0, 0.03, 0.05, 0.1):
            self.assertAlmostEqual(Interconnection.calc_annuity_factor(d, self.N),
                                   NetOperationalValue.annuity_factor_from(d, self.N), places=15)

    def test_invalid_inputs_raise_value_error(self):
        with self.assertRaises(ValueError):
            NetOperationalValue.annuity_factor_from(self.D, 0)

        with self.assertRaises(ValueError):
            NetOperationalValue.annuity_factor_from(-1.0, self.N)


if __name__ == '__main__':
    unittest.main()
