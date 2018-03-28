# importXmlToTD

## A terminal script written in Python that reads XML files and loads to Teradata tables/views via BTEQ.

## Developed using Visual Studio Code with Python extension.

## Deployment Setup:
1. Project Directory
   - archive (archive folder)
   - logs (log folder)
   - reject (reject folder)
   - scripts (bteq scripts folder
   - src (source folder)
   - tgt (target folder)
2. Provide Teradata database, user, and password by updating ./scripts/logon file
3. Create ODBC DSN connection to Teradata database
4. Install the following in the host machine:
   - Python 3.6.4 or later
   - lxml python module (to parse XML files)
   - pyodbc python module (to check Teradata connection)
   - xmlschema python module (to validate XML files using XSD schema)
   - PowerShell 4.0 or later (for running bteq commands)

## How to run:
### $ python import_xmltotd.py

## Notes:
- To modify default values, update classdef.py
- Each run producess two(2) types of output files:
  - date_time_import_xmltotd.py.log (execution log of the python script)
  - date_time_action_scriptname.btq.out (bteq output files)