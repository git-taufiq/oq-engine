# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import os
import getpass
import unittest
import itertools
import mock
import numpy

from nose.plugins.attrib import attr

from openquake.hazardlib.imt import PGA

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based import core
from openquake.engine.utils import stats

from tests.utils import helpers


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        self.cfg = helpers.get_data_path('event_based_hazard/job_2.ini')
        self.job = helpers.get_hazard_job(self.cfg, username=getpass.getuser())
        self.calc = core.EventBasedHazardCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)

    def test_donot_save_trivial_gmf(self):
        gmf_set = mock.Mock()

        # setup two ground motion fields on a region made by three
        # locations. On the first two locations the values are
        # nonzero, in the third one is zero. Then, we will expect the
        # bulk inserter to add only two entries.
        gmvs = numpy.matrix([[1., 1.],
                             [1., 1.],
                             [0., 0.]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2], gmvs=gmvs)}

        fake_bulk_inserter = mock.Mock()
        with helpers.patch('openquake.engine.writer.BulkInserter') as m:
            m.return_value = fake_bulk_inserter
            core._save_gmfs(
                gmf_set, gmf_dict, [mock.Mock(), mock.Mock(), mock.Mock()], 1)
            self.assertEqual(2, fake_bulk_inserter.add_entry.call_count)

    def test_save_only_nonzero_gmvs(self):
        gmf_set = mock.Mock()

        gmvs = numpy.matrix([[0.0, 0, 1]])
        gmf_dict = {PGA: dict(rupture_ids=[1, 2, 3], gmvs=gmvs)}

        fake_bulk_inserter = mock.Mock()
        with helpers.patch('openquake.engine.writer.BulkInserter') as m:
            m.return_value = fake_bulk_inserter
            core._save_gmfs(
                gmf_set, gmf_dict, [mock.Mock()], 1)
            call_args = fake_bulk_inserter.add_entry.call_args_list[0][1]
            self.assertEqual([1], call_args['gmvs'])
            self.assertEqual([3], call_args['rupture_ids'])

    def test_initialize_ses_db_records(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='ses')
        self.assertEqual(2, len(outputs))

        # With this job configuration, we have 2 logic tree realizations.
        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            sess = models.SES.objects.filter(
                ses_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(sess))

            for ses in sess:
                # The only metadata in in the SES is investigation time.
                self.assertEqual(hc.investigation_time, ses.investigation_time)

    def test_initialize_pr_data_with_ses(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_items = 12
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_items + ltr2.total_items, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_items + ltr2.completed_items, done)

    def test_initialize_gmf_db_records(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='gmf')
        self.assertEqual(2, len(outputs))

        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            gmf_sets = models.GmfSet.objects.filter(
                gmf_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(gmf_sets))

            for gmf_set in gmf_sets:
                # The only metadata in a GmfSet is investigation time.
                self.assertEqual(
                    hc.investigation_time, gmf_set.investigation_time)

    def test_initialize_pr_data_with_gmf(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_items = 13
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_items + ltr2.total_items, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_items + ltr2.completed_items, done)

    def test_initialize_complete_lt_ses_db_records_branch_enum(self):
        # Set hazard_calculation.number_of_logic_tree_samples = 0
        # This indicates that the `end-branch enumeration` method should be
        # used to carry out the calculation.

        # This test was added primarily for branch coverage (in the case of end
        # branch enum) for the method `initialize_complete_lt_ses_db_records`.
        hc = self.job.hazard_calculation
        hc.number_of_logic_tree_samples = 0

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        self.calc.initialize_complete_lt_ses_db_records()

        complete_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=self.job.id,
            ses_collection__output__output_type='complete_lt_ses',
            ordinal=None)

        self.assertEqual(250.0, complete_lt_ses.investigation_time)
        self.assertIsNone(complete_lt_ses.ordinal)

    def _patch_calc(self):
        """
        Patch the stochastic functions and the save-to-db functions in the
        calculator to make the test faster and independent on the stochastic
        number generator
        """
        rupture1 = mock.Mock()
        rupture1.tectonic_region_type = 'Active Shallow Crust'
        rupture2 = mock.Mock()
        rupture2.tectonic_region_type = 'Active Shallow Crust'
        self.patch_ses = mock.patch(
            'openquake.hazardlib.calc.stochastic.'
            'stochastic_event_set_poissonian',
            mock.MagicMock(return_value=[rupture1, rupture2]))
        self.patch_gmf = mock.patch(
            'openquake.hazardlib.calc.gmf.ground_motion_fields',
            mock.MagicMock())
        self.patch_save_rup = mock.patch(
            'openquake.engine.calculators.hazard.'
            'event_based.core._save_ses_rupture')
        self.patch_save_gmf = mock.patch(
            'openquake.engine.calculators.hazard.'
            'event_based.core._save_gmfs')
        self.patch_ses.start()
        self.patch_gmf.start()
        self.patch_save_rup.start()
        self.patch_save_gmf.start()

    def _unpatch_calc(self):
        "Remove the patches"
        self.patch_ses.stop()
        self.patch_gmf.stop()
        self.patch_save_rup.stop()
        self.patch_save_gmf.stop()

    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        self._patch_calc()
        try:
            from openquake.hazardlib import calc
            from openquake.engine.calculators.hazard.event_based import core
            ses_mock = calc.stochastic.stochastic_event_set_poissonian
            gmf_mock = calc.gmf.ground_motion_fields
            save_rup_mock = core._save_ses_rupture
            save_gmf_mock = core._save_gmfs

            # run the calculation in process and check the outputs
            os.environ['OQ_NO_DISTRIBUTE'] = '1'
            try:
                job = helpers.run_hazard_job(self.cfg)
            finally:
                del os.environ['OQ_NO_DISTRIBUTE']
            hc = job.hazard_calculation
            rlz1, rlz2 = models.LtRealization.objects.filter(
                hazard_calculation=hc.id).order_by('ordinal')

            # check that the parameters are read correctly from the files
            self.assertEqual(hc.ses_per_logic_tree_path, 5)

            # Check that we have the right number of gmf_sets.
            # The correct number is (num_real * ses_per_logic_tree_path).
            gmf_sets = models.GmfSet.objects.filter(
                gmf_collection__output__oq_job=job.id,
                gmf_collection__lt_realization__isnull=False)
            # 2 realizations, 5 ses_per_logic_tree_path
            self.assertEqual(10, gmf_sets.count())

            # check that we called the right number of times the patched
            # functions: 40 = 2 Lt * 4 sources * 5 ses = 8 tasks * 5 ses
            self.assertEqual(ses_mock.call_count, 40)
            self.assertEqual(save_rup_mock.call_count, 80)  # 2 rupt per ses
            self.assertEqual(gmf_mock.call_count, 80)  # 2 ruptures per ses
            self.assertEqual(save_gmf_mock.call_count, 40)  # num_tasks * ses

            # Check the complete logic tree SES
            complete_lt_ses = models.SES.objects.get(
                ses_collection__output__oq_job=job.id,
                ses_collection__output__output_type='complete_lt_ses',
                ordinal=None)

            # Test the computed `investigation_time`
            # 2 lt realizations * 5 ses_per_logic_tree_path * 50.0 years
            self.assertEqual(500.0, complete_lt_ses.investigation_time)

            self.assertIsNone(complete_lt_ses.ordinal)

            # Now check for the correct number of hazard curves:
            curves = models.HazardCurve.objects.filter(output__oq_job=job)
            # ((2 IMTs * 2 real) + (2 IMTs * (1 mean + 2 quantiles))) = 10
            # + 3 mean and quantiles multi-imt curves
            self.assertEqual(13, curves.count())

            # Finally, check for the correct number of hazard maps:
            maps = models.HazardMap.objects.filter(output__oq_job=job)
            # ((2 poes * 2 realizations * 2 IMTs)
            # + (2 poes * 2 IMTs * (1 mean + 2 quantiles))) = 20
            self.assertEqual(20, maps.count())
        finally:
            self._unpatch_calc()

    def test_task_arg_gen(self):
        hc = self.job.hazard_calculation

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        [rlz1, rlz2] = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by('id')

        expected = [  # sources, ses_id, rlz_id, seed, result_grp_ordinal
            ([1], 1, rlz1.id, 1711655216, 1),
            ([1], 2, rlz1.id, 1038305917, 2),
            ([1], 3, rlz1.id, 836289861, 3),
            ([1], 4, rlz1.id, 1781144172, 4),
            ([1], 5, rlz1.id, 1869241528, 5),
            ([2], 1, rlz1.id, 215682727, 6),
            ([2], 2, rlz1.id, 1101399957, 7),
            ([2], 3, rlz1.id, 2054512780, 8),
            ([2], 4, rlz1.id, 1550095676, 9),
            ([2], 5, rlz1.id, 1537531637, 10),
            ([3], 1, rlz1.id, 834081132, 11),
            ([3], 2, rlz1.id, 2109160433, 12),
            ([3], 3, rlz1.id, 1527803099, 13),
            ([3], 4, rlz1.id, 1876252834, 14),
            ([3], 5, rlz1.id, 1712942246, 15),
            ([4], 1, rlz1.id, 219667398, 16),
            ([4], 2, rlz1.id, 332999334, 17),
            ([4], 3, rlz1.id, 1017801655, 18),
            ([4], 4, rlz1.id, 1577927432, 19),
            ([4], 5, rlz1.id, 1810736590, 20),
            ([1], 1, rlz2.id, 745519017, 21),
            ([1], 2, rlz2.id, 2107357950, 22),
            ([1], 3, rlz2.id, 1305437041, 23),
            ([1], 4, rlz2.id, 75519567, 24),
            ([1], 5, rlz2.id, 179387370, 25),
            ([2], 1, rlz2.id, 1653492095, 26),
            ([2], 2, rlz2.id, 176278337, 27),
            ([2], 3, rlz2.id, 777508283, 28),
            ([2], 4, rlz2.id, 718002527, 29),
            ([2], 5, rlz2.id, 1872666256, 30),
            ([3], 1, rlz2.id, 796266430, 31),
            ([3], 2, rlz2.id, 646033314, 32),
            ([3], 3, rlz2.id, 289567826, 33),
            ([3], 4, rlz2.id, 1964698790, 34),
            ([3], 5, rlz2.id, 613832594, 35),
            ([4], 1, rlz2.id, 1858181087, 36),
            ([4], 2, rlz2.id, 195127891, 37),
            ([4], 3, rlz2.id, 1761641849, 38),
            ([4], 4, rlz2.id, 259827383, 39),
            ([4], 5, rlz2.id, 1464146382, 40),
        ]

        # utilities to present the generated arguments in a nicer way
        dic = {}
        counter = itertools.count(1)

        def src_no(src_id):
            try:
                return dic[src_id]
            except KeyError:
                dic[src_id] = counter.next()
                return dic[src_id]

        def process_args(arg_gen):
            for (job_id, source_ids, ses_rlz_n, lt_rlz, task_seed,
                 result_grp_ordinal) in arg_gen:
                yield (map(src_no, source_ids), ses_rlz_n, lt_rlz.id,
                       task_seed, result_grp_ordinal)

        actual = list(process_args(self.calc.task_arg_gen()))
        self.assertEqual(expected, actual)
