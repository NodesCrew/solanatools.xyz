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
    print(f"Update credits for {cluster_rpc}")

    # Read credits database
    credits = collections.defaultdict(dict)
    for epoch_path in sorted(glob.glob(dir_name + "/*.txt")):
        epoch_no = int(epoch_path.rsplit("/", 1)[-1].split(".")[0])

        for line in iter_file(epoch_path):
            pubkey, *credits_range = line.split(";")
            credits_range = list(map(int, credits_range))
            credits[epoch_no][pubkey] = credits_range

    # Grab fresh data from RPC
    for validator in get_vote_accounts(cluster_rpc=cluster_rpc, merge=1):
        pubkey = validator["nodePubkey"]
        for epoch, *credits_range in validator["epochCredits"]:
            credits[epoch][pubkey] = list(map(int, credits_range))

    # Save data
    for epoch_no, data in credits.items():
        with open(dir_name + "/%s.txt" % epoch_no, "w+") as w:
            for pubkey, credits_range in sorted(data.items()):
                if len(credits_range) < 2:
                    print(f"Skip vote credits for {pubkey} savings because "
                          f"wrong data received: {credits_range}")
                    continue
                w.write("%s;%s;%s\n" % (pubkey,
                                        credits_range[0],
                                        credits_range[1]))


if __name__ == "__main__":
    os.makedirs(DIR_MAINNET, exist_ok=True)
    os.makedirs(DIR_TESTNET, exist_ok=True)

    update_credits(config.RPC_MAINNET, DIR_MAINNET)
    update_credits(config.RPC_TESTNET, DIR_TESTNET)
