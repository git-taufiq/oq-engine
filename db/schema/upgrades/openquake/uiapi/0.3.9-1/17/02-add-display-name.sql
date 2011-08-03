/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


ALTER TABLE uiapi.output ADD COLUMN display_name VARCHAR;
UPDATE uiapi.output SET display_name = substring(path, '[^/]*$');
ALTER TABLE uiapi.output ALTER COLUMN display_name SET NOT NULL;
