#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import configparser as ConfigParser
import os
import sys

try:
    import JsonTableSchema
    from droidcsvhandlerclass import *
    from rosettacsvsectionsclass import RosettaCSVSections
except ModuleNotFoundError:
    try:
        from src.rosetta_csv.droidcsvhandlerclass import *
        from src.rosetta_csv.json_table_schema import JsonTableSchema
        from src.rosetta_csv.rosettacsvsectionsclass import RosettaCSVSections
    except ModuleNotFoundError:
        from rosetta_csv.json_table_schema import JsonTableSchema
        from rosetta_csv.rosettacsvsectionsclass import RosettaCSVSections


class RosettaCSVGenerator:
    # flags for singleIE config
    ieOutput = False
    representationOutput = False
    sectionstatusupdate = False
    lenIE = 0
    lenREP = 0

    # zip name we removed
    zipname = ""

    # Main init options...
    config = None
    singleIE = None
    droidcsv = None
    rosettaschema = None
    rosettasections = None
    includezips = None

    def __init__(self, droidcsv=False, rosettaschema=False, configfile=False):
        self.config = ConfigParser.RawConfigParser()
        self.config.read(configfile)

        if self.config.has_option("application configuration", "includezips"):
            self.includezips = self.__handle_text_boolean__(
                self.config.get("application configuration", "includezips")
            )

        if self.config.has_option("application configuration", "singleIE"):
            self.singleIE = self.__handle_text_boolean__(
                self.config.get("application configuration", "singleIE")
            )

        self.droidcsv = droidcsv

        # NOTE: A bit of a hack, compare with import schema work and refactor
        self.rosettaschema = rosettaschema
        self.readRosettaSchema()

        # Grab Rosetta Sections
        rs = RosettaCSVSections(configfile)
        self.rosettasections = rs.sections

    def __handle_text_boolean__(self, boolvalue):
        if boolvalue.lower() == "true":
            return True
        else:
            return False

    def add_csv_value(self, value):
        field = f'"{value}"'
        return field

    def readRosettaSchema(self):
        f = open(self.rosettaschema, "rb")
        importschemajson = f.read()
        importschema = JsonTableSchema.JSONTableSchema(importschemajson)

        importschemadict = importschema.as_dict()
        importschemaheader = importschema.as_csv_header()

        self.rosettacsvheader = (
            importschemaheader + "\n"
        )  # TODO: Add newline in JSON Handler class?
        self.rosettacsvdict = importschemadict["fields"]
        f.close()

    def createcolumns(self, columno):
        columns = ""
        for column in range(columno):
            columns = columns + '"",'
        return columns

    def csvstringoutput(self, csvlist):
        # String output...
        csvrows = self.rosettacsvheader

        # TODO: Understand how to get this in rosettacsvsectionclass
        # NOTE: Possibly put all basic RosettaCSV stuff in rosettacsvsectionclass?
        # Static ROW in CSV Ingest Sheet
        SIPROW = ['"",'] * len(self.rosettacsvdict)
        SIPROW[0] = '"SIP",'

        # SIP Title...
        if self.config.has_option("rosetta mapping", "SIP Title"):
            SIPROW[1] = '"' + self.config.get("rosetta mapping", "SIP Title") + '",'
        else:
            SIPROW[1] = '"CSV Load",'

        csvrows = csvrows + "".join(SIPROW).rstrip(",") + "\n"

        for sectionrows in csvlist:
            rowdata = ""
            for sectionrow in sectionrows:
                for fielddata in sectionrow:
                    rowdata = rowdata + fielddata + ","
                rowdata = rowdata.rstrip(",") + "\n"
            csvrows = csvrows + rowdata

        # this is the best i can think of because ExLibris have named two fields with the same
        # title in CSV which doesn't help us when we're trying to use unique names for populating rows
        # replaces SIP Title with Title (DC)
        csvrows = csvrows.replace(
            '"Object Type","SIP Title"', '"Object Type","Title (DC)"'
        )

        # finally return the CSV.
        return csvrows

    # TODO: Passed each time we go through the code, improve on this: DO ONCE!
    def __update_section_status__(self, section):
        sect = self.__get_section_key__(section)

        if self.singleIE is True and sect == "IE":
            self.ieOutput = True
            self.lenIE = len(list(section.values())[0])
        if self.singleIE is True and sect == "REPRESENTATION":
            self.representationOutput = True
            self.lenREP = len(list(section.values())[0])

        # One method of only visiting this function only as many times as required...
        if self.ieOutput is True and self.representationOutput is True:
            return True
        else:
            return False

    def __get_section_key__(self, section):
        return list(section)[0]

    def createrosettacsv(self):
        CSVINDEXSTARTPOS = 2
        csvindex = CSVINDEXSTARTPOS

        fields = []

        for item in self.droidlist:
            itemrow = []

            for sections in self.rosettasections:
                # TODO: Could be more intuitive
                # IF relates to single IE for the file or not... IF 'not', then we don't output IE and REP for a single IE
                if not (
                    self.sectionstatusupdate is True
                    and (
                        self.__get_section_key__(sections) == "REPRESENTATION"
                        or self.__get_section_key__(sections) == "IE"
                    )
                ):
                    sectionrow = ['""'] * len(self.rosettacsvdict)

                    section_value = list(sections)[0]

                    sectionrow[0] = self.add_csv_value(section_value)

                    # ROW OUTPUT LOOP STARTS
                    for field in sections[section_value]:
                        if field == self.rosettacsvdict[csvindex]["name"]:
                            if self.config.has_option("rosetta mapping", field):
                                if (
                                    field == "Title" or field == "Title(DC)"
                                ):  # Title(DC) added for future configuration
                                    if (
                                        self.includezips is True
                                        and self.singleIE is True
                                    ):
                                        if self.config.has_option(
                                            "application configuration", "ziptitle"
                                        ):
                                            addvalue = self.config.get(
                                                "application configuration", "ziptitle"
                                            )
                                        else:
                                            addvalue = self.zipname
                                    elif self.singleIE is True:
                                        addvalue = self.config.get(
                                            "rosetta mapping", field
                                        )
                                    else:
                                        rosettafield = self.config.get(
                                            "rosetta mapping", field
                                        )
                                        addvalue = item[rosettafield]
                                else:
                                    rosettafield = self.config.get(
                                        "rosetta mapping", field
                                    )
                                    addvalue = item[rosettafield]

                                sectionrow[csvindex] = self.add_csv_value(addvalue)

                            elif self.config.has_option("static values", field):
                                rosettafield = self.config.get("static values", field)
                                sectionrow[csvindex] = self.add_csv_value(rosettafield)

                            elif self.config.has_option("droid mapping", field):
                                rosettafield = self.config.get("droid mapping", field)

                                # get pathmask for location values...
                                # TODO: Only need to do this once somewhere... e.g. Constructor
                                pathmask = ""
                                if self.config.has_option("path values", "pathmask"):
                                    pathmask = self.config.get(
                                        "path values", "pathmask"
                                    )

                                    addvalue = item[rosettafield]

                                    if (
                                        field == "File Location"
                                        or field == "File Original Path"
                                    ):
                                        if not self.includezips:
                                            basedirname = (
                                                os.path.dirname(item[rosettafield])
                                                + "\\"
                                            )
                                            addvalue = basedirname.replace(
                                                pathmask, ""
                                            ).replace("\\", "/")
                                            # TODO: Test against other cases, workaround for no directory structure in ZIP
                                            if addvalue == "/" and len(addvalue) == 1:
                                                addvalue = ""
                                        else:
                                            path = item["URI"]
                                            addvalue = (
                                                "/".join(
                                                    urlparse(path).path.split("/")[1:-1]
                                                )
                                                .replace(pathmask, "")
                                                .replace("\\", "/")
                                                + "/"
                                            )
                                    # if field == 'File Original Path':
                                    #   addvalue = item[rosettafield].replace(pathmask, '').replace('\\','/')

                                sectionrow[csvindex] = self.add_csv_value(addvalue)
                            else:
                                # If we haven't a value, add a blank field...
                                sectionrow[csvindex] = self.add_csv_value("")

                            csvindex += 1

                    itemrow.append(sectionrow)
                    # ROW OUTPUT LOOP ENDS

                # Need to know to output sections if we have a single IE
                if not self.sectionstatusupdate and self.singleIE:
                    self.sectionstatusupdate = self.__update_section_status__(sections)

            # add row to sheet
            fields.append(itemrow)

            # reset field entry point, default two represents Object Type and SIP Title (see schema)
            csvindex = CSVINDEXSTARTPOS
            if self.singleIE:
                number_of_empty_fields = CSVINDEXSTARTPOS + self.lenIE + self.lenREP
                # len IE + Len REP?
                csvindex = number_of_empty_fields

        return self.csvstringoutput(fields)

    def readExportCSV(self):
        if self.exportsheet is not False:
            csvhandler = genericCSVHandler()
            exportlist = csvhandler.csvaslist(self.exportsheet)
            return exportlist

    def readDROIDCSV(self):
        if self.droidcsv is not False:
            droidcsvhandler = droidCSVHandler()
            droidlist = droidcsvhandler.readDROIDCSV(self.droidcsv)
            droidlist = droidcsvhandler.removefolders(droidlist)
            if not self.includezips:
                droidlist = droidcsvhandler.removecontainercontents(droidlist)

            # TODO: Move to DROIDCSVHANDLER Class
            if self.includezips:
                newlist = []
                for d in droidlist:
                    if droidcsvhandler.getURIScheme(d["URI"]) != "file":
                        newlist.append(d)
                    else:
                        self.zipname = d["NAME"]

                droidlist = newlist

            if len(droidlist) == 0:
                sys.exit(
                    "ERROR: Listing empty. Check ingest from ZIP settings, or contents of DROID report."
                )

            return droidlist

    def export2rosettacsv(self):
        if not self.droidcsv:
            return ""
        self.droidlist = self.readDROIDCSV()
        return self.createrosettacsv()
