# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.mgmpe.modifiable_gmpe` implements
:class:`~openquake.hazardlib.mgmpe.ModifiableGMPE`
"""

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const


class ModifiableGMPE(GMPE):
    """
    This is a fully configurable GMPE

    :param string gmpe_name:
        The name of a GMPE class used for the calculation.
    :param params:
        A dictionary where the key defines the required modification and the
        value is a list with the required parameters. The modifications
        currently supported are:
        - 'set_between_epsilon' This sets the epsilon of the between event
           variability i.e. the returned mean is the original + tau * episilon
           and sigma tot is equal to sigma_within
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, params=None):

        # Initialize the superclass
        super().__init__(gmpe_name=gmpe_name)

        # Create the original GMPE
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()
        self.params = params
        self.mean = None
        self.stds = None
        self.stds_types = self.gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # Compute the original mean and standard deviations
        omean, ostds = self.gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                      stds_types)
        self.mean = omean
        self.stds = ostds
        for key in self.params:
            meth = getattr(self, key)
            meth(self.params[key])

        return self.mean, self.stds

    def set_between_epsilon(self, par):
        """
        :param par:
            A list of parameters. In this case it contains the epsilon value
            used to constrain the between event variability
        """
        if const.StdDev.INTER_EVENT not in self.stds_types:
            raise ValueError('The GMPE does not have between event std')

        # Index for the between event standard deviation
        types = list(self.stds_types)
        idx = types.index(const.StdDev.INTER_EVENT)
        print(idx, types)
        print('function', self.stds[idx])
        self.mean = self.mean + par[0] * self.stds[idx]

        # Set between event variability to 0
        self.stds[idx] = np.zeros_like(self.stds[idx])

        # Set total variability equal to the within-event one
        idxa = types.index(const.StdDev.TOTAL)
        idxb = types.index(const.StdDev.INTRA_EVENT)
        self.stds[idxa] = self.stds[idxb]
