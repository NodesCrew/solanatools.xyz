# coding: utf-8
import config

from lib.rpc import get_epoch
from lib.rpc import get_vote_accounts

import os
import re
import glob
import json
import datetime
import requests
import subprocess
import collections
from contextlib import suppress

MIN_COMMISSION = 1
MAX_COMMISSION = 10

RE_GITHUB_VALIDATORS = re.compile(r'">Validator ([a-zA-Z0-9]+)')

DIR_TESTNET = "data/credits_deep/testnet"
DIR_MAINNET = "data/credits_deep/mainnet"


def github_get_pubkeys():
    print("Send github request")
    url = "https://github.com/solana-labs/stake-o-matic/wiki/"
    res = requests.get(url)

    validators = set(RE_GITHUB_VALIDATORS.findall(res.text))
    print("Total validators from stake-o-matic: %d" % len(validators))

    return validators


def save_data(data: dict, data_dir: str):
    for epoch_no, info in data.items():
        with open(f"{data_dir}/{epoch_no}.txt", "w+") as w:
            for pubkey, creds in sorted(info.items()):
                w.write(f"{pubkey};{creds[0]};{creds[1]}\n")


def grab_credits(cluster_rpc: str, vote_account: str):
    print(f"[{datetime.datetime.utcnow()}]: grab credits for {vote_account}")

    command = [
        "solana",
        "--url", cluster_rpc,
        "vote-account",  vote_account,
        "--output", "json"
    ]

    data = subprocess.check_output(command)

    for info in json.loads(data.decode())["epochVotingHistory"]:
        # print(f'Yield {info["epoch"]}, {info["credits"]}, {info["prevCredits"]}')
        yield info["epoch"], info["credits"], info["prevCredits"]


def update_credits_deep(cluster_rpc: str, data_dir: str):
    """ Update epoch rewards for validators in mainnet
    """
    os.makedirs(data_dir, exist_ok=True)

    # Get github validators
    github_pubkeys = github_get_pubkeys()

    # Prevent duplicate requests
    epoch_data = collections.defaultdict(dict)
    last_epoch_pubkeys = set()

    # Read exists data
    for epoch_path in glob.glob("data/rewards/*.txt"):
        epoch_no = int(epoch_path.rsplit("/", 1)[-1].split(".")[0])
        with open(epoch_path) as f:
            for line in f:
                line = line.strip()
                pubkey, *creds = line.split(";")
            epoch_data[epoch_no][pubkey] = creds

    for node in get_vote_accounts(cluster_rpc=cluster_rpc, merge=True):
        commission = node["commission"]
        if commission not in range(MIN_COMMISSION, MAX_COMMISSION + 1):
            continue

        node_pubkey = node["nodePubkey"]

        if node_pubkey in last_epoch_pubkeys:
            print(f"Skip grabbing for {node_pubkey} - already in our database")
            continue

        if node_pubkey not in github_pubkeys:
            print(f"Skip grabbing for {node_pubkey} - not in bot database")
            continue

        vote_pubkey = node["votePubkey"]

        for epoch_no, *creds in grab_credits(cluster_rpc, vote_pubkey):
            epoch_data[epoch_no][node_pubkey] = creds
            save_data(epoch_data, data_dir=data_dir)


if __name__ == "__main__":
    update_credits_deep(cluster_rpc=config.RPC_MAINNET, data_dir=DIR_MAINNET)
    update_credits_deep(cluster_rpc=config.RPC_TESTNET, data_dir=DIR_TESTNET)
