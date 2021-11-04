# coding: utf-8
import os

RPC_TESTNET = "https://api.testnet.solana.com"
RPC_MAINNET = "https://api.mainnet-beta.solana.com"

SFDP_URL = "&".join((
    "https://kyc-api.vercel.app/api/validators/list?limit=100",
    "order_by=onboarding_number",
    "order=asc",
    "search_term=",
    "offset=%d"
))

CACHE_JINJA2_DIR = "/tmp/solanatools.xyz_jinja2"
TESTNET_FAUCET_ADDR = "HdgXzrgbt8VqqiFBnrAtAgajhQK9pYYjeGZgPtyX7ubg"

SOL_BINARY = "/root/.local/share/solana/install/active_release/bin/solana"
if not os.path.exists(SOL_BINARY):
    SOL_BINARY = "solana"

SOL_FAUCET_AMOUNT = 100
