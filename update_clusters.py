# coding: utf-8
import json

import config

import os
import collections

from lib.rpc import get_epoch
from lib.rpc import get_cluster_nodes
from lib.rpc import get_vote_accounts

DIR_TESTNET = "data/clusters/testnet"
DIR_MAINNET = "data/clusters/mainnet"


def update_cluster(cluster_rpc, cluster_dir):
    """ Update cluster info
    """
    os.makedirs(cluster_dir, exist_ok=True)

    data = collections.defaultdict(int)
    data["versions_nodes"] = collections.defaultdict(int)
    data["versions_stake"] = collections.defaultdict(int)

    epoch_no = get_epoch(cluster_rpc=cluster_rpc)
    nodes_versions = dict()

    # Get nodes versions
    for node in get_cluster_nodes(cluster_rpc=cluster_rpc):
        pubkey = node["pubkey"]
        nodes_versions[pubkey] = node["version"]

    # Get stake info
    vote_accounts = get_vote_accounts(cluster_rpc=cluster_rpc, merge=False)
    for state, validators in vote_accounts.items():
        for validator in validators:
            pubkey = validator["nodePubkey"]
            version = nodes_versions.get(pubkey, "unknown")

            data["stake_total"] += validator["activatedStake"]
            data["count_total"] += 1
            data["versions_nodes"][version] += 1
            data["versions_stake"][version] += validator["activatedStake"]

            if state == "current":
                data["stake_active"] += validator["activatedStake"]
                data["count_active"] += 1

            else:
                data["stake_delinq"] += validator["activatedStake"]
                data["count_delinq"] += 1

    with open(f"{cluster_dir}/{epoch_no}.txt", "w+") as w:
        w.write(json.dumps(data))


def update_clusters():
    """ Update stats for clusters
    """
    update_cluster(config.RPC_MAINNET, DIR_MAINNET)
    update_cluster(config.RPC_TESTNET, DIR_TESTNET)


if __name__ == "__main__":
    update_clusters()
