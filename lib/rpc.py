# coding: utf-8

import json
import config
import requests
from lib.common import fatal_error


http = requests.Session()


def call_rpc(params, cluster_rpc=None):
    """ Send request to RPC endpoint and returns result
    """
    r = http.post(
        cluster_rpc or config.RPC_TESTNET,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, **params}),
        headers={"Content-Type": "application/json"}
    )

    try:
        return r.json()["result"]
    except Exception as e:
        fatal_error("Unable to parse response: status=%s, text=%s\n%s" % (
            r.status_code, r.text, e))

    fatal_error("Unable to call: %s" % {"jsonrpc": "2.0", "id": 1, **params})


def get_epoch(cluster_rpc):
    """ Get current epoch number from testnet RPC
    """
    result = call_rpc({"method": "getEpochInfo"}, cluster_rpc=cluster_rpc)
    return result["epoch"]


def get_slots_info(cluster_rpc):
    """ Get current slot in epoch
    """
    epoch_info = call_rpc({"method": "getEpochInfo"}, cluster_rpc=cluster_rpc)
    return epoch_info["slotIndex"], epoch_info["slotsInEpoch"]


def get_cluster_nodes(cluster_rpc):
    """ Get cluster nodes
    """
    result = call_rpc({"method": "getClusterNodes"}, cluster_rpc=cluster_rpc)
    return result


def get_vote_accounts(cluster_rpc, merge=False):
    """ Returns validators
    """
    voters = call_rpc({"method": "getVoteAccounts"}, cluster_rpc=cluster_rpc)

    if not merge:
        return voters

    return [*voters["current"], *voters["delinquent"]]
