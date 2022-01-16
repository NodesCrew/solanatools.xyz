# coding: utf-8


import config

import os
import json

from lib.rpc import call_rpc
from lib.rpc import get_epoch

DIR_TESTNET = "data/stakes/testnet"
DIR_MAINNET = "data/stakes/mainnet"


def iter_stakes(cluster_rpc):
    """
    """
    params = {
        "method": "getProgramAccounts",
        "params": [
            "Stake11111111111111111111111111111111111111",
            {
                "commitment": "confirmed",
                "encoding": "jsonParsed",
            }
        ]
    }

    for row in call_rpc(params, cluster_rpc=cluster_rpc):

        if row["account"]["data"]["parsed"]["type"] == "initialized":
            continue

        try:
            info = row["account"]["data"]["parsed"]["info"]
        except:
            print(f"Unable to handle {row}")
            continue

        try:
            delegation = info["stake"]["delegation"]
        except:
            print(f"Unable to handle delegation from {row}")
            continue

        yield dict(
            vote_account=delegation["voter"],
            stake_lamports=int(delegation["stake"]),
            epoch_activated=int(delegation["activationEpoch"]),
            epoch_deactivated=int(delegation["deactivationEpoch"]),
            authorized_voter=info["meta"]["authorized"]["staker"],
            authorized_withdrawer=info["meta"]["authorized"]["withdrawer"],
            lockup_epoch=info["meta"]["lockup"]["epoch"],
            lockup_castodian=info["meta"]["lockup"]["custodian"],
            lockup_timestamp=info["meta"]["lockup"]["unixTimestamp"],
        )


def update_stakes(cluster_rpc: str, data_dir: str):
    """ Update approve stakes
    """
    os.makedirs(data_dir, exist_ok=True)
    epoch_no = get_epoch(cluster_rpc=cluster_rpc)

    with open(f"{data_dir}/{epoch_no}.txt", "w+") as w:
        for item in iter_stakes(cluster_rpc=cluster_rpc):
            w.write(f"{json.dumps(item)}\n")


if __name__ == "__main__":
    update_stakes(cluster_rpc=config.RPC_MAINNET, data_dir=DIR_MAINNET)



