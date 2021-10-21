# coding: utf-8

import glob
import json
import jinja2
import datetime

from contextlib import suppress
from collections import defaultdict

from lib.common import iter_file


def render(jinja2_env, template_name, context):
    template = jinja2_env.get_template("%s.html" % template_name)

    with open("www/%s.html" % template_name, "w+") as w:
        w.write(template.render(**context))


def get_actual_states():
    max_epoch = 0
    states = dict()

    for epoch_file in sorted(glob.glob("data/states/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        max_epoch = max(max_epoch, epoch_no)

    for line in iter_file("data/states/%s.txt" % max_epoch):
        tn_pubkey, state = line.split(";")
        states[tn_pubkey] = state

    return states


def get_index_context():
    """ Get vars for index.html and useful templates
    """
    for epoch_file in sorted(glob.glob("data/clusters/mainnet/*.txt")):
        with open(epoch_file) as f:
            mainnet = json.load(f)

    for epoch_file in sorted(glob.glob("data/clusters/testnet/*.txt")):
        with open(epoch_file) as f:
            testnet = json.load(f)

    return dict(mainnet=mainnet, testnet=testnet)


def get_onboarding_context():
    """ Get vars for onboarding-history.html template
    """
    def node_scoring(node):
        bonus_13 = float(node["bonus_13"] or 0)
        bonus_207 = float(node["bonus_207"] or 0)
        credits_64p = float(node["credits_64p"] or 0)
        return "%.5f" % (
                (bonus_207 * .25) + (bonus_13 * .25) + (credits_64p * .5))

    nodes = dict()
    epoches = set()
    states = get_actual_states()

    for epoch_file in sorted(glob.glob("data/onboarding/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        epoches.add(epoch_no)

        with open(epoch_file) as f:
            for line in f:
                njson = json.loads(line)
                tn_pubkey = njson["testnet_pk"]
                node_position = njson["onboarding_number"]

                bonus_13, bonus_207 = None, None
                credits_64, credits_64p = None, None

                with suppress(TypeError):
                    cs = njson["tn_calculated_stats"]
                    bonus_13 = "%.2f" % (
                                cs["percent_bonus_last_13_epochs"] * 100)
                    bonus_207 = "%.2f" % (
                                cs["percent_bonus_since_aug1_2021"] * 100)
                    credits_64 = int(cs["vote_credits_last_64_epochs"])
                    credits_64p = "%.2f" % (cs["vote_credit_score"] * 100)

                if tn_pubkey not in nodes:
                    nodes[tn_pubkey] = {
                        "testnet_pk": tn_pubkey,
                        "mainnet_beta_pk": njson["mainnet_beta_pk"],
                        "tds_onboarding_group": njson["tds_onboarding_group"],
                        "positions": defaultdict(dict),
                    }

                nodes[tn_pubkey]["state"] = states.get(tn_pubkey, "Unknown")
                nodes[tn_pubkey]["bonus_13"] = bonus_13
                nodes[tn_pubkey]["bonus_207"] = bonus_207
                nodes[tn_pubkey]["credits_64"] = credits_64
                nodes[tn_pubkey]["credits_64p"] = credits_64p
                nodes[tn_pubkey]["scoring"] = node_scoring(nodes[tn_pubkey])
                nodes[tn_pubkey]["positions"][epoch_no] = node_position

    epoches = list(sorted(epoches))

    nodes_clean = dict()
    for tn_pubkey, node in nodes.items():
        if any(node["positions"].values()):
            nodes_clean[tn_pubkey] = node

    return dict(nodes=nodes_clean,
                epoches=epoches,
                datetime=datetime.datetime.utcnow())


def get_signups_context():
    """ Get vars for signups.html template
    """
    nodes = dict()
    epoches = set()
    epoch_positions = defaultdict(list)
    github_validators = defaultdict(set)

    # Read known validators from github (later will excluded from rating)
    for epoch_file in sorted(glob.glob("data/validators-testnet/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        with open(epoch_file) as f:
            github_validators[epoch_no] = set(x.strip() for x in f)

    # Map slots to positoons
    for epoch_file in sorted(glob.glob("data/signups/epoches/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        epoches.add(epoch_no)

        with open(epoch_file) as f:
            for line in f:
                tn_pubkey, slot = line.strip().split(";")

                # Skip validator if already in github
                if tn_pubkey in github_validators[epoch_no]:
                    print(f"Skip {tn_pubkey} as github validator")
                    continue

                epoch_positions[epoch_no].append(int(slot))
        epoch_positions[epoch_no].sort()

    # Iterate
    for epoch_file in sorted(glob.glob("data/signups/epoches/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        epoches.add(epoch_no)

        with open(epoch_file) as f:
            for line in f:
                tn_pubkey, slot = line.strip().split(";")
                slot = int(slot)

                if tn_pubkey not in nodes:
                    nodes[tn_pubkey] = {
                        "testnet_pk": tn_pubkey,
                        "slots": defaultdict(dict),
                        "positions": defaultdict(dict),
                    }

                try:
                    position = epoch_positions[epoch_no].index(slot) + 1
                    nodes[tn_pubkey]["slots"][epoch_no] = int(slot)
                except ValueError:
                    position = None
                    nodes[tn_pubkey]["slots"][epoch_no] = None

                nodes[tn_pubkey]["positions"][epoch_no] = position

    epoches = list(sorted(epoches))
    return dict(nodes=nodes,
                epoches=epoches,
                datetime=datetime.datetime.utcnow())


def get_rewards_context():
    """ Get vars for rewards.html template
    """
    nodes = dict()
    epoches = set()

    # Iterate
    for epoch_file in sorted(glob.glob("data/rewards/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        epoches.add(epoch_no)

        with open(epoch_file) as f:
            for line in f:
                node_pubkey, vote_pubkey, rewards = line.strip().split(";")
                rewards = "%.2f" % (int(rewards) / 1000000000)

                if node_pubkey not in nodes:
                    nodes[node_pubkey] = {
                        "node_pubkey": node_pubkey,
                        "vote_pubkey": vote_pubkey,
                        "rewards": defaultdict(dict)
                    }

                nodes[node_pubkey]["rewards"][epoch_no] = rewards

    epoches = list(sorted(epoches))
    return dict(nodes=nodes,
                epoches=epoches,
                datetime=datetime.datetime.utcnow())

def generate_static():
    jinja2_loader = jinja2.FileSystemLoader("templates")
    jinja2_env = jinja2.Environment(loader=jinja2_loader)

    render(jinja2_env, "index", get_index_context())
    render(jinja2_env, "useful", get_index_context())
    render(jinja2_env, "rewards", get_rewards_context())
    render(jinja2_env, "signups", get_signups_context())
    render(jinja2_env, "onboarding-history", get_onboarding_context())



if __name__ == "__main__":
    generate_static()
