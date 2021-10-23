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


def github_get_pubkeys():
    print("Send github request")
    url = "https://github.com/solana-labs/stake-o-matic/wiki/"
    res = requests.get(url)

    validators = set(RE_GITHUB_VALIDATORS.findall(res.text))
    print("Total validators from stake-o-matic: %d" % len(validators))

    return validators


def save_data(data):
    for epoch_no, epoch_rewards in data.items():
        with open(f"data/rewards/{epoch_no}.txt", "w+") as w:
            w.write("\n".join(sorted(epoch_rewards)))


def grab_rewards(vote_account):
    print(f"[{datetime.datetime.utcnow()}]: grab rewards for {vote_account}")

    command = [
        "solana",
        "-um", "vote-account",  vote_account,
        "--with-rewards",
        #"--num-rewards-epochs", "2",
        "--output", "json"
    ]

    data = subprocess.check_output(command)

    for epoch_info in json.loads(data.decode())["epochRewards"]:
        yield epoch_info["epoch"], epoch_info["amount"]


def update_rewards_mainnet():
    """ Update epoch rewards for validators in mainnet
    """
    os.makedirs("data/rewards", exist_ok=True)

    # Get epoch
    curr_epoch = get_epoch(cluster_rpc=config.RPC_MAINNET)
    prev_epoch = curr_epoch - 1

    # Get github validators
    github_pubkeys = github_get_pubkeys()

    # Prevent duplicate requests
    epoch_data = collections.defaultdict(list)
    last_epoch_pubkeys = set()

    # Read exists data
    for epoch_path in glob.glob("data/rewards/*.txt"):
        epoch_no = int(epoch_path.rsplit("/", 1)[-1].split(".")[0])
        with open(epoch_path) as f:
            epoch_data[epoch_no] = list(line.strip() for line in f)

    # Get pubkeys from last epoch data for grab skipping
    with suppress(FileNotFoundError):
        with open(f"data/rewards/{prev_epoch}.txt") as f:
            last_epoch_pubkeys = set(line.split(";")[0] for line in f)

    for node in get_vote_accounts(config.RPC_MAINNET, merge=True):
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

        for epoch_no, lamports in grab_rewards(vote_pubkey):
            data = map(str, [node_pubkey, vote_pubkey, lamports])
            epoch_data[epoch_no].append(";".join(data))

            save_data(epoch_data)



if __name__ == "__main__":
    update_rewards_mainnet()
