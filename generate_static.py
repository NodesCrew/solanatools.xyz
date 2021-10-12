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
    #
    # with open("templates/%s.html" % template_name) as f:
    #     template = jinja2.Template(f.read())

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


def get_onboarding_context():
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
                nodes[tn_pubkey]["positions"][epoch_no] = node_position

    epoches = list(sorted(epoches))

    nodes_clean = dict()
    for tn_pubkey, node in nodes.items():
        if any(node["positions"].values()):
            nodes_clean[tn_pubkey] = node

    return dict(nodes=nodes_clean,
                epoches=epoches,
                datetime=datetime.datetime.utcnow())


def generate_static():
    jinja2_loader = jinja2.FileSystemLoader("templates")
    jinja2_env = jinja2.Environment(loader=jinja2_loader)

    render(jinja2_env, "index", dict())
    render(jinja2_env, "onboarding-history", get_onboarding_context())


if __name__ == "__main__":
    generate_static()