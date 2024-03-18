#!/usr/bin/env python3
import argparse
import sys
import time
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)


import msal
from exchangelib import OAuth2AuthorizationCodeCredentials, Configuration, OAUTH2, Account, Identity, Folder
from exchangelib.errors import ErrorServerBusy

SCOPES = ["EWS.AccessAsUser.All"]

parser = argparse.ArgumentParser(description="Moves the messages in one folder to another folder.")
parser.add_argument("--client-id", help="The client ID to use for authentication.", required=True)
parser.add_argument("--authority",
                    help="The authority to use for authentication.",
                    default="https://login.microsoftonline.com/organizations")
parser.add_argument("--username", help="The username to use for authentication.", required=True)
parser.add_argument("--source-principal", help="The principal to move the messages from.")
parser.add_argument("--source-folder", help="The folder to move the messages from.", required=True)
parser.add_argument("--destination-principal", help="The principal to move the messages to.")
parser.add_argument("--destination-folder", help="The folder to move the messages to.", required=True)
parser.add_argument("--server", help="The server to connect to.", default="outlook.office365.com")
parser.add_argument("--interval", help="The interval to use when polling or if an error is encountered, seconds.", type=int, default=120)
parser.add_argument("--poll", help="Poll the source folder for new messages.", action="store_true", default=False)

args = parser.parse_args()
source_principal = args.source_principal or args.username
destination_principal = args.destination_principal or args.username

msal_app = msal.PublicClientApplication(args.client_id, authority=args.authority)
result = msal_app.acquire_token_interactive(scopes=SCOPES, login_hint=args.username)
assert "access_token" in result, f"Failed to acquire token: {result}"


accounts = {}


def account_for_principal(principal) -> Account:
    if principal not in accounts:
        creds = OAuth2AuthorizationCodeCredentials(access_token=result)
        conf = Configuration(server=args.server, auth_type=OAUTH2, credentials=creds)
        accounts[principal] = Account(primary_smtp_address=principal, config=conf, access_type="delegate", autodiscover=False)
    return accounts[principal]


source_account = account_for_principal(source_principal)
destination_account = account_for_principal(destination_principal)
assert source_account.primary_smtp_address == source_principal
assert destination_account.primary_smtp_address == destination_principal


def get_folder_from_path(root, path) -> Folder:
    parts = path.split("/")
    folder = root
    for part in parts:
        folder /= part
    return folder


source_folder = get_folder_from_path(source_account.root, args.source_folder)
destination_folder = get_folder_from_path(destination_account.root, args.destination_folder)

logger.info(f"Moving messages from {source_folder.absolute} ({source_account}) to {destination_folder.absolute} ({destination_account})...")




while True:
    try:
        source_folder.filter().move(to_folder=destination_folder, page_size=1000, chunk_size=100)
        if not args.poll:
            break
    except ErrorServerBusy:
        logger.info("Server busy, back off...")
    if args.interval > 0:
        logger.info(f"Sleeping for {args.interval} seconds...")
        time.sleep(args.interval)
        logger.info("Waking up...")
    else:
        break

