# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

import os
import getpass
import unittest
import tempfile
import mock

from django.db import connection
from openquake.commonlib import readinput, datastore
from openquake.server.db import models, actions, upgrade_manager
from openquake.server.settings import DATABASE
from openquake.server.tests import helpers

USER = getpass.getuser()


# twin to engine.job_from_file
def job_from_file(cfg_file, username, datadir, hazard_calculation_id=None):
    oq = readinput.get_oqparam(cfg_file)
    job_id = actions.create_job(oq.calculation_mode, oq.description,
                                username, datadir, hazard_calculation_id)
    return job_id, oq


def setup_module():
    global tmpfile
    fh, tmpfile = tempfile.mkstemp()
    os.close(fh)
    DATABASE['NAME'] = tmpfile
    DATABASE['USER'] = USER
    connection.cursor()  # connect to the db
    # sanity check: make sure we are using the right db
    fname = connection.connection.execute(
        'PRAGMA database_list').fetchone()[-1]
    assert fname == tmpfile, (fname, tmpfile)
    upgrade_manager.upgrade_db(connection.connection)


def teardown_module():
    connection.close()


def get_job(cfg, username, hazard_calculation_id=None):
    job_id, oq = job_from_file(cfg, username, datastore.DATADIR,
                               hazard_calculation_id)
    return models.OqJob.objects.get(pk=job_id)


class FakeJob(object):
    def __init__(self, job_type, calculation_mode):
        self.job_type = job_type
        self.calculation_mode = calculation_mode

    def get_oqparam(self):
        m = mock.Mock()
        m.calculation_mode = self.calculation_mode
        return m


class CheckHazardRiskConsistencyTestCase(unittest.TestCase):
    def test_ok(self):
        haz_job = FakeJob('hazard', 'scenario')
        actions.check_hazard_risk_consistency(
            haz_job, 'scenario_risk')

    def test_obsolete_mode(self):
        haz_job = FakeJob('hazard', 'scenario')
        with self.assertRaises(ValueError) as ctx:
            actions.check_hazard_risk_consistency(
                haz_job, 'scenario')
        msg = str(ctx.exception)
        self.assertEqual(msg, 'Please change calculation_mode=scenario into '
                         'scenario_risk in the .ini file')

    def test_inconsistent_mode(self):
        haz_job = FakeJob('hazard', 'scenario')
        with self.assertRaises(actions.InvalidCalculationID) as ctx:
            actions.check_hazard_risk_consistency(
                haz_job, 'classical_risk')
        msg = str(ctx.exception)
        self.assertEqual(
            msg, "In order to run a risk calculation of kind "
            "'classical_risk', you need to provide a "
            "calculation of kind ['classical', 'classical_risk'], "
            "but you provided a 'scenario' instead")


class DeleteHazCalcTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hazard_cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path(
            'classical_psha_based_risk/job.ini')
        cls.job = get_job(cls.hazard_cfg, USER)

    def test_del_calc(self):
        hazard_job = get_job(self.hazard_cfg, USER)

        models.Output.objects.create_output(
            hazard_job, 'test_curves_1', ds_key='hcurve'
        )
        models.Output.objects.create_output(
            hazard_job, 'test_curves_2', ds_key='hcurve'
        )

        # Sanity check: make sure the hazard calculation and outputs exist in
        # the database:
        hazard_jobs = models.OqJob.objects.filter(id=hazard_job.id)
        self.assertEqual(1, hazard_jobs.count())

        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(2, outputs.count())

        # Delete the calculation
        actions.del_calc(hazard_job.id, USER)

        # Check that the hazard calculation and its outputs were deleted:
        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(0, outputs.count())

        hazard_jobs = models.OqJob.objects.filter(id=hazard_job.id)
        self.assertEqual(0, hazard_jobs.count())

    def test_del_calc_does_not_exist(self):
        self.assertRaises(models.NotFound, actions.del_calc, -1, USER)

    def test_del_calc_no_access(self):
        # Test the case where we try to delete a hazard calculation which does
        # not belong to current user.
        # In this case, deletion is now allowed and should raise an exception.
        hazard_job = get_job(self.hazard_cfg, helpers.random_string())
        self.assertRaises(RuntimeError, actions.del_calc, hazard_job.id, USER)

    def test_del_calc_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing the hazard
        # calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job = get_job(self.risk_cfg, USER,
                           hazard_calculation_id=self.job.id)
        hc = risk_job.hazard_calculation
        self.assertRaises(RuntimeError, actions.del_calc, hc.id, USER)

    def test_del_calc_output_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing one of the
        # belonging to the hazard calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job = get_job(self.risk_cfg, USER,
                           hazard_calculation_id=self.job.id)
        hc = risk_job.hazard_calculation
        self.assertRaises(RuntimeError, actions.del_calc, hc.id, USER)


class DeleteRiskCalcTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hazard_cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path(
            'classical_psha_based_risk/job.ini')
        cls.job = get_job(cls.hazard_cfg, USER)

    def test_del_calc(self):
        risk_job = get_job(self.risk_cfg, USER,
                           hazard_calculation_id=self.job.id)
        models.Output.objects.create_output(
            risk_job, 'test_curves_1', ds_key='rcurves-rlzs'
        )
        models.Output.objects.create_output(
            risk_job, 'test_curves_2', ds_key='rcurves-rlzs'
        )

        # Sanity check: make sure the risk calculation and outputs exist in
        # the database:
        risk_calcs = models.OqJob.objects.filter(id=risk_job.id)
        self.assertEqual(1, risk_calcs.count())

        outputs = models.Output.objects.filter(oq_job=risk_job.id)
        self.assertEqual(2, outputs.count())

        # Delete the calculation
        actions.del_calc(risk_job.id, USER)

        # Check that the risk calculation and its outputs were deleted:
        outputs = models.Output.objects.filter(oq_job=risk_job.id)
        self.assertEqual(0, outputs.count())

        risk_calcs = models.OqJob.objects.filter(id=risk_job.id)
        self.assertEqual(0, risk_calcs.count())

    def test_del_calc_does_not_exist(self):
        self.assertRaises(models.NotFound, actions.del_calc, -1, USER)

    def test_del_calc_no_access(self):
        # Test the case where we try to delete a risk calculation which does
        # not belong to current user.
        # In this case, deletion is now allowed and should raise an exception.
        risk_job = get_job(self.risk_cfg, helpers.random_string(),
                           hazard_calculation_id=self.job.id)
        self.assertRaises(RuntimeError, actions.del_calc, risk_job.id, USER)


class FakeOutput(object):
    def __init__(self, id, display_name):
        self.id = id
        self.display_name = display_name

    def get_output_type_display(self):
        return self.display_name + str(self.id)


class PrintSummaryTestCase(unittest.TestCase):
    outputs = [FakeOutput(i, 'gmf') for i in range(1, 12)]

    def print_outputs_summary(self, full):
        got = actions.print_outputs_summary(self.outputs, full)
        return '\n'.join(got)

    def test_print_outputs_summary_full(self):
        self.assertEqual(self.print_outputs_summary(full=True), '''\
  id | name
   1 | gmf
   2 | gmf
   3 | gmf
   4 | gmf
   5 | gmf
   6 | gmf
   7 | gmf
   8 | gmf
   9 | gmf
  10 | gmf
  11 | gmf''')

    def test_print_outputs_summary_short(self):
        self.assertEqual(
            self.print_outputs_summary(full=False), '''\
  id | name
   1 | gmf
   2 | gmf
   3 | gmf
   4 | gmf
   5 | gmf
   6 | gmf
   7 | gmf
   8 | gmf
   9 | gmf
  10 | gmf
 ... | 1 additional output(s)
Some outputs where not shown. You can see the full list with the command
`oq-engine --list-outputs`''')
