# coding: utf-8
import os

import config

import glob
import base58
import base64
import datetime

from lib.rpc import call_rpc
from lib.rpc import get_epoch

STATES = {
    0: "Uninitialized",
    1: "Pending",
    2: "Rejected",
    3: "Approved"
}


def iter_signups():
    """ Yields tn_pubkey, mn_pubkey, state from RPC call
    """
    params = {
        "method": "getProgramAccounts",
        "params": [
            "reg8X1V65CSdmrtEjMgnXZk96b9SUSQrJ8n1rP1ZMg7",
            {
                "commitment": "confirmed",
                "encoding": "base64",
                "filters": [{"dataSize": 65}]
            }
        ]
    }

    for row in call_rpc(params, cluster_rpc=config.RPC_MAINNET):

        coded_string = row["account"]["data"][0]
        vector = base64.b64decode(coded_string)

        tn_pubkey = base58.b58encode(vector[:32])
        state = vector[64]

        # Send only pubkeys with pending status
        if state == 1:
            yield tn_pubkey.decode()


def get_first_transaction(tn_pubkey):
    """ Get first transaction for testnet key
    """
    params = {
        "method": "getSignaturesForAddress",
        "params": [
            tn_pubkey,
            {
                "encoding": "base64",
                "filters": [{"dataSize": 65}]
            }
        ]
    }

    trx_slots = set()
    for trx in call_rpc(params, cluster_rpc=config.RPC_MAINNET):
        trx_slots.add(trx["slot"])

    if not trx_slots:
        return None

    return min(trx_slots)


def save_data(path, data):
    """ Save data into file
    """
    with open(path, "w+") as w:
        for tn_pubkey, first_trx in data.items():
            w.write(f"{tn_pubkey};{first_trx}\n")


def save_epoch_data(epoch_no, data):
    """ Save data by epoches
    """
    save_data(f"data/signups/epoches/{epoch_no}.txt", data)


def save_date_data(data):
    """ Save data by dates
    """
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    save_data(f"data/signups/dates/{today}.txt", data)


def update_signups():
    """ Update approve states
    """
    os.makedirs("data/signups/dates", exist_ok=True)
    os.makedirs("data/signups/epoches", exist_ok=True)

    epoch_no = get_epoch(cluster_rpc=config.RPC_TESTNET)

    cached_validators = dict()

    # Skip validators from github
    for p in sorted(glob.glob("data/validators-testnet/*.txt"), reverse=True):
        with open(p) as f:
            github_validators = set(x.strip() for x in f)

    # Skip validators from cache
    for p in sorted(glob.glob("data/signups/*.txt")):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    tn_pubkey, first_trx = line.split(";")
                except ValueError:
                    print(line)
                    exit(-1)
                cached_validators[tn_pubkey] = first_trx

    for tn_pubkey in iter_signups():
        # Skip known validators
        if tn_pubkey in github_validators:
            continue
        if tn_pubkey in cached_validators:
            continue

        first_trx = get_first_transaction(tn_pubkey)
        if not first_trx:
            print("Unable to get first transaction for %s" % tn_pubkey)

        # Prevent duplicate request
        cached_validators[tn_pubkey] = first_trx

        if not len(cached_validators) % 10:
            save_date_data(cached_validators)
            save_epoch_data(epoch_no, cached_validators)

    save_date_data(cached_validators)
    save_epoch_data(epoch_no, cached_validators)


if __name__ == "__main__":
    update_signups()

