# coding: utf-8
import config

import os
import json

from lib.rpc import http
from lib.rpc import get_epoch


def grab_data():
    """ Grab data from Solana Foundation Delegation Program status page
    """
    nodes = []

    for x in range(0, 50):
        url = config.SFDP_URL % (x * 99)
        d = http.get(url).json()

        if "data" not in d:
            print(d.keys())
            break

        if not d["data"]:
            break

        for row in d["data"]:
            nodes.append(json.dumps(row))

    return list(set(nodes))


def update_onboarding():
    """ Update onboarding numbers and save
    """
    os.makedirs("data/onboarding", exist_ok=True)
    epoch_no = get_epoch(cluster_rpc=config.RPC_TESTNET)

    with open("data/onboarding/%d.txt" % epoch_no, "w+") as w:
        for node in grab_data():
            w.write(node + "\n")


if __name__ == "__main__":
    update_onboarding()


