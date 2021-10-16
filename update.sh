set -x;

python3 update_credits.py;
python3 update_onboarding.py;
python3 update_states.py;
python3 update_clusters.py;
python3 update_validators_testnet.py;
python3 update_signups.py;
python3 generate_static.py;

set +x;
