# coding: utf-8

import config

import re
import os
import requests

from lib.rpc import get_epoch

GITHUB_URL = str("https://raw.githubusercontent.com/solana-labs/stake-o-matic/"
                 "master/bot/src/validator_list.rs")

RE_PUBKEY = re.compile(r'"([a-zA-Z0-9]+)?",')

DIR_TESTNET_VALIDATORS = "data/validators-testnet"


def update_validators_testnet():
    """ Update testnet validators list
    """
    os.makedirs(DIR_TESTNET_VALIDATORS, exist_ok=True)
    epoch_no = get_epoch(cluster_rpc=config.RPC_TESTNET)
    html = requests.get(GITHUB_URL).text

    with open(f"{DIR_TESTNET_VALIDATORS}/{epoch_no}.txt", "w+") as w:
        for tn_pubkey in RE_PUBKEY.findall(html):
            w.write(f"{tn_pubkey}\n")


if __name__ == "__main__":
    update_validators_testnet()

