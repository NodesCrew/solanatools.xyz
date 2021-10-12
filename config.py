# coding: utf-8

RPC_TESTNET = "https://api.testnet.solana.com"
RPC_MAINNET = "https://api.mainnet-beta.solana.com"

SFDP_URL = "&".join((
    "https://kyc-api.vercel.app/api/validators/list?limit=100",
    "order_by=onboarding_number",
    "order=asc",
    "search_term=",
    "offset=%d"
))

