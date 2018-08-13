SRCFILE_BEGIN = 'food'
SRCFILE_END = 'xml'
TD_LOGON_FILE = 'logon'

class TDObject:
    DefaultDatabaseName = '$DATABASE'
    NewDatabaseName = 'IMPORTXMLTOTD'

class BTEQScript:
    # delete temporary tables
    DeleteTempTables = '{}'.format('Delete_TMP.btq')
    # import landing tables
    ImportLdgTables = '{}'.format('Import_LDG.btq')
    # insert staging tables
    InsertStgTables = '{}'.format('Insert_STG.btq')
    # insert summary table
    InsertSummaryTable = '{}'.format('Insert_SUMMARY.btq')

class Delimiter:
    Pipe = '|'
    Comma = ','
    Period = '.'
    Slash = '/'
    BackSlash = '\\'
    Tab = '\t'

class DirList:
    SourceDir = 'src'
    TargetDir = 'tgt'
    ScriptDir = 'scripts'
    LogDir = 'logs'
    ArchiveDir = 'archive'
    RejectDir = 'reject'

class Files:
    XSDSchema = 'source_schema.xsd'
    SummaryLog = 'summary_log.csv'

class FileListName:
    GenericFileList = 'filelist'
    XMLFileList = '{}_{}'.format(GenericFileList, 'XML')

class XMLElement:
    Breakfast = 'breakfast'
    Drinks = 'drinks'
    Waffles = 'waffles'
    Toast = 'toast'
    HomeStyle = 'homestyle'
    Espresso = 'espresso'
    Frappuccino = 'frappuccino'
    Tea = 'tea'
    Chocolate = 'chocolate'

class XMLElementList:
    ElementList = (
        XMLElement.Waffles,
        XMLElement.Toast,
        XMLElement.HomeStyle,
        XMLElement.Espresso,
        XMLElement.Frappuccino,
        XMLElement.Tea,
        XMLElement.Chocolate,
    )

class XMLElementAttrib:
    Waffles = (
        'name',
        'price',
        'decscription',
    )
    Toast = (
        'name',
        'price',
        'decscription',
    )
    HomeStyle = (
        'name',
        'price',
        'decscription',
    )
    Espresso = (
        'name',
        'price',
        'decscription',
    )
    Frappuccino = (
        'name',
        'price',
        'decscription',
    )
    Tea = (
        'name',
        'price',
        'decscription',
    )
    Chocolate = (
        'name',
        'price',
        'decscription',
    )

def getXMLElementAttrib(elementName):
    if elementName == XMLElement.Waffles:
        return XMLElementAttrib.Waffles
    elif elementName == XMLElement.Toast:
            return XMLElementAttrib.Toast
    elif elementName == XMLElement.HomeStyle:
            return XMLElementAttrib.HomeStyle
    elif elementName == XMLElement.Espresso:
            return XMLElementAttrib.Espresso
    elif elementName == XMLElement.Frappuccino:
            return XMLElementAttrib.Frappuccino
    elif elementName == XMLElement.Tea:
            return XMLElementAttrib.Tea
    elif elementName == XMLElement.Chocolate:
            return XMLElementAttrib.Chocolate
