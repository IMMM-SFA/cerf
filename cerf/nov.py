import calendar

import numpy as np


class NetOperationalValue:
    """Calculate Net Operational Value (NOV) in ($ / yr) per grid cell for all technologies.

    :param discount_rate:                   The time value of money in real terms.
                                            Units:  fraction
    :type discount_rate:                    float

    :param lifetime_yrs:                    Years of the expected technology plant lifetime_yrs.
                                            Units:  years
    :type lifetime_yrs:                     int

    :param unit_size_mw:                   The size of the expected power plant.
                                            Units:  megawatt
    :type unit_size_mw:                    int

    :param capacity_factor_fraction:        Capacity factor defined as average annual power generated divided by the
                                            potential output if the plant operated at its rated capacity for a year.
                                            Units:  fraction
    :type capacity_factor_fraction:         float

    :param variable_om_esc_rate_fraction:   Escalation rate of variable cost.
                                            Units:  fraction
    :type variable_om_esc_rate_fraction:    float

    :param fuel_price_esc_rate_fraction:    Escalation rate of fuel.
                                            Units:  fraction
    :type fuel_price_esc_rate_fraction:     float

    :param carbon_tax_esc_rate_fraction:    Escalation rate of carbon.
                                            Units:  fraction
    :type carbon_tax_esc_rate_fraction:     float

    :param variable_om_usd_per_mwh:         Variable operation and maintenance costs of yearly capacity use.
                                            Units:  $/MWh
    :type variable_om_usd_per_mwh:          float

    :param heat_rate_btu_per_kWh:           Amount of energy used by a power plant to generate one kilowatt-hour of
                                            electricity.
                                            Units:  Btu/kWh
    :type heat_rate_btu_per_kWh:            float

    :param fuel_price_usd_per_mmbtu:        Cost of fuel per unit.
                                            Units:  $/MMBtu
    :type fuel_price_usd_per_mmbtu:         float

    :param carbon_tax_usd_per_ton:          The fee imposed on the burning of carbon-based fuels.
                                            Units:  $/ton
    :type carbon_tax_usd_per_ton:           float

    :param carbon_capture_rate_fraction:    Rate of carbon capture.
                                            Units:  fraction
    :type carbon_capture_rate_fraction:     float

    :param fuel_co2_content_tons_per_btu:   CO2 content of the fuel and the heat rate of the technology.
                                            Units:  tons/Btu
    :type fuel_co2_content_tons_per_btu:    float

    :param lmp_arr:                         Locational Marginal Price (LMP) per grid cell for each technology in a
                                            multi-dimensional array where the shape is [tech_id, xcoord, ycoord].
                                            Units:  $/MWh
    :type lmp_arr:                          ndarray

    :param target_year:                     Target year of the simulation as a four digit integer (e.g., 2010)
    :type target_year:                      int

    :param consider_leap_year:              Choose to account for leap year in the number of hours per year calculation
    :type consider_leap_year:               bool

    :returns:                               [0] generation_mwh_per_year
                                            [1] operating cost
                                            [2] NOV

    """

    # type hints
    discount_rate: float
    lifetime_yrs: int
    unit_size_mw: int
    capacity_factor_fraction: float
    variable_om_esc_rate_fraction: float
    fuel_price_esc_rate_fraction: float
    carbon_tax_esc_rate_fraction: float
    variable_om_usd_per_mwh: float
    heat_rate_btu_per_kWh: float
    fuel_price_usd_per_mmbtu: float
    carbon_tax_usd_per_ton: float
    carbon_capture_rate_fraction: float
    fuel_co2_content_tons_per_btu: float
    lmp_arr: np.ndarray
    target_year: int
    consider_leap_year: bool

    # constants for conversion
    HOURS_PER_YEAR_NONLEAP = 8760
    HOURS_PER_YEAR_LEAP = 8784

    def __init__(self,
                 discount_rate,
                 lifetime_yrs,
                 unit_size_mw,
                 capacity_factor_fraction,
                 variable_om_esc_rate_fraction,
                 fuel_price_esc_rate_fraction,
                 carbon_tax_esc_rate_fraction,
                 variable_om_usd_per_mwh,
                 heat_rate_btu_per_kWh,
                 fuel_price_usd_per_mmbtu,
                 carbon_tax_usd_per_ton,
                 carbon_capture_rate_fraction,
                 fuel_co2_content_tons_per_btu,
                 lmp_arr,
                 target_year,
                 consider_leap_year=False):

        # assign class attributes
        self.discount_rate = discount_rate
        self.lifetime_yrs = lifetime_yrs
        self.unit_size_mw = unit_size_mw
        self.capacity_factor_fraction = capacity_factor_fraction
        self.variable_cost_esc = variable_om_esc_rate_fraction
        self.fuel_esc = fuel_price_esc_rate_fraction
        self.carbon_esc = carbon_tax_esc_rate_fraction
        self.variable_om_usd_per_mwh = variable_om_usd_per_mwh
        self.heat_rate_btu_per_kWh = heat_rate_btu_per_kWh
        self.carbon_tax_usd_per_ton = carbon_tax_usd_per_ton
        self.carbon_capture_rate_fraction = carbon_capture_rate_fraction
        self.fuel_price_usd_per_mmbtu = fuel_price_usd_per_mmbtu
        self.fuel_co2_content_tons_per_btu = fuel_co2_content_tons_per_btu
        self.lmp_arr = lmp_arr

        # adjust by leap year if so desired
        self.hours_per_year = self.assign_hours_per_year(target_year, consider_leap_year)

        # calculate annuity factor
        self.annuity_factor = self.calc_annuity_factor()

        # calculate levelizing factor for variable OM
        self.lf_vom = self.calc_levelization_factor_vom()

        # calculate levelizing factor for fuel
        self.lf_fuel = self.calc_levelization_factor_fuel()

        # calculate levelizing factor for carbon
        self.lf_carbon = self.calc_levelization_factor_carbon()

    @classmethod
    def assign_hours_per_year(cls, target_year, consider_leap_year):
        """Assign the hours per year based on whether or not the target year is a leap year."""

        if calendar.isleap(target_year) and consider_leap_year:
            return cls.HOURS_PER_YEAR_LEAP
        else:
            return cls.HOURS_PER_YEAR_NONLEAP

    def calc_annuity_factor(self):
        """Calculate annuity factor."""

        fx = pow(1.0 + self.discount_rate, self.lifetime_yrs)
        return self.discount_rate * fx / (fx - 1.0)

    def calc_levelization_factor_vom(self):
        """Calculate the levelizing factor for variable OM."""

        k = (1.0 + self.variable_cost_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime_yrs)) * self.annuity_factor / (1.0 - k)

    def calc_levelization_factor_fuel(self):
        """Calculate the levelizing factor for fuel."""

        k = (1.0 + self.fuel_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime_yrs)) * self.annuity_factor / (1.0 - k)

    def calc_levelization_factor_carbon(self):
        """Calculate the levelizing factor for carbon."""

        k = (1.0 + self.carbon_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - pow(k, self.lifetime_yrs)) * self.annuity_factor / (1.0 - k)

    def calc_generation(self):
        """Calculate electricity generation."""

        return self.unit_size_mw * self.capacity_factor_fraction * self.hours_per_year

    def calc_nov(self):
        """Calculate NOV array for all technologies."""

        generation = self.calc_generation()
        term2 = self.lmp_arr * self.lf_fuel
        term3 = self.variable_om_usd_per_mwh * self.lf_vom
        term4 = self.heat_rate_btu_per_kWh * (self.fuel_price_usd_per_mmbtu / 1000) * self.lf_fuel
        term5 = (self.carbon_tax_usd_per_ton * self.fuel_co2_content_tons_per_btu * self.heat_rate_btu_per_kWh * self.lf_carbon / 1000000) * (1 - self.carbon_capture_rate_fraction)
        operating_cost = (term2 - (term3 + term4 + term5))

        return generation, operating_cost, generation * operating_cost
