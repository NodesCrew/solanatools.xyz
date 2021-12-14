# coding: utf-8

import glob
import json
import jinja2
import datetime

from contextlib import suppress
from collections import defaultdict

from lib.common import iter_file
from distutils.version import StrictVersion


def render(jinja2_env, template_name, context, target=None):
    template = jinja2_env.get_template("%s.html" % template_name)

    if not target:
        target = template_name

    with open("www/%s.html" % target, "w+") as w:
        w.write(template.render(**context))


def get_actual_states():
    max_epoch = 0
    states = dict()

    for epoch_file in sorted(glob.glob("data/states/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        max_epoch = max(max_epoch, epoch_no)

    print(f"Max epoch for states is {max_epoch}")

    for line in iter_file("data/states/%s.txt" % max_epoch):
        tn_pubkey, state = line.split(";")
        states[tn_pubkey] = state

    return states


def read_cluster_info(cluster_name):
    max_epoch = 0

    def clear_versions(versions):
        valid = []
        for v in versions:
            if v not in ("null", "unknown"):
                valid.append(v)
            elif "0.0.0" not in valid:
                valid.append("0.0.0")
        return valid

    for epoch_file in sorted(glob.glob(f"data/clusters/{cluster_name}/*.txt")):
        epoch_no = int(epoch_file.split("/")[-1][0:3])
        max_epoch = max(max_epoch, epoch_no)

    with open(f"data/clusters/{cluster_name}/{max_epoch}.txt") as f:
        cluster_info = json.load(f)

    _versions = clear_versions(cluster_info["versions_nodes"].keys())
    _versions.sort(key=StrictVersion)

    cluster_info["epoch_no"] = max_epoch
    cluster_info["versions_sorted"] = _versions
    return cluster_info


def get_index_context():
    """ Get vars for index.html and useful templates
    """
    testnet = read_cluster_info("testnet")
    mainnet = read_cluster_info("mainnet")

    # Get queue size
    return dict(mainnet=mainnet, testnet=testnet)


def get_onboarding_context():
    """ Get vars for onboarding-history.html template
    """
    def node_scoring(node):
        bonus_13 = float(node["bonus_13"] or 0)
        bonus_207 = float(node["bonus_207"] or 0)
        credits_64p = float(node["credits_64p"] or 0)
        return "%.2f" % (
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

    epoches = list(sorted(epoches))[-5:]

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
                    # print(f"Skip {tn_pubkey} as github validator")
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


def get_credits_context(cluster):
    """ Render only last 5 epoches
    """

    nodes = dict()
    epoches = []

    for epoch_file in sorted(glob.glob(f"data/credits/{cluster}/*.txt")):
        try:
            epoch_no = int(epoch_file.split("/")[-1][0:3])
            epoches.append(epoch_no)
        except ValueError:
            continue
    epoches = epoches[-7:]

    for epoch_no in epoches:
        with open(f"data/credits/{cluster}/{epoch_no}.txt") as f:
            for line in f:
                pubkey, *credits_ = line.split(";")
                if pubkey not in nodes:
                    nodes[pubkey] = {
                        "pubkey": pubkey,
                        "credits": defaultdict(dict),
                    }
                credits_ = list(map(int, credits_))
                nodes[pubkey]["credits"][epoch_no] = credits_[0] - credits_[1]

    return {
        "nodes": nodes,
        "epoches": epoches,
        "cluster": cluster
    }


def generate_static():
    """ Generate all known pages
    """
    jinja2_loader = jinja2.FileSystemLoader("templates")
    jinja2_env = jinja2.Environment(loader=jinja2_loader)

    render(jinja2_env, "index", get_index_context())
    render(jinja2_env, "useful", get_index_context())
    render(jinja2_env, "rewards", get_rewards_context())
    render(jinja2_env, "signups", get_signups_context())
    render(jinja2_env, "onboarding-history", get_onboarding_context())
    render(jinja2_env, "problematic-hardware", get_index_context())

    render(jinja2_env, "credits", get_credits_context("testnet"),
           target="credits-testnet")

    render(jinja2_env, "credits", get_credits_context("mainnet"),
           target="credits-mainnet")


if __name__ == "__main__":
    generate_static()
