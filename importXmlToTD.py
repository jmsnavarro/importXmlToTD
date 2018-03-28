#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" Tool to Import XML to Teradata via BTEQ
# importXmlToTD

A terminal script written in Python that reads XML files and loads to Teradata tables/views via BTEQ.

Developed using Visual Studio Code with Python extension.

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
$ python import_xmltotd.py

## Notes:
- To modify default values, update classdef python file
- Each run producess two(2) types of output files:
  - date_time_import_xmltotd.py.log (execution log of the python script)
  - date_time_action_scriptname.btq.out (bteq output files)
"""

import csv
from datetime import timedelta, datetime    # to calculate runtime
import fileinput
import glob
import logging
import os
import pathlib
import re
import subprocess                           # to execute external commands
import sys
import shutil
import time

# 3rd party modules
from lxml import etree as ET                # to parse XML files
import pyodbc                               # to check Teradata connection
import xmlschema as xs                      # to validate XML files

# developer-created modules
import classdef                        # local module


# replace strings from a file
def doReplaceString(filename, oldString, newString, backupExtention=""):
    [print(line.replace(oldString, newString), end='')
        for line in fileinput.input([filename], inplace=True, backup=backupExtention)]

# generate file list
def genFileList(fileDir, fileListName, strBegin, strEnd, enableLogInfo=False):
    with os.scandir(fileDir) as files:
        cntFile = [file for file in files if file.name.endswith((strBegin, strEnd)) and file.is_file()]
        if cntFile:
            try:
                with open(os.path.join(fileDir, fileListName), 'w', newline='') as filelist:
                    if enableLogInfo == True:
                        msg = 'Generating file list...'
                        print('{}: {}'.format(logging.info.__name__.upper(), msg))
                        logging.info('{}'.format(msg))
                    [filelist.write('{}\n'.format(os.path.join(fileDir, f.name))) for f in cntFile]
                return len(cntFile)
            except Exception as e:
                print('{}: {}'.format(logging.debug.__name__.upper(), e))
                logging.debug('{}'.format(e))

# move file to a folder
def doMoveFile(filename, srcPathDir, tgtPathDir, comment='moving to'):
    if os.path.isfile(os.path.join(tgtPathDir, filename)):
        msg = ('Cannot move', 'file', 'It already exists in', 'directory')
        print('{}: {} {} {}. {} {} {}.'.format(logging.warning.__name__.upper(),
            msg[0], filename, msg[1], msg[2], '.\\{}'.format(os.path.basename(tgtPathDir)), msg[3]))
        logging.warning('{} {} {}. {} {} {}.'.format(msg[0], filename, msg[1], msg[2], tgtPathDir, msg[3]))
    else:
        shutil.move(os.path.join(srcPathDir, filename), os.path.join(tgtPathDir, filename))
        if comment:
            print('{}: {} {} .\\{}'.format(logging.info.__name__.upper(), filename, comment, os.path.basename(tgtPathDir)))
            logging.info('{} {} .\\{}'.format(filename, comment, os.path.basename(tgtPathDir)))

# file cleanup
def doFileCleanup(pathDir, filename, strMessage='Removing files...', enableLogInfo=True):
    try:
        files = glob.glob(os.path.join(pathDir, filename))
    except FileNotFoundError:
        None
    except Exception as e:
        print('{}: {}'.format(logging.warning.__name__.upper(), e))
        logging.warning('{}'.format(e))
    else:
        if files:
            if enableLogInfo == True:
                print('{}: {}'.format(logging.info.__name__.upper(), strMessage))
                logging.info('{}'.format(strMessage))
            for f in files:
                try:
                    os.remove(f)
                except Exception as e:
                    print('{}: {}'.format(logging.debug.__name__.upper(), e))
                    logging.debug('{}'.format(e))

# validate if group of files exists
def ifFilesExists(path, wildcardFilename):
    if glob.glob(os.path.join(path, wildcardFilename)):
        return True
    else:
        return False

# validate if file exists
def isFileExists(path, filename, showMsg=False, showLog=False):
    if os.path.isfile(os.path.join(path, filename.rstrip('\r\n'))):
        return True
    else:
        msg = 'does not exists in'
        if showMsg:
            print('{}: {} {} {}'.format(logging.info.__name__.upper(), filename.rstrip('\r\n'), msg, path))
        if showLog:
            logging.info('{} {} {}'.format(filename.rstrip('\r\n'), msg, path))
        return False

# check if directories exists
def isWorkDirsPresent():
    msg = '{}'.format('Checking work directory...')
    print('{}: {}'.format(logging.info.__name__.upper(), msg))
    logging.info('{}'.format(msg))
    if os.path.isdir(os.path.join(currentWorkDir, scriptsDir)) and \
        os.path.isdir(os.path.join(currentWorkDir, tgtDir)) and \
        os.path.isdir(os.path.join(currentWorkDir, srcDir)) and \
        os.path.isdir(os.path.join(currentWorkDir, logDir)) and \
        os.path.isdir(os.path.join(currentWorkDir, rejectDir)) and \
        os.path.isdir(os.path.join(currentWorkDir, archiveDir)):
        return True
    else:
        return False

# check if dependent files exists
def isDependentFilesPresent():
    if isFileExists(scriptsDir, classdef.Files.XSDSchema) and \
        ifFilesExists(scriptsDir, '*.btq'):
        return True
    else:
        return False

# parse XML to .csv file
def doParseXMLtoCSV(srcPathFilename, elementName):
    # set variables
    srcFilename = os.path.basename(srcPathFilename)
    tree = ET.parse(srcPathFilename)
    xmlRoot = tree.getroot()
    tgtPathFilename = os.path.join(tgtPathDir, '{}.{}'.format(elementName, 'csv'))

    if os.path.isfile(tgtPathFilename):
        fileObject = open(tgtPathFilename, 'a', newline='')
        csvWriter = csv.writer(fileObject, delimiter=classdef.Delimiter.Pipe)

    # get XML element attributes
    tupAttrib = classdef.getXMLElementAttrib(elementName)

    elementNameTemp = None
    for dom in xmlRoot.findall(".//{}".format(elementName)):
        if elementName != elementNameTemp:
            msg = 'fetching data from ...<{}>'.format(elementName)
            print(msg)
            logging.info(msg)
            elementNameTemp = elementName

        # collect attribute values
        attrib = [dom.get(a) for a in tupAttrib]
        attrib.append(srcFilename.rstrip('\r\n'))

        # add csv file header
        if not os.path.isfile(tgtPathFilename):
            fileObject = open(tgtPathFilename, 'w', newline='')
            csvWriter = csv.writer(fileObject, delimiter=classdef.Delimiter.Pipe)
            val = list(tupAttrib)
            val.append('SRCFILE')
            csvWriter.writerow(val)
        csvWriter.writerow(attrib)

    if os.path.isfile(tgtPathFilename):
        fileObject.close()

# check teradata connection
def execTeradataPing(showLog=True):
    if showLog == True:
        msg = '{}'.format('Checking connection to Teradata...')
        print('{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info('{}'.format(msg))
    try:
        with open(os.path.join(currentWorkDir, scriptsDir, classdef.TD_LOGON_FILE), 'r', newline=None) as file:
            connLogon = file.readline().rstrip('\r\n')
            connVal = (connLogon.replace('/',',').replace(' ', ',')).split(',')
            try:
                pyodbc.connect('DSN={};UID={};PWD={}'.format(
                        connVal[1],
                        connVal[2],
                        connVal[3]
                    )
                )
            except Exception:
                msg = '{}. {}'.format(
                    'Unable to access Teradata database',
                    'Please verify the logon file and or manually check database connection'
                )
                print('{}: {}.'.format(logging.warning.__name__.upper(), msg))
                logging.warning('{}'.format(msg))
                return False
            else:
                return True
    except Exception:
        msg = 'Unable to access or locate Teradata logon file. Please verify'
        print('{}: {}.'.format(logging.warning.__name__.upper(), msg))
        logging.warning('{}'.format(msg))
        return False

# execute Teradata script
def execTeradataScript(scriptsDir, logDir, BTEQScript, action, showRunCommand=False, filename=None):

    # prepare BTEQ scripts by replacing $Database strings to classdef.py > class:TDObject > DatabaseName = <value>
    doReplaceString(os.path.join(os.getcwd(), scriptsDir, BTEQScript),
        classdef.TDObject.DefaultDatabaseName,
        classdef.TDObject.NewDatabaseName)

    # create command
    # eg. <date>_<time>_<action>_<XML file>_<bteq file>.out
    command = 'powershell Get-Content .\\{}\\{} | bteq > .\\{}\\{}_{}'.\
        format(
            scriptsDir,
            BTEQScript,
            logDir,
            time.strftime('%Y%m%d_%H%M%S'),
            action
        )
    if filename:
        command = '{}_{}.{}.out'.format(command, filename, BTEQScript)
    else:
        command = '{}_{}.out'.format(command, BTEQScript)

    if showRunCommand == True:
        msg = 'Running command'
        print('{} -> {}'.format(msg, command))
        logging.info('{} {}'.format(msg, command))

    try:
        subproc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        msg = ('The script encountered an error', 'Please check the logs')
        print('{} {}.\n{}.\n{}'.format(logging.error.__name__.upper(), msg[0], msg[1], e))
        logging.error('{} {}. {}'.format(msg[0], msg[1], e))
    else:
        if subproc.returncode > 0:
            msg = ('Failed running command', 'Please check log (.btq.out) file')
            print('{}: {} "{}"\n{} {}.'.format(logging.warning.__name__.upper(), msg[0], command,
                str(subproc.stderr, 'utf-8'), msg[1]))
            logging.warning('{} "{}". {} {}.'.format(msg[0], command,
                str(subproc.stderr).replace('b', '').replace('\\r', ' ').replace('\\n', ' ').replace('\\t', ' '),
                msg[1]))
        else:
            if showRunCommand == True:
                msg = ('Output', 'SUCCESSFUL')
                print('{}: {}'.format(msg[0], msg[1]))
                logging.info('{}: {}'.format(msg[0], msg[1]))
    return subproc.returncode

# clean temporary files and tables created from previous runs if exists
def doCleanTempData():
    doFileCleanup(tgtPathDir, '*.csv', 'Removing temporary files...')
    doFileCleanup(
        srcPathDir,
        '{}*.txt'.format(classdef.FileListName.GenericFileList),
        'Removing file lists...'
    )

    msg = 'Cleaning temporary tables...'
    print('{}: {}'.format(logging.info.__name__.upper(), msg))
    logging.info('{}'.format(msg))
    execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.DeleteTempTables, 'deletetmp')

# move XML source files to archive folder
def doArchiveSrc():
    msg = 'Moving XML source files to archive folder...'
    print('\n{}: {}'.format(logging.info.__name__.upper(), msg))
    logging.info('{}'.format(msg))

    # regenerate file list (rejects already moved to rejects folder)
    doFileCleanup(
        srcPathDir,
        '{}*.txt'.format(classdef.FileListName.GenericFileList),
        None,
        False
    )
    fileListName = '{}.{}'.format(classdef.FileListName.XMLFileList, 'txt')
    genFileList(srcPathDir, fileListName, classdef.SRCFILE_BEGIN, '.{}'.format(classdef.SRCFILE_END))

    try:
        with open(os.path.join(srcPathDir, fileListName), 'r', newline=None) as fileListName:
            for file in list(fileListName):
                doMoveFile(os.path.basename(file.rstrip('\r\n')),
                    srcPathDir,
                    os.path.join(currentWorkDir, archiveDir),
                    comment='')
    except Exception as e:
        print('{}: {}'.format(logging.debug.__name__.upper(), e))
        logging.debug('{}'.format(e))

# insert run summary to summary table
def genRunSummary(logPathDir, startDateTime, elapsedRunTime, summaryDesc):
    path = os.path.join(logPathDir, '{}'.format(classdef.Files.SummaryLog))
    try:
        with open(path, 'w', newline='') as fileObject:
            csvWriter = csv.writer(fileObject, delimiter=classdef.Delimiter.Pipe)
            l = list()
            l.append(startDateTime)
            l.append(elapsedRunTime)
            l.append('.\\{}\\{}'.format(logDir, logFilename))
            l.append(summaryDesc.replace('"', '').replace('|', ':'))
            csvWriter.writerow(l)
    except Exception as e:
        print('{}: {}'.format(logging.warning.__name__.upper(), e))
        logging.warning('{}'.format(e))

# log print: Nothing to process
def genLogPrint_NothingToProcess(elapsedTime, reason):
    elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
    msg = ('Nothing to process', 'Total runtime')
    print('\n{}: {}. {}.\n{}: {}\n'.format(logging.info.__name__.upper(), msg[0], reason, msg[1], elapsedTime))
    logging.info('{}. {}. {}: {}'.format(msg[0], reason, msg[1], elapsedTime))

# log print: Cannot continue
def genLogPrint_CannotContinue(elapsedTime, reason):
    msg = ('Cannot continue', 'Total runtime')
    print('{}: {}. {}.\n{}: {}'.format(logging.info.__name__.upper(), msg[0], reason, msg[1], elapsedTime))
    logging.info('{}. {}. {}: {}'.format(msg[0], reason, msg[1], elapsedTime))

# main definition
def main():
    # check Teradata connection
    if execTeradataPing() == False:
        # show elapsed time
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        msg = 'Elapsed time {}'.format(elapsedTime)
        print('{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info(msg)

        # end
        sys.exit()

    # check if project directories exists
    if isWorkDirsPresent() == False:
        # show if work folders are missing
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        msg = '{} "{}": {}, {}, {}, {}, {} and {}'.format(
            'Please check if these folders exists in the current work directory',
            currentWorkDir, archiveDir, logDir, rejectDir, scriptsDir, srcDir, tgtDir)
        genLogPrint_CannotContinue(elapsedTime, msg)

        # write summary log
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()

    # check if dependent files exists
    if isDependentFilesPresent() == False:
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        msg ='{}: {} {} in .\\{} and {} {} in .\\{}'.format(
            'Please check if these files exists',
            'schema file', classdef.Files.XSDSchema, scriptsDir,
            'BTEQ files' , '(*.btq)', scriptsDir)
        genLogPrint_CannotContinue(elapsedTime, msg)

        # write summary log
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()

    # create file list if there are source files to process
    cntFilesOnQue = 0
    files = glob.glob(os.path.join(srcPathDir, '{}*.{}'.format(classdef.SRCFILE_BEGIN, classdef.SRCFILE_END)))
    if not files:
        # show if nothing to process
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        msg = '{} "{}"'.format('Please check source availability in', srcPathDir)
        genLogPrint_NothingToProcess(elapsedTime, msg)

        # write summary log
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()
    else:
        # clean temporary files and tables created from previous runs if exists
        doCleanTempData()

        # generate file list from XML souce files
        fileListName = '{}.{}'.format(classdef.FileListName.XMLFileList, 'txt')
        cntFilesOnQue = genFileList(
            srcPathDir,
            fileListName,
            classdef.SRCFILE_BEGIN,
            '.{}'.format(classdef.SRCFILE_END),
            True
        )

    # validate XML source files
    cntValidSchema = 0
    cntInvalidSchema = 0
    if cntFilesOnQue == 0:
        # show if file list was not generated when no sources found
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        genLogPrint_NothingToProcess(elapsedTime, 'File list was not created')

        # write summary log
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()
    else:
        msg = 'Validating {} XML source file(s)...'.format(cntFilesOnQue)
        print('\n{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info('{}'.format(msg))

        try:
            with open(os.path.join(srcPathDir, fileListName), 'r', newline=None) as filelist:
                startTime_ValidateXML_main = time.time()
                try:
                    with open(os.path.join(currentWorkDir, scriptsDir, classdef.Files.XSDSchema)) as schemaFile:
                        getSchema = xs.XMLSchema(schemaFile)
                        cntFile = 1
                        for file in list(filelist):
                            file = file.rstrip('\r\n')
                            filename = os.path.basename(file)
                            # test xml against xsd schema file
                            if getSchema.is_valid(file):
                                cntValidSchema += 1
                                msg = '(File {} of {}) {} ...validated (OK)'.format(cntFile, cntFilesOnQue, filename)
                                print('{}'.format(msg))
                                logging.info('{}'.format(msg))
                                cntFile += 1
                            else:
                                cntInvalidSchema += 1
                                msg = '(File {} of {}) {} ...rejected (INVALID SCHEMA)'.format(cntFile, cntFilesOnQue, filename)
                                print('{}: {}'.format(logging.warning.__name__.upper(), msg))
                                logging.warning('{}'.format(msg))
                                try:
                                    getSchema.validate(file)
                                except Exception as e:
                                    print('{}: {}'.format(logging.warning.__name__.upper(), e))
                                    logging.warning('{}'.format(e))
                                    continue
                                finally:
                                    # rename reject file as <datetime>_filename.XML.reject and move to reject folder
                                    rejectFile = '{}_{}.reject'.format(time.strftime('%Y%m%d_%H%M%S'), filename)
                                    shutil.move(file, os.path.join(srcPathDir, rejectFile))
                                    doMoveFile(rejectFile, srcPathDir, rejectPathDir, None)
                                    cntFile += 1

                    elapsedTime = timedelta(seconds=round(time.time() - startTime_ValidateXML_main))
                    msg = 'Total files checked against xsd: {} validated, {} rejected (elapsed time {})'.format(
                            cntValidSchema,
                            cntInvalidSchema,
                            elapsedTime)
                    print('\n{}: {}'.format(logging.info.__name__.upper(), msg))
                    logging.info('{}'.format(msg))

                except Exception as e:
                    print('{}: {}'.format(logging.error.__name__.upper(), e))
                    logging.error('{}'.format(e))

        except Exception as e:
            msg = 'Cannot read filelist'
            print('\n{}: {} {}\n{}'.format(logging.debug.__name__.upper(), msg, fileListName, e))
            logging.debug('{} {} {}'.format(msg, fileListName, e))

    # regenerate file list based from validated XML source files
    cntFilesOnQue_Valid = 0
    if cntValidSchema == 0:
        # write summary log
        msg = 'SUMMARY: {} files processed | {} xml files(s) validated, {} invalid'.format(
                cntFilesOnQue,
                cntValidSchema, cntInvalidSchema)
        print('{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info('{}'.format(msg))
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()
    else:
        doFileCleanup(
            srcPathDir,
            '{}*.txt'.format(classdef.FileListName.GenericFileList),
            'Refreshing file list...'
        )
        fileListName = '{}.{}'.format(classdef.FileListName.XMLFileList, 'txt')
        cntFilesOnQue_Valid = genFileList(
            srcPathDir,
            fileListName,
            classdef.SRCFILE_BEGIN,
            '.{}'.format(classdef.SRCFILE_END)
        )

        if cntFilesOnQue_Valid == 0:
            # show if file list was not generated when no sources found
            elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
            msg = 'No valid XML file(s)'
            genLogPrint_NothingToProcess(elapsedTime, msg)

            # write summary log
            msg = '{} in "{}"'.format(msg, '.\\{}'.format(srcDir))
            genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg)
            execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

            # end
            sys.exit()

    # parse validated XML source files to CSV then import to Teradata
    if cntFilesOnQue_Valid > 0:
        msg = 'Parsing source files and importing to tables...'
        print('\n{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info('{}'.format(msg))

        try:
            with open(os.path.join(srcPathDir, fileListName), 'r', newline=None) as filelist:
                cntImportedToTable = 0
                cntImportToTableRejected = 0
                cntFileNoData = 0
                startTime_ParsingAndTDLoad_Main = time.time()

                cntFile = 1
                for file in list(filelist):
                    doFileCleanup(tgtPathDir, '*.csv', None, False)
                    file = file.rstrip('\r\n')
                    filename = os.path.basename(file)
                    msg = '(File: {} of {}) parsing .\\{}\\{}'.format(cntFile, cntFilesOnQue_Valid, srcDir, filename)
                    print('\n{}'.format(msg))
                    logging.info('{}'.format(msg))

                    # parse XML to csv file
                    startTime_ParsingAndTDLoad = time.time()
                    [doParseXMLtoCSV(file, el) for el in classdef.XMLElementList.ElementList]

                    # import csv to landing tables
                    if ifFilesExists(tgtPathDir, '*.csv'):
                        if execTeradataScript(
                                scriptsDir,
                                logDir,
                                classdef.BTEQScript.ImportLdgTables,
                                'importtoldg',
                                True,
                                filename
                            ) > 0:
                            cntImportToTableRejected += 1
                            # rename reject file as <datetime>_filename.XML.reject and move to reject folder
                            rejectFile = '{}_{}.reject'.format(time.strftime('%Y%m%d_%H%M%S'), filename)
                            shutil.move(file, os.path.join(srcPathDir, rejectFile))
                            doMoveFile(rejectFile, srcPathDir, rejectPathDir)
                        else:
                            # insert landing tables to staging tables
                            if execTeradataScript(
                                    scriptsDir,
                                    logDir,
                                    classdef.BTEQScript.InsertStgTables,
                                    'loadtostg',
                                    True,
                                    filename
                                ) > 0:
                                cntImportToTableRejected += 1
                                # rename reject file as <datetime>_filename.XML.reject and move to reject folder
                                rejectFile = '{}_{}.reject'.format(time.strftime('%Y%m%d_%H%M%S'), filename)
                                shutil.move(file, os.path.join(srcPathDir, rejectFile))
                                doMoveFile(rejectFile, srcPathDir, rejectPathDir)
                            else:
                                cntImportedToTable += 1
                    else:
                        msg = 'XML file do not have data.'
                        print('{}'.format(msg))
                        logging.info('{}'.format(msg))
                        cntFileNoData += 1

                    elapsedTime = timedelta(seconds=round(time.time() - startTime_ParsingAndTDLoad))
                    msg = 'Elapsed time {}'.format(elapsedTime)
                    print('{}: {}'.format(logging.info.__name__.upper(), msg))
                    logging.info('{}'.format(msg))
                    cntFile += 1

        except Exception as e:
            msg = 'Cannot read filelist'
            print('\n{}: {} {}\n{}'.format(logging.debug.__name__.upper(), msg, fileListName, e))
            logging.debug('{} {} {}'.format(msg, fileListName, e))

        elapsedTime = timedelta(seconds=round(time.time() - startTime_ParsingAndTDLoad_Main))
        msg = 'Total files processed: {} imported, {} rejected (elapsed time {})'.format(
                cntImportedToTable,
                cntImportToTableRejected,
                elapsedTime)
        print('\n{}: {}'.format(logging.info.__name__.upper(), msg))
        logging.info('{}'.format(msg))

        # transfer XML source files to archive folder
        doArchiveSrc()

        # show end
        if cntInvalidSchema > 0 or cntImportToTableRejected > 0:
            rejectMessage = ' {}. {} "{}".'.format('with reject file(s)', 'Please check log directory', tgtPathDir)
        else:
            rejectMessage = '.'
        msg = 'DONE! Importing XML files to Teradata run successfully'
        print('\n{}: {}{}'.format(logging.info.__name__.upper(), msg, rejectMessage))
        logging.info('{}{}'.format(msg, rejectMessage))

        # show summary
        elapsedTime = timedelta(seconds=round(time.time() - startTime_Main))
        msg = 'SUMMARY: {} file(s) processed'.format(cntFilesOnQue)
        msg = '{} | {} xml files(s) validated, {} invalid/rejected'.format(msg, cntFilesOnQue_Valid, cntInvalidSchema)
        msg = '{} | {} imported to tables, {} no data, {} with issue(s)/rejected'.format(
            msg,
            cntImportedToTable,
            cntFileNoData,
            cntImportToTableRejected
        )
        print('\n{}: {} | Elapsed time {}\n'.format(logging.info.__name__.upper(), msg, elapsedTime))
        logging.info('{} | Elapsed time {}'.format(msg, elapsedTime))

        # write summary log
        genRunSummary(tgtPathDir, startTime_Main_Str, elapsedTime, msg.rstrip('\r\n'))
        execTeradataScript(scriptsDir, logDir, classdef.BTEQScript.InsertSummaryTable, 'writelog')

        # end
        sys.exit()

# main
if __name__ == "__main__":
    # set runtime
    startTime_Main = time.time()
    startTime_Main_Str = datetime.fromtimestamp(startTime_Main).strftime('%Y-%m-%d %H:%M:%S')

    # set global variables
    srcDir = classdef.DirList.SourceDir
    tgtDir = classdef.DirList.TargetDir
    scriptsDir = classdef.DirList.ScriptDir
    logDir = classdef.DirList.LogDir
    archiveDir = classdef.DirList.ArchiveDir
    rejectDir = classdef.DirList.RejectDir
    currentWorkDir = os.getcwd()
    srcPathDir = os.path.join(currentWorkDir, srcDir)
    tgtPathDir = os.path.join(currentWorkDir, tgtDir)
    rejectPathDir = os.path.join(currentWorkDir, rejectDir)

    # set global logging
    logFilename = '{}_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'), os.path.basename(__file__))
    logging.basicConfig(filename = os.path.join(currentWorkDir, logDir, logFilename),
        level = logging.DEBUG,
        format = "[%(levelname)s] : %(asctime)s : %(message)s")

    # show execution start
    msg = 'Starting execution of'
    print('\n{}: {} {}'.format(logging.info.__name__.upper(), msg, os.path.basename(__file__)))
    logging.info('{} {}'.format(msg, os.path.basename(__file__)))

    # call main definition
    main()