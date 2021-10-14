# coding: utf-8

import config

import os
import glob
import requests
import collections

from lib.rpc import get_vote_accounts
from lib.common import iter_file

DIR_CREDITS = "data/credits"


def update_credits():
    """ Update credits for cluster nodes
    """
    os.makedirs(DIR_CREDITS, exist_ok=True)

    # Read credits database
    credits = collections.defaultdict(dict)
    for epoch_path in sorted(glob.glob(DIR_CREDITS + "/*.txt")):
        epoch_no = int(epoch_path.rsplit("/", 1)[-1].split(".")[0])

        for line in iter_file(epoch_path):
            tn_pubkey, epoch_creds = line.split(";")
            credits[epoch_no][tn_pubkey] = int(epoch_creds)

    # Grab fresh data from RPC
    for validator in get_vote_accounts(cluster_rpc=config.RPC_TESTNET, merge=1):
        tn_pubkey = validator["nodePubkey"]
        for epoch, epoch_creds, prev_epoch_creds in validator["epochCredits"]:
            credits[epoch][tn_pubkey] = epoch_creds
            credits[epoch - 1][tn_pubkey] = prev_epoch_creds

    # Save data
    for epoch_no, data in credits.items():
        with open(DIR_CREDITS + "/%s.txt" % epoch_no, "w+") as w:
            for tn_pubkey, epoch_creds in sorted(data.items()):
                w.write("%s;%s\n" % (tn_pubkey, epoch_creds))


if __name__ == "__main__":
    update_credits()
