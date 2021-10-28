# coding: utf-8

import config

import os
import glob
import requests
import collections

from lib.rpc import get_vote_accounts
from lib.common import iter_file

DIR_TESTNET = "data/credits/testnet"
DIR_MAINNET = "data/credits/mainnet"


def update_credits(cluster_rpc: str, dir_name: str, ):
    """ Update credits for cluster nodes
    """
    os.makedirs(DIR_TESTNET, exist_ok=True)

    # Read credits database
    credits = collections.defaultdict(dict)
    for epoch_path in sorted(glob.glob(dir_name + "/*.txt")):
        epoch_no = int(epoch_path.rsplit("/", 1)[-1].split(".")[0])

        for line in iter_file(epoch_path):
            tn_pubkey, epoch_creds = line.split(";")
            credits[epoch_no][tn_pubkey] = int(epoch_creds)

    # Grab fresh data from RPC
    for validator in get_vote_accounts(cluster_rpc=cluster_rpc, merge=1):
        tn_pubkey = validator["nodePubkey"]
        for epoch, epoch_creds, prev_epoch_creds in validator["epochCredits"]:
            credits[epoch][tn_pubkey] = epoch_creds

    # Save data
    for epoch_no, data in credits.items():
        with open(dir_name + "/%s.txt" % epoch_no, "w+") as w:
            for tn_pubkey, epoch_creds in sorted(data.items()):
                w.write("%s;%s\n" % (tn_pubkey, epoch_creds))


if __name__ == "__main__":
    os.makedirs(DIR_MAINNET, exist_ok=True)
    os.makedirs(DIR_TESTNET, exist_ok=True)

    update_credits(config.RPC_MAINNET, DIR_MAINNET)
    update_credits(config.RPC_TESTNET, DIR_TESTNET)
