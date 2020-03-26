# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
Module exports :class:`BindiEtAl2014RhypEC8scaled`
"""
import numpy as np
from openquake.hazardlib.gsim.bindi_2014 import BindiEtAl2014Rhyp, CoeffsTable


class BindiEtAl2014RhypEC8scaled(BindiEtAl2014Rhyp):
    """
    Implements European GMPE:
    D.Bindi, M. Massa, L.Luzi, G. Ameri, F. Pacor, R.Puglia and P. Augliera
    (2014), "Pan-European ground motion prediction equations for the
    average horizontal component of PGA, PGV and 5 %-damped PSA at spectral
    periods of up to 3.0 s using the RESORCE dataset", Bulletin of
    Earthquake Engineering, 12(1), 391 - 340

    The regressions are developed considering the geometrical mean of the
    as-recorded horizontal components
    The printed version of the GMPE was corrected by Erratum:
    D.Bindi, M. Massa, L.Luzi, G. Ameri, F. Pacor, R.Puglia and P. Augliera
    (2014), "Erratum to Pan-European ground motion prediction equations for the
    average horizontal component of PGA, PGV and 5 %-damped PSA at spectral
    periods of up to 3.0 s using the RESORCE dataset", Bulletin of
    Earthquake Engineering, 12(1), 431 - 448. The erratum notes that the
    printed coefficients tables were in error. In this implementation
    coefficients tables were taken from the Electronic Supplementary
    material of the original paper, which are indicated as being unaffected.
    """
    def _get_site_amplification_term(self, C, vs30):
        """
        Returns the site amplification given Eurocode 8 site classification
        """
        f_s = np.zeros_like(vs30)
        # Site class B
        idx = np.logical_and(vs30 < 800.0, vs30 >= 360.0)
        f_s[idx] = C["eB"]
        # Site Class C
        idx = np.logical_and(vs30 < 360.0, vs30 >= 180.0)
        f_s[idx] = C["eC"]
        # Site Class D
        idx = vs30 < 180.0
        f_s[idx] = C["eD"]
        return f_s

    #: Coefficients from Table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""
    imt             e1             c1            c2             h             c3            b1             b2            b3            eA            eB            eC            eD           sofN           sofR           sofS          sofU           tau           phi        phis2s         sigma
    pgv    3.33368672   -1.665480000   0.136478000   6.310130000   0.0000000000   0.436373000   -0.049720200   0.264336000   0.000000000   0.130319000   0.272298000   0.350870000   -0.090869900    0.013282500   -0.067381500   0.000000000   0.241933000   0.284305000   0.231138000   0.373311000
    pga    4.409190407   -1.752120000   0.150507000   7.321920000   0.0000000000   0.144291000   -0.066081100   0.284211000   0.000000000   0.143778000   0.231064000   0.187402000   -0.071745100    0.084957800   -0.057096500   0.000000000   0.195249000   0.284622000   0.213455000   0.345155000
    0.04   4.590759595   -1.854600000   0.165968000   6.982270000   0.0000000000   0.124402000   -0.056602000   0.260601000   0.000000000   0.140350000   0.217010000   0.146507000   -0.065379200    0.088098100   -0.057670900   0.000000000   0.204345000   0.297881000   0.222929000   0.361234000
    0.07   4.773689595   -1.878220000   0.157048000   8.133700000   0.0000000000   0.138028000   -0.040786500   0.276090000   0.000000000   0.145543000   0.206101000   0.115846000   -0.051289600    0.113143000   -0.037623000   0.000000000   0.208843000   0.304438000   0.242821000   0.369185000
    0.10   4.719726517   -1.799170000   0.151808000   8.380980000   0.0005478660   0.098832300   -0.056937000   0.322027000   0.000000000   0.158622000   0.208849000   0.125428000   -0.037486800    0.120065000   -0.036904000   0.000000000   0.195390000   0.313320000   0.251339000   0.369252000
    0.15   4.620956911   -1.614050000   0.105601000   7.496250000   0.0011834100   0.125747000   -0.083500900   0.464456000   0.000000000   0.162534000   0.197589000   0.158161000   -0.047089600    0.098045600   -0.050605600   0.000000000   0.193856000   0.310861000   0.247987000   0.366353000
    0.20   4.504936218   -1.465010000   0.056754500   6.272220000   0.0014308100   0.236642000   -0.083463900   0.542025000   0.000000000   0.143446000   0.213637000   0.170195000   -0.021448300    0.139454000   -0.012459600   0.000000000   0.191231000   0.306652000   0.226544000   0.361392000
    0.30   4.531386994   -1.460160000   0.025927200   5.503160000   0.0005543760   0.332549000   -0.097217900   0.551296000   0.000000000   0.121637000   0.254554000   0.226009000   -0.042269100    0.119803000   -0.019226600   0.000000000   0.199096000   0.304125000   0.207111000   0.363499000
    0.40   4.432384887   -1.428430000   0.016902400   4.819740000   0.0000000000   0.368987000   -0.111955000   0.547881000   0.000000000   0.119481000   0.275041000   0.275672000   -0.053267600    0.091980000   -0.032188300   0.000000000   0.207716000   0.302796000   0.194828000   0.367194000
    0.50   4.349197652   -1.414650000   0.028367500   4.955190000   0.0000000000   0.389410000   -0.118151000   0.495459000   0.000000000   0.118871000   0.298870000   0.344584000   -0.064737900    0.069448700   -0.037414200   0.000000000   0.225415000   0.300553000   0.198934000   0.375691000
    0.70   4.255689621   -1.412970000   0.020875700   4.293770000   0.0000000000   0.470648000   -0.118095000   0.460014000   0.000000000   0.115734000   0.325887000   0.477053000   -0.074956400    0.028574500   -0.055644400   0.000000000   0.246498000   0.301897000   0.212696000   0.389747000
    0.80   4.173259621   -1.404290000   0.038146400   4.010590000   0.0000000000   0.481962000   -0.116743000   0.393948000   0.000000000   0.110981000   0.334461000   0.517530000   -0.081627800    0.008428810   -0.063434400   0.000000000   0.249844000   0.305995000   0.224068000   0.395038000
    1.00   4.06654889   -1.395430000   0.034061400   4.096680000   0.0000000000   0.550001000   -0.110860000   0.386023000   0.000000000   0.103026000   0.336196000   0.566463000   -0.057167500    0.014892500   -0.051388400   0.000000000   0.274446000   0.309616000   0.244465000   0.413742000
    2.00   3.523713055   -1.381110000   0.137878000   6.539170000   0.0000000000   0.551312000   -0.098766100   0.000000000   0.000000000   0.115091000   0.320404000   0.586654000   -0.023796000    0.034963600    0.025270300   0.000000000   0.277179000   0.325724000   0.259839000   0.427696000
    3.00   3.319083208   -1.399740000   0.216533000   8.339210000   0.0000000000   0.552993000   -0.071343600   0.000000000   0.000000000   0.143969000   0.315187000   0.559213000   -0.146666000   -0.128655000   -0.067567300   0.000000000   0.283885000   0.320266000   0.267078000   0.427973000
    4.00   3.110535797   -1.333280000   0.203724000   8.409960000   0.0000000000   0.652840000   -0.054790600   0.000000000   0.000000000   0.124787000   0.285654000   0.532224000   -0.141040000   -0.153993000   -0.059989300   0.000000000   0.259933000   0.305458000   0.000000000   0.401086000
    """)
