/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- uiapi.hazard_map_data
GRANT ALL ON SEQUENCE uiapi.hazard_map_data_id_seq to GROUP openquake;
GRANT SELECT ON uiapi.hazard_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_map_data TO oq_uiapi_writer;

-- uiapi.loss_map_data
GRANT ALL ON SEQUENCE uiapi.loss_map_data_id_seq to GROUP openquake;
GRANT SELECT ON uiapi.loss_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_map_data TO oq_uiapi_writer;
