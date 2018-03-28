# importXmlToTD

""" Tool to Import XML to Teradata via BTEQ
    Name         : import_xmltotd.py
    Info         : A terminal application written in Python that reads XML files
                   and loads to Teradata tables/views.
    Build        : March 27, 2018

    Developer    : Joseph Navarro (josephmichael.navarro@teradata.com)
    Python Editor: Visual Studio Code with Python extension
    Environment  : Windows 7 SP1 or later

    Setup        :
    1.) <working_directory>
        |- archive (archive folder)
        |- logs    (log folder)
        |- reject  (reject folder)
        |- scripts (bteq scripts folder
        |- src     (source folder)
        |- tgt     (target folder)
    2.) Provide Teradata database, user, and password by updating ./scripts/logon
        file

    Requirements :
    1.) Python 3.6.4 or later
    2.) Python modules
        - lxml (to parse XML files)
        - pyodbc (to check Teradata connection)
        - xmlschema (to validate XML files using XSD schema)
    3.) PowerShell 4.0 or later (for running bteq commands)

    How to run   :
    $ python import_xmltotd.py

    Notes        :
    - To modify default values, update classdef.py
    - Each run producess two(2) types of output files:
      <date>_<time>_import_xmltotd.py.log            - execution log of the
                                                       python script
      <date>_<time>_<action>_<script_name>.btq.out   - bteq output files
"""
