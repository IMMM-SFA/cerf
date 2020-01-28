import numpy as np


class Nov:
    """Calculate Net Operating Value (NOV) in ($ / yr) as the following:

    ```NOV ($ / yr) = Generation (MWh / yr) *
                        [ Locational Marginal Price ($ / MWh) - Operating Costs ($ / MWh) ] *
                        Levelization Factor

            where, Operating Costs ($ / MWh) = Heat Rate (Btu / kWh) *
                                                Fuel Price ($ / MBtu) (MBtu / 10**6 Btu) (10**3 kWh / MWh) +
                                                Variable O&M ($ / MWh) +
                                                Carbon Price ($ / ton) *
                                                Carbon Fuel Content (tons / Btu) *
                                                Heat Rate (Btu / kWh) (10**3 kWh / MWh) *
                                                (1 - Carbon Capture Rate (%))

            and, Levelization Factor = k * (1 - k**n) * (Annuity Factor / (1 - k))

                where, k = (1 + l) / (1 + d)
                        l = real annual growth rate (%)
                        d = real annual discount rate (%)

                and, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)

                    where, d = real annual discount rate (%)
                            n = asset lifetime (years)```

    """

    def __init__(self):

        pass

    def calc_levelization_factor(self):
        """Calculate levelization factor"""

        pass

    def calc_annuity_factor(self):
        """Calculate annuity factor"""

        pass

    def calc_operating_costs(self):
        """Calculate operating costs"""

        pass

    def calc_nov(self):
        """Calculate NOV"""

        pass
