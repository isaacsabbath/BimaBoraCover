# For beginners: This file (apps/audit/services/blockchain_anchor.py) contains
# part of the application logic. Read this file from top to bottom to see what
# data it handles and which functions/classes other files can call.

"""
=================================================
BLOCKCHAIN ANCHOR SERVICE — Polygon Amoy Registry
=================================================

Anchors proof of policy issuance and claim payouts on the BimaRegistry
smart contract deployed to the Polygon Amoy testnet.

WHY THIS EXISTS:
    Postgres remains the single source of truth for business state
    (policies, claims, payments). This service does NOT replace that.
    Its only job is to write an immutable, timestamped proof-of-existence
    record on-chain so a policy or claim payout can be independently
    verified later, even if the database were ever tampered with.

DESIGN, PORTED FROM BimaOS (CodeWithEugene/BimaOS):
    BimaOS wraps a single owner-controlled registry contract
    (BimaRegistry.sol) with a "real transaction, mock fallback" pattern:
    if RPC/wallet/contract env vars aren't configured, or the chain call
    fails for any reason (RPC down, out of test funds, network hiccup),
    it falls back to a locally-generated pseudo tx hash instead of
    raising an error. That keeps claim approval and policy issuance from
    ever blocking on blockchain infrastructure being unavailable.

    This port keeps that same fallback behavior. If you are defending
    this project and want failures to be loud instead of silent, see the
    `strict` flag below.

WHO CALLS THIS:
    - apps.audit.tasks.anchor_policy / anchor_claim (run async via
      django-q2, NOT called synchronously from request/response cycle)

CONFIGURATION (see .env.example):
    POLYGON_AMOY_RPC_URL       — JSON-RPC endpoint for Amoy testnet
    BIMA_BORA_REGISTRY_ADDRESS — deployed BimaRegistry contract address
    OPERATOR_PRIVATE_KEY       — private key of the wallet that owns the
                                  contract (the only account allowed to
                                  call registerPolicy/registerClaimPayout)
"""

import json
import logging
import secrets

from decouple import config
from django.conf import settings

logger = logging.getLogger(__name__)

REGISTRY_ABI_PATH = settings.BASE_DIR / 'apps' / 'audit' / 'contracts' / 'bima_registry_abi.json'

# KES has 2 decimal places; we scale to "cents" before sending on-chain so we
# never need floats/wei-fraction math in Solidity.
KES_SCALE = 100


class BlockchainAnchorService:
    """
    Wraps the BimaRegistry contract on Polygon Amoy.

    Set `strict=True` to raise instead of silently falling back to a mock
    tx hash when the chain call fails — useful in a defense/demo where you
    want to know immediately if the RPC or wallet isn't working, rather
    than finding out later that everything was "simulation" mode.
    """

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.rpc_url = config('POLYGON_AMOY_RPC_URL', default='')
        self.registry_address = config('BIMA_BORA_REGISTRY_ADDRESS', default='')
        self.private_key = config('OPERATOR_PRIVATE_KEY', default='')

        self._configured = bool(self.rpc_url and self.registry_address and self.private_key)
        self.w3 = None
        self.contract = None
        self.account = None

        if self._configured:
            self._init_web3()

    def _init_web3(self):
        # For beginners: This function '_init_web3' performs one reusable task.
        # Other parts of the app call it to avoid duplicating logic.
        from web3 import Web3
        try:
            from web3.middleware import geth_poa_middleware
        except ImportError:  # web3.py >=7 renamed/relocated this middleware
            geth_poa_middleware = None

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if geth_poa_middleware is not None:
            # Amoy is a Proof-of-Authority style chain; without this
            # middleware, web3.py chokes on the "extraData" field length
            # in block headers.
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        with open(REGISTRY_ABI_PATH) as f:
            abi = json.load(f)

        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(self.registry_address), abi=abi)
        self.account = self.w3.eth.account.from_key(self.private_key)

    @staticmethod
    def _id_to_bytes32(entity_id) -> bytes:
        from web3 import Web3
        return Web3.keccak(text=str(entity_id))

    def anchor_policy(self, policy) -> dict:
        """Anchor a Policy. Expects the apps.plans.models.Policy fields:
        policy_id, premium_paid, coverage_amount, plan_id (FK to InsurancePlan)."""
        premium = policy.premium_paid
        coverage = policy.coverage_amount
        policy_type = getattr(policy.plan_id, 'plan_type', 'Standard Cover')

        return self._send(
            fn_name='registerPolicy',
            build_args=lambda user_addr: [
                self._id_to_bytes32(policy.policy_id),
                user_addr,
                int(float(premium) * KES_SCALE),
                int(float(coverage) * KES_SCALE),
                str(policy_type),
            ],
            entity_label=f'policy:{policy.policy_id}',
        )

    def anchor_claim_payout(self, claim) -> dict:
        """Anchor a Claim payout. apps.claims.models.Claim has no direct FK
        to a Policy — only to InsurancePlan (plan_id) and User (user_id) —
        so we look up the user's matching Policy for the on-chain policy
        reference, falling back to the plan_id itself if none is found
        (e.g. claim submitted before a Policy row existed)."""
        from apps.plans.models import Policy

        payout = claim.claim_amount

        policy = Policy.objects.filter(user_id=claim.user_id, plan_id=claim.plan_id).first()
        policy_ref = policy.policy_id if policy else claim.plan_id_id

        return self._send(
            fn_name='registerClaimPayout',
            build_args=lambda user_addr: [
                self._id_to_bytes32(claim.claim_id),
                self._id_to_bytes32(policy_ref),
                user_addr,
                int(float(payout) * KES_SCALE),
                str(claim.status),
            ],
            entity_label=f'claim:{claim.claim_id}',
        )

    def verify_claim(self, claim_id) -> dict:
        """Read-only check against the chain. No gas cost, no queueing
        needed — safe to call synchronously from a view."""
        if not self._configured:
            return {'configured': False, 'exists': False, 'status': None, 'payout_amount': None}

        try:
            claim_id_bytes = self._id_to_bytes32(claim_id)
            exists, status, payout_amount = self.contract.functions.verifyClaim(claim_id_bytes).call()
            return {
                'configured': True,
                'exists': exists,
                'status': status,
                'payout_amount': payout_amount / KES_SCALE if exists else None,
            }
        except Exception:
            logger.exception('verify_claim failed for claim_id=%s', claim_id)
            return {'configured': True, 'exists': False, 'status': None, 'payout_amount': None, 'error': True}

    def _send(self, fn_name: str, build_args, entity_label: str) -> dict:
        if not self._configured:
            if self.strict:
                raise RuntimeError(
                    'BlockchainAnchorService is not configured: set POLYGON_AMOY_RPC_URL, '
                    'BIMA_BORA_REGISTRY_ADDRESS, and OPERATOR_PRIVATE_KEY.'
                )
            logger.warning('Blockchain anchor not configured, using simulation for %s', entity_label)
            return self._mock_result()

        try:
            user_addr = self.account.address
            args = build_args(user_addr)
            fn = getattr(self.contract.functions, fn_name)

            tx = fn(*args).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300_000,
                'gasPrice': self.w3.eth.gas_price,
            })
            signed = self.account.sign_transaction(tx)
            raw = getattr(signed, 'raw_transaction', None) or signed.rawTransaction
            tx_hash = self.w3.eth.send_raw_transaction(raw)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            logger.info('Anchored %s on Polygon Amoy: tx=%s block=%s', entity_label, tx_hash.hex(), receipt.blockNumber)

            return {
                'tx_hash': tx_hash.hex(),
                'block_number': receipt.blockNumber,
                'network': 'polygon_amoy',
                'simulated': False,
            }
        except Exception:
            logger.exception('Anchor failed for %s, falling back to simulation', entity_label)
            if self.strict:
                raise
            return self._mock_result()

    @staticmethod
    def _mock_result() -> dict:
        return {
            'tx_hash': '0x' + secrets.token_hex(32),
            'block_number': None,
            'network': 'simulation',
            'simulated': True,
        }
