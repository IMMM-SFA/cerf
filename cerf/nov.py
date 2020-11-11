import numpy as np


class NetOperationalValue:
    """Calculate Net Operating Value (NOV) in ($ / yr) per grid cell as the following:

    NOV ($ / yr) = Generation (MWh / yr) *
                        [ Locational Marginal Price ($ / MWh) - Operating Costs ($ / MWh) ] *
                        Levelization Factor
            where, Operating Costs ($ / MWh) = Heat Rate (Btu / kWh) *
                                                Fuel Price ($ / MBtu) +
                                                Variable O&M ($ / MWh) +
                                                Carbon Price ($ / ton) *
                                                Carbon Fuel Content (tons / Btu) *
                                                Heat Rate (Btu / kWh) *
                                                (1 - Carbon Capture Rate (%))
            and, Levelization Factor = k * (1 - k**n) * (Annuity Factor / (1 - k))
                where, k = (1 + l) / (1 + d)
                        l = real annual growth rate (%)
                        d = real annual discount rate (%)
                and, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)
                    where, d = real annual discount rate (%)
                            n = asset lifetime (years)


    :param discount_rate:                   The time value of money in real terms. Fraction.
    :type discount_rate:                    float

    :param lifetime:                        Years of the expected technology plant lifetime.  Years.
    :type lifetime:                         int

    :param unit_size:                       The size of the expected power plant in MW
    :type unit_size:                        int

    :param cap_fact:                        Capacity factor defined as average annual power generated divided by the
                                            potential output if the plant operated at its rated capacity for a year.
    :type cap_fact:                         float

    :param variable_om_esc:                 Escalation factor of variable cost.  Fraction.
    :type variable_om_esc:                  float

    :param fuel_esc:                        Fuel price escalation factor. Fraction.
    :type fuel_esc:                         float

    :param carbon_esc:                      The annual escalation rate for carbon tax.
    :type carbon_esc:                       float

    :param variable_om:                     Variable operation and maintenance costs of yearly capacity use in $/MWh
    :type variable_om:                      float

    :param heat_rate:                       Amount of energy used by a power plant to generate one kilowatt-hour of
                                            electricity in Btu/kWh
    :type heat_rate:                        float

    :param fuel_price:                      Cost of fuel per unit in $/MBtu.
    :type fuel_price:                       float

    :param carbon_tax:                      The fee imposed on the burning of carbon-based fuels in $/ton
    :type carbon_tax:                       float

    :param carbon_capture:                  Rate of carbon capture.
    :type carbon_capture:                   float

    :param fuel_co2:                        CO2 content of the fuel and the heat rate of the technology in Tons/MWh
    :type fuel_co2:                         float

    :param lmp_arr:                         Locational Marginal Price (LMP) per grid cell for each technology in a
                                            multi-dimensional array where the shape is [tech_id, xcoord, ycoord]
    :type lmp_arr:                          NumPy array as dtype np.int

    """

    def __init__(self, discount_rate, lifetime, unit_size, capacity_factor, variable_om_esc_rate,
                 fuel_esc_rate, carbon_esc_rate, variable_om, heat_rate, fuel_price, carbon_tax,
                 carbon_capture_rate, fuel_co2_content, lmp_arr):

        self.discount_rate = discount_rate
        self.lifetime = lifetime
        self.unit_size = unit_size
        self.cap_fact = capacity_factor
        self.variable_om_esc = variable_om_esc_rate
        self.fuel_esc = fuel_esc_rate
        self.carbon_esc = carbon_esc_rate
        self.variable_om = variable_om
        self.heat_rate = heat_rate
        self.fuel_price = fuel_price
        self.carbon_tax = carbon_tax
        self.carbon_capture = carbon_capture_rate
        self.fuel_co2 = fuel_co2_content
        self.lmp_arr = lmp_arr

    def calc_annuity_factor(self):
        """Calculate annuity factor."""
        fx = np.power(1.0 + self.discount_rate, self.lifetime)
        return self.discount_rate * fx / (fx - 1.0)

    def calc_lf_lmp(self):
        """Calculate the levelizing factor for LMP."""
        k = (1.0 + self.lmp_arr) / (1.0 + self.discount_rate)
        return k * (1.0 - np.power(k, self.lifetime)) * self.calc_annuity_factor() / (1.0 - k)

    def calc_lf_vom(self):
        """Calculate the levelizing factor for variable OM."""
        k = (1.0 + self.variable_om_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - np.power(k, self.lifetime)) * self.calc_annuity_factor() / (1.0 - k)

    def calc_lf_fuel(self):
        """Calculate the levelizing factor for fuel."""
        k = (1.0 + self.fuel_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - np.power(k, self.lifetime)) * self.calc_annuity_factor() / (1.0 - k)

    def calc_lf_carbon(self):
        """Calculate the levelizing factor for carbon."""
        k = (1.0 + self.carbon_esc) / (1.0 + self.discount_rate)
        return k * (1.0 - np.power(k, self.lifetime)) * self.calc_annuity_factor() / (1.0 - k)

    def calc_nov(self):
        """Calculate NOV array for the target technology."""
        term1 = self.unit_size * self.cap_fact * 8760
        term2 = self.lmp_arr * self.calc_lf_fuel()
        term3 = self.variable_om * self.calc_lf_vom()
        term4 = self.heat_rate * (self.fuel_price / 1000) * self.calc_lf_fuel()
        term5 = (self.carbon_tax * self.fuel_co2 * self.heat_rate * self.calc_lf_carbon() / 1000000) * \
                (1 - self.carbon_capture)

        return term1 * (term2 - (term3 + term4 + term5))
