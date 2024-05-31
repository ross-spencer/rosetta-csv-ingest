"""Rosetta CSV Generator.

Creates a generic Rosetta ingest CSV from a DROID formatted export.
"""

import argparse
import logging
import time

try:
    from RosettaCSVGenerator import RosettaCSVGenerator
except ModuleNotFoundError:
    try:
        from src.rosetta_csv.RosettaCSVGenerator import RosettaCSVGenerator
    except ModuleNotFoundError:
        from rosetta_csv.RosettaCSVGenerator import RosettaCSVGenerator


logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
)

# Default to UTC time.
logging.Formatter.converter = time.gmtime


def rosettacsvgeneration(droidcsv, rosettaschema, configfile):
    csvgen = RosettaCSVGenerator(droidcsv, rosettaschema, configfile)
    print(csvgen.export2rosettacsv())


def main():
    """Primary entry point for this script."""
    parser = argparse.ArgumentParser(
        description="generate Rosetta Ingest CSV from DROID CSV Reports."
    )
    parser.add_argument(
        "--csv", help="single DROID CSV to read.", default=False, required=True
    )
    parser.add_argument(
        "--ros", help="rosetta CSV validation schema.", default=False, required=True
    )
    parser.add_argument(
        "--cfg", help="config file for field mapping.", default=False, required=True
    )
    global args
    args = parser.parse_args()
    rosettacsvgeneration(args.csv, args.ros, args.cfg)


if __name__ == "__main__":
    main()
