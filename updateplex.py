#!/usr/bin/env python3

"""
Simple updater for Plex Media Server.
"""

import argparse
import logging
import os
import requests
import subprocess
import sys

from xml.etree import ElementTree as etree

PLEX_TOKEN = 'XXXXXXXXXXXXXXXXXX'
PLEX_URL = 'http://localhost:32400/updater/status'
LOG_FILE = 'updateplex.log'
DOWNLOAD_DIR = '/tmp'

def set_up():
    levels = {
            'INFO': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR,
            'DEBUG': logging.DEBUG,
            }
    logging.basicConfig(
        filename=ARGS.log_file,
        format='%(asctime)s %(levelname)s\t%(funcName)s\t%(message)s',
        datefmt='%b %d %T',
        level=levels[ARGS.log_level],
    )

def check_for_updates(url):
    """Requests plexmediaserver update status and initiates update if possible.

    Args:
        url: string, URI for Plex API /updater/status endpoint

    Returns:
        None
    """
    logging.debug("Checking for updates...")
    url_args = {'X-Plex-Token': PLEX_TOKEN}
    api_response = requests.get(url, params=url_args)
    update_available = etree.fromstring(api_response.text).get('size')
    if update_available == '1':
        logging.debug("Update available!")
        download_url = etree.fromstring(api_response.text).get('downloadURL')
        update_plex(download_url=download_url)
        # write to log
        sys.exit(0)
    elif update_available == '0':
        logging.debug("No update available. Bye!")
        sys.exit(0)
    else:
        logging.error("Something broke while checking")
        sys.exit(1)


def download_plex(url):
    update_package = requests.get(url, stream=True)
    if ARGS.filename is None:
        ARGS.filename = update_package.url.split('/')[-1]
    with open(os.path.join(ARGS.directory, ARGS.filename), 'wb') as output_file:
        logging.info("Downloading %s..." % update_package.url)
        for chunk in update_package.iter_content(chunk_size=1024):
            output_file.write(chunk)
            logging.debug("Writing chunk...")
        update_package.close()
        logging.info("Update downloaded.")
        return


def update_plex(download_url):
    try:
        download_plex(url=download_url)
        subprocess.run(['/usr/bin/sudo', '/usr/bin/dpkg', '-i',
                        ARGS.directory + ARGS.filename])
        logging.info("Success!")
    except:
        logging.error("Something broke while downloading.")
        print("Failure.")
        sys.exit(1)


if __name__ == "__main__":
    global ARGS
    parser = argparse.ArgumentParser(description='Update a local Plex Meda Server.')
    parser.add_argument('-l', '--log_file', action='store', type=str, default='./updateplex.log',
                        help='Specify a logfile destination (default: ./updateplex.log)')
    parser.add_argument('-L', '--log_level', action='store', type=str, default='INFO',
                        help='Logging level. One of: INFO, WARN, ERROR, DEBUG')
    parser.add_argument('-d', '--directory', action='store', type=str, default='/tmp/',
                        help='Download folder for update file (default: /tmp/)')
    parser.add_argument('-r', '--dry-run', action='store_true',
                        help='Do not apply the update (default: false)')
    parser.add_argument('-f', '--filename', action='store', type=str, default=None,
                        help='Optional: specify an output filename other than as-downloaded')
    ARGS = parser.parse_args()
    set_up()
    check_for_updates(PLEX_URL)
