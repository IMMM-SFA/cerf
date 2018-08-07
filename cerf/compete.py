import numpy as np


class Competition:
    """
    Technology competition algorithm for CERF.

    Grid cell level net locational cost (NLC) per technology and an
    energy technology capacity expansion plan is used to compete
    technologies against each other to see which will win the grid
    cell. The technology that wins the grid cell is then sited until
    no further winning cells exist. Once sited, the location of the
    winning technology's grid cell is no longer available for siting.
    The competition array is recalculated after all technologies have
    passed through an iteration. This process is completed until there
    are either no cells left to site in or there are no more sites left
    to site for any technology.

    :param expansion_plan:      Dictionary of {tech_id: number_of_sites, ...}
    :param nlc_array:
    """

    def __init__(self, expansion_plan, nlc_array):

        self.exp = expansion_plan
        self.arx = self.mask_nlc(nlc_array)
        self.arx_shp = self.arx.shape

        # show cheapest option, add 1 to the index to represent the technology number
        self.ste = np.argmin(self.arx, axis=0)

        # flatten cheapest array to be able to use random
        self.flat_ste = self.ste.flatten()

        # prep array to hold outputs
        self.out_ste = np.zeros_like(self.flat_ste)

        self.avail_grids = True

        self.main()

    @staticmethod
    def mask_nlc(nlc_array):
        """
        Insert zero array and mask it as index [0, :, :] so the tech_id 0 will always
        be the minimum if nothing is left to site.

        :return:
        """
        arx = np.insert(nlc_array, 0, np.zeros_like(nlc_array[0, :, :]), axis=0)
        arx[0, :, :] = np.ma.masked_array(arx[0, :, :], np.ones_like(arx[0, :, :]))

        return arx

    def main(self):

        while self.avail_grids:

            # evaluate by technology
            for tech_id in self.exp.keys():

                if self.exp[tech_id] > 0 and self.avail_grids:

                    # get the index of target tech_id
                    tech = np.where(self.flat_ste == tech_id)[0]

                    # create a random array from 0 to n for the length of the input array
                    arg = np.random.rand(tech.shape[0]).argsort(axis=0)

                    # keep only a required number of values for sites; mask the rest
                    rdx = tech[arg < self.exp[tech_id]]

                    # apply new sites as 0
                    self.flat_ste[rdx] = 0

                    # add sited techs to output array
                    self.out_ste[rdx] = tech_id

                    # update dictionary with how many plants are left to site
                    self.exp[tech_id] = self.exp[tech_id] - rdx.shape[0]

                    # update original array with excluded area where siting occurred
                    if self.exp[tech_id] == 0:
                        self.arx[tech_id, :, :] = np.ma.masked_array(self.arx[0, :, :], np.ones_like(self.arx[0, :, :]))
                        self.arx[1:, :, :] = np.ma.masked_array(self.arx[1:, :, :],
                                                                np.tile(np.where(self.flat_ste == 0, 1, 0),
                                                                        self.arx_shp[0] - 1).reshape(
                                                                    self.arx_shp[0] - 1, self.arx_shp[1],
                                                                    self.arx_shp[2]))

                    # mask techs that have been sited in main array
                    else:
                        self.arx[1:, :, :] = np.ma.masked_array(self.arx[1:, :, :],
                                                                np.tile(np.where(self.flat_ste == 0, 1, 0),
                                                                        self.arx.shape[0] - 1).reshape(
                                                                    self.arx_shp[0] - 1, self.arx_shp[1],
                                                                    self.arx_shp[2]))

                    # show cheapest option, add 1 to the index to represent the technology number
                    self.ste = np.argmin(self.arx, axis=0)

                    # flatten cheapest array to be able to use random
                    self.flat_ste = self.ste.flatten()

                    # check for any available grids to site in
                    self.avail_grids = np.where(self.flat_ste > 0)[0].shape[0]

        # reshape output array to 2D
        self.out_ste = self.out_ste.reshape(self.ste.shape)