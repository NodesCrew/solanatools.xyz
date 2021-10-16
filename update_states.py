# coding: utf-8

import config

import base58
import base64

from lib.rpc import call_rpc
from lib.rpc import get_epoch

"""
https://github.com/solana-labs/stake-o-matic/blob/master/program/src/state.rs

pub enum ParticipantState {
    /// Default account state after creating it
    Uninitialized,
    
    /// The participant's application is pending
    Pending,

    /// The participant's application was rejected
    Rejected,

    /// Participant is enrolled
    Approved,
}
"""
STATES = {
    0: "Uninitialized",
    1: "Pending",
    2: "Rejected",
    3: "Approved"
}


def iter_states():
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

    signups = dict()

    for row in call_rpc(params, cluster_rpc=config.RPC_MAINNET):

        coded_string = row["account"]["data"][0]
        vector = base64.b64decode(coded_string)

        tn_pubkey = base58.b58encode(vector[:32])
        mn_pubkey = base58.b58encode(vector[32:64])
        state = vector[64]

        yield tn_pubkey.decode(), mn_pubkey, STATES[state]


def update_states():
    """ Update approve states
    """
    epoch_no = get_epoch(cluster_rpc=config.RPC_TESTNET)

    with open("data/states/%d.txt" % epoch_no, "w+") as w:
        for tn_pubkey, _, state in iter_states():
            w.write("%s;%s\n" % (tn_pubkey, state))


if __name__ == "__main__":
    update_states()

