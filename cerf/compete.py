import copy
import logging

import numpy as np
import pandas as pd

import cerf.utils as util

logger = logging.getLogger(__name__)


class Competition:
    """Technology competition algorithm for CERF.

    Grid cell level net locational cost (NLC) per technology and an electricity technology capacity expansion plan are
    used to compete technologies against each other to see which will win the grid cell. The technology that wins the
    grid cell is then sited until no further winning cells exist. Once sited, the location of the winning technology’s
    grid cell, along with its buffer, are no longer available for siting. The competition array is recalculated after
    all technologies have passed through an iteration. This process is repeated until there are either no cells left
    to site or there are no more power plants left to satisfy the expansion plan for any technology. For technologies
    that have the same NLC value in multiple grid cells that win the competition, random selection is available by
    default. If the user wishes to have the outcomes be repeatable, the randomizer can be set to False and a random
    seed set.

    :param expansion_plan:                          Dictionary of {tech_id: number_of_sites, ...}
    :type expansion_plan:                           dict

    :param nlc_mask:                                3D array of [tech_id, x, y] for Net Locational Costs. Each
                                                    technology has been masked with its suitability data, so only
                                                    grid cells that are suitable have a finite NLC per tech; unsuitable
                                                    cells are ``+inf`` (a ``numpy.ma`` masked array is also accepted
                                                    and converted). The 0 index position is a default dimension, all
                                                    ``+inf``, which is chosen if no technologies are able to compete.
                                                    A contiguous ``float64`` input is used as the working array and
                                                    is modified in place as cells are sited and excluded.
    :type nlc_mask:                                 ndarray

    :param technology_dict:                         A technology dictionary containing at a minimum
                                                    {tech_id:  buffer_in_km, ...}
    :type technology_dict:                          dict

    :param randomize:                               Choose to make randomization of site selection where NLC is the same
                                                    in multiple grid cells for a single technology random. If False,
                                                    the seed_value will be used as a way to reproduce the exact siting.
                                                    Default:  True
    :type randomize:                                bool

    :param seed_value:                              Seed for this competition's private random number generator when
                                                    ``randomize`` is False. The generator is local to the instance
                                                    (the global NumPy RNG is never touched), so seeded results are
                                                    identical for every joblib backend and processing order.
    :type seed_value:                               int

    :param verbose:                                 Log out siting information. Default False.
    :type verbose:                                  bool

    """

    def __init__(self,
                 target_region_name,
                 settings_dict,
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 lmp_dict,
                 generation_dict,
                 operating_cost_dict,
                 nov_dict,
                 ic_dict,
                 nlc_mask,
                 zones_arr,
                 xcoords,
                 ycoords,
                 indices_flat,
                 randomize=True,
                 seed_value=0,
                 verbose=False,
                 auto_run=True):

        # target region
        self.target_region_name = target_region_name

        # project level settings dictionary
        self.settings_dict = settings_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # private copy of the region's expansion plan; `compete()` decrements `n_sites` as plants are sited and the
        #  remaining counts are exposed via `self.expansion_dict`, so the caller's plan must never be touched
        self.expansion_dict = copy.deepcopy(expansion_dict)

        # locational marginal pricing
        self.lmp_flat_dict = lmp_dict

        # generation
        self.generation_flat_dict = generation_dict

        # operating cost
        self.operating_cost_flat_dict = operating_cost_dict

        # net operational value
        self.nov_flat_dict = nov_dict

        # interconnection costs
        self.ic_flat_dict = ic_dict

        # lmp zones array
        self.zones_flat_arr = zones_arr

        # flat array of full grid indices value for the target region
        self.indices_flat = indices_flat

        # net locational costs with suitability applied for the target region: unsuitable / excluded cells are +inf so a
        #  plain float array with `argmin` reproduces the masked-array semantics (masked values fill with +inf) at a
        #  fraction of the cost
        if np.ma.isMaskedArray(nlc_mask):
            nlc_mask = nlc_mask.astype(np.float64).filled(np.inf)
        self.nlc_mask = np.ascontiguousarray(nlc_mask, dtype=np.float64)
        self.nlc_mask_shape = self.nlc_mask.shape

        # 2D view [layer, flat_cell] of the same memory for cheap per-cell exclusion updates
        self._nlc_2d = self.nlc_mask.reshape(self.nlc_mask_shape[0], -1)

        # log out additional info
        self.verbose = verbose

        # private random number generator; seeded for reproducible outcomes when requested. A local `RandomState`
        #  yields exactly the same draws the legacy global `np.random.seed`/`np.random.choice` did, without mutating
        #  process-wide state shared with other regions, threads, or user code
        self.rng = np.random.RandomState(None if randomize else seed_value)

        # number of technologies
        self.n_techs = len(self.technology_order)

        # dictionary to hold sited information
        self.sited_dict = util.empty_sited_dict()

        # coordinates for each index
        self.xcoords = xcoords
        self.ycoords = ycoords

        # exclude any technologies having 0 expected sites in the expansion plan from competition
        for index, i in enumerate(self.technology_order, 1):
            if self.expansion_dict[i]["n_sites"] == 0:
                self.exclude_technology(index)

        # create dictionary of {tech_id: flat_nlc_array, ...}; a snapshot taken before any siting so the NLC of a
        #  chosen cell can still be reported after its neighbourhood has been excluded
        self.nlc_flat_dict = {i: self._nlc_2d[ix + 1].copy() for ix, i in enumerate(self.technology_order)}

        # show cheapest option, add 1 to the index to represent the technology number
        self.update_cheapest()

        # prep array to hold outputs
        self.sited_arr_1d = np.zeros_like(self.cheapest_arr_1d)

        # results, populated by `run()`
        self.sited_array = None
        self.sited_df = None
        self._has_run = False

        # construction leaves the object fully prepared but un-sited; `auto_run` preserves the historical behaviour
        #  of siting on instantiation
        if auto_run:
            self.run()

    def run(self):
        """Run the competition once and populate ``sited_array`` / ``sited_df`` / ``sited_dict``.

        The object is prepared for inspection at construction (``cheapest_arr``, ``nlc_mask``, ``avail_grids``, ...);
        calling ``run()`` performs the siting. It is idempotent: a second call returns the existing result.

        :return:                        self

        """

        if not self._has_run:
            self.sited_array, self.sited_df = self.compete()
            self.log_outcome()
            self._has_run = True

        return self

    def metric_at(self, arr, flat_index):
        """Return the value of a per-technology metric array at a flat region cell index.

        Metric arrays may be either flat 1D arrays or 2D ``[row, col]`` views over the region's bounding box (the
        latter avoids flattening full technology stacks per region); both are indexed without copying.

        """

        if arr.ndim == 1:
            return arr[flat_index]

        row, col = divmod(int(flat_index), self.nlc_mask_shape[2])

        return arr[row, col]

    def sited_record(self, tech_id, target_ix, retirement_year):
        """Build the output record for one sited plant as a dictionary keyed like `util.empty_sited_dict()`.

        :param tech_id:                 Technology ID of the sited plant
        :param target_ix:               Flat region cell index of the site
        :param retirement_year:         Year the plant retires (``run_year + operational_life_yrs``)

        """

        tech = self.technology_dict[tech_id]

        return {'region_name': self.target_region_name,
                'tech_id': tech_id,
                'tech_name': tech['tech_name'],
                'unit_size_mw': tech['unit_size_mw'],
                'xcoord': self.xcoords[target_ix],
                'ycoord': self.ycoords[target_ix],
                'index': self.indices_flat[target_ix],
                'buffer_in_km': tech['buffer_in_km'],
                'sited_year': self.settings_dict['run_year'],
                'retirement_year': retirement_year,
                'lmp_zone': self.zones_flat_arr[target_ix],
                'locational_marginal_price_usd_per_mwh': self.metric_at(self.lmp_flat_dict[tech_id], target_ix),
                'generation_mwh_per_year': self.metric_at(self.generation_flat_dict[tech_id], target_ix),
                'operating_cost_usd_per_year': self.metric_at(self.operating_cost_flat_dict[tech_id], target_ix),
                'net_operational_value_usd_per_year': self.metric_at(self.nov_flat_dict[tech_id], target_ix),
                'interconnection_cost_usd_per_year': self.metric_at(self.ic_flat_dict[tech_id], target_ix),
                'net_locational_cost_usd_per_year': self.nlc_flat_dict[tech_id][target_ix],
                'capacity_factor_fraction': tech['capacity_factor_fraction'],
                'carbon_capture_rate_fraction': tech['carbon_capture_rate_fraction'],
                'fuel_co2_content_tons_per_btu': tech['fuel_co2_content_tons_per_btu'],
                'fuel_price_usd_per_mmbtu': tech['fuel_price_usd_per_mmbtu'],
                'fuel_price_esc_rate_fraction': tech['fuel_price_esc_rate_fraction'],
                'heat_rate_btu_per_kWh': tech['heat_rate_btu_per_kWh'],
                'lifetime_yrs': tech['lifetime_yrs'],
                'operational_life_yrs': tech['operational_life_yrs'],
                'variable_om_usd_per_mwh': tech['variable_om_usd_per_mwh'],
                'variable_om_esc_rate_fraction': tech['variable_om_esc_rate_fraction'],
                'carbon_tax_usd_per_ton': tech['carbon_tax_usd_per_ton'],
                'carbon_tax_esc_rate_fraction': tech['carbon_tax_esc_rate_fraction']}

    def add_sited_record(self, tech_id, target_ix, retirement_year):
        """Append one sited plant to ``self.sited_dict`` (a dict of column lists aligned with `empty_sited_dict`)."""

        record = self.sited_record(tech_id, target_ix, retirement_year)

        if record.keys() != self.sited_dict.keys():
            missing = set(self.sited_dict) ^ set(record)
            raise KeyError(f"Sited record columns do not match `empty_sited_dict()`: {sorted(missing)}")

        for key, value in record.items():
            self.sited_dict[key].append(value)

    def exclude_technology(self, tech_index):
        """Make every grid cell unavailable to the technology at layer ``tech_index``."""

        self.nlc_mask[tech_index, :, :] = np.inf

    def exclude_cells(self, flat_indices):
        """Make the given flat grid cell indices unavailable to all technologies."""

        self._nlc_2d[1:, flat_indices] = np.inf

    def update_cheapest(self):
        """Recompute the cheapest technology per grid cell (0 where no technology is available)."""

        # unsuitable cells are +inf in every layer, so layer 0 (all +inf) wins the tie exactly as the masked argmin did
        self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

        # flatten cheapest array to be able to use random
        self.cheapest_arr_1d = self.cheapest_arr.flatten()

        # number of grid cells still available to some technology
        self.avail_grids = int(np.count_nonzero(self.cheapest_arr_1d))

    def log_outcome(self):
        """Log a warning sites that were not able to be sited."""

        for k in self.expansion_dict.keys():

            tech_name = self.expansion_dict[k]['tech_name']
            remaining_sites = self.expansion_dict[k]['n_sites']

            if remaining_sites > 0:
                logger.warning(f"Unable to achieve full siting for `{tech_name}` in `{self.target_region_name}`:  "
                               f"{remaining_sites} unsited.")

    def compete(self):

        # initialize keep sighting designation; False if no more sites or area to site
        keep_siting = True

        while keep_siting:

            # evaluate by technology
            for index, tech_id in enumerate(self.technology_order):

                # assign an index as it appears in the n-dim array to the order in which it is being processed
                #  index of 0 is the default array and does not represent a technology
                tech_index = index + 1

                # get the indices of the target tech ids where the target tech is the cheapest option
                tech = np.where(self.cheapest_arr_1d == tech_index)[0]

                # the number of sites for the target tech
                required_sites = self.expansion_dict[tech_id]['n_sites']

                # calculate the year of retirement
                operational_life_yrs = int(self.technology_dict[tech_id]['operational_life_yrs'])
                retirement_year = self.settings_dict['run_year'] + operational_life_yrs

                # if there are more power plants to site and there are grids available to site them...
                if self.avail_grids > 0 and tech.shape[0] > 0 and required_sites > 0:

                    # site with buffer and exclude buffered area from further siting
                    still_siting = True
                    sited_list = []
                    excluded_lists = []
                    while still_siting:

                        # get the NLC values associated with each winner
                        tech_nlc = self.nlc_flat_dict[tech_id][tech]

                        # get the least expensive NLC indices from the winners
                        tech_nlc_cheap = tech[np.where(tech_nlc == np.nanmin(tech_nlc))]

                        # select a random index that has a winning cell for the check where multiple low NLC may exists
                        target_ix = self.rng.choice(tech_nlc_cheap)

                        # record the sited plant
                        self.add_sited_record(tech_id, target_ix, retirement_year)

                        # add selected index to list
                        sited_list.append(target_ix)

                        # apply buffer: the site and its neighbourhood are no longer the cheapest option for anyone
                        buffer_indices = util.buffer_flat_indices(target_index=target_ix,
                                                                  nrows=self.nlc_mask_shape[1],
                                                                  ncols=self.nlc_mask_shape[2],
                                                                  ncells=self.technology_dict[tech_id]['buffer_in_km'])
                        self.cheapest_arr_1d[buffer_indices] = 0
                        excluded_lists.append(buffer_indices)

                        # update the number of sites left to site
                        required_sites -= 1
                        self.expansion_dict[tech_id].update(n_sites=required_sites)

                        # remove any buffered elements as an option to site; `tech` is a sorted unique index array
                        #  from np.where, and boolean masking preserves its order so seeded outcomes are unchanged
                        tech = tech[~np.isin(tech, buffer_indices, assume_unique=True)]

                        # exit siting for the target technology if all sites have been sited or if there are no more
                        #   winning cells
                        if required_sites == 0 or tech.shape[0] == 0:
                            still_siting = False

                    # array of the site indices
                    rdx = np.array(sited_list)

                    # add sited techs to output array
                    self.sited_arr_1d[rdx] = tech_id

                    if self.verbose:
                        logger.info('\nUpdate expansion plan to represent siting requirements:')
                        logger.info(self.expansion_dict)

                    # apply the new exclusion (sited cells and their buffers from this batch) to all techs
                    self.exclude_cells(np.concatenate(excluded_lists))

                    # if the technology has achieved its full expansion, then exclude the rest of its suitable area so
                    #  other technologies can now compete for the grid cells it previously won but now no longer needs
                    if self.expansion_dict[tech_id]['n_sites'] == 0:
                        self.exclude_technology(tech_index)

                    # show cheapest option and count the grid cells still available
                    self.update_cheapest()

                    # are there any sites left to site
                    left_to_site = sum([self.expansion_dict[i]['n_sites'] for i in self.expansion_dict.keys()])

                    # stop technology iteration if all area is consumed or if all sites have been sited
                    if self.avail_grids == 0 or left_to_site == 0:
                        keep_siting = False

                    if self.verbose:
                        logger.info(f'\nAvailable grid cells:  {self.avail_grids}')

                # there are no more suitable grid cells
                elif self.avail_grids == 0:
                    keep_siting = False

                # if there are available grids and a cheapest option available but no more required sites
                elif self.avail_grids > 0 and tech.shape[0] > 0 and required_sites == 0:

                    # if there are no required sites, then exclude the rest of the techs suitable area so
                    #  other technologies can now compete for the grid cells it previously won but now no longer needs
                    self.exclude_technology(tech_index)

                    # show cheapest option and count the grid cells still available
                    self.update_cheapest()

                # if there are suitable cells AND no winners and some or no sites left to site pass until next round
                else:
                    pass

        # create sited data frame
        df = pd.DataFrame(self.sited_dict).astype(util.sited_dtypes())

        # reshape output array to 2D
        return self.sited_arr_1d.reshape(self.cheapest_arr.shape), df
