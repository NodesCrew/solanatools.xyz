# coding: utf-8

import json
import config
from lib.common import fatal_error


def call_rpc(http, params, rpc_endpoint=None):
    """ Send request to RPC endpoint and returns result
    """
    r = http.post(
        rpc_endpoint or config.RPC_TESTNET,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, **params}),
        headers={"Content-Type": "application/json"}
    )

    try:
        return r.json()["result"]
    except Exception as e:
        fatal_error("Unable to parse response: status=%s, text=%s\n%s" % (
            r.status_code, r.text, e))

    fatal_error("Unable to call: %s" % {"jsonrpc": "2.0", "id": 1, **params})


def get_epoch(http):
    """ Get current epoch number from testnet RPC
    """
    result = call_rpc(http, {"method": "getEpochInfo"})
    return result["epoch"]
