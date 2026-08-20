# For beginners: This file (apps/audit/tasks.py) contains part of the
# application logic. It defines background jobs run by django-q2's worker
# process (started with `python manage.py qcluster`), not by the web
# request/response cycle. This keeps blockchain confirmation latency (a
# few seconds on Amoy) off the critical path of approving a claim or
# issuing a policy.

"""
=================================================
AUDIT TASKS — async blockchain anchoring
=================================================

HOW TO QUEUE A TASK:
    from apps.audit.tasks import queue_policy_anchor, queue_claim_anchor
    queue_policy_anchor(policy.policy_id)
    queue_claim_anchor(claim.claim_id)

REQUIREMENTS:
    - 'django_q' must be enabled in INSTALLED_APPS (config/settings/base.py)
    - migrations run: `python manage.py migrate django_q`
    - a worker process running: `python manage.py qcluster`
      (run this in a separate terminal/process from `runserver`, and as
      its own systemd unit / supervisor process in production)

WHY SEPARATE queue_* / anchor_* FUNCTIONS:
    django-q2 needs an importable dotted path string ('apps.audit.tasks.anchor_claim')
    to hand to worker processes, so the "do the work" function and the
    "schedule the work" function are kept separate and both easily testable.
"""

import logging

from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def queue_policy_anchor(policy_id):
    # For beginners: This function 'queue_policy_anchor' performs one reusable
    # task. Other parts of the app call it to avoid duplicating logic.
    """Schedule a policy to be anchored on-chain. Fire-and-forget."""
    async_task('apps.audit.tasks.anchor_policy', policy_id)


def queue_claim_anchor(claim_id):
    # For beginners: This function 'queue_claim_anchor' performs one reusable
    # task. Other parts of the app call it to avoid duplicating logic.
    """Schedule a claim payout to be anchored on-chain. Fire-and-forget."""
    async_task('apps.audit.tasks.anchor_claim', claim_id)


def anchor_policy(policy_id):
    """Worker entrypoint: anchor a single Policy and save the result."""
    from apps.plans.models import Policy
    from apps.audit.services.blockchain_anchor import BlockchainAnchorService
    from apps.audit.models import AuditLog

    try:
        policy = Policy.objects.select_related('plan').get(policy_id=policy_id)
    except Policy.DoesNotExist:
        logger.error('anchor_policy: Policy %s not found', policy_id)
        return

    result = BlockchainAnchorService().anchor_policy(policy)

    policy.blockchain_hash = result['tx_hash']
    policy.save(update_fields=['blockchain_hash'])

    AuditLog.objects.create(
        event_type='policy_anchored',
        target_model='Policy',
        target_id=policy.policy_id,
        metadata={
            'tx_hash': result['tx_hash'],
            'network': result['network'],
            'block_number': result['block_number'],
            'simulated': result['simulated'],
        },
    )
    logger.info('Policy %s anchored: %s (%s)', policy_id, result['tx_hash'], result['network'])


def anchor_claim(claim_id):
    """Worker entrypoint: anchor a single Claim payout and save the result."""
    from apps.claims.models import Claim
    from apps.audit.services.blockchain_anchor import BlockchainAnchorService
    from apps.audit.models import AuditLog

    try:
        claim = Claim.objects.get(claim_id=claim_id)
    except Claim.DoesNotExist:
        logger.error('anchor_claim: Claim %s not found', claim_id)
        return

    result = BlockchainAnchorService().anchor_claim_payout(claim)

    claim.blockchain_hash = result['tx_hash']
    claim.blockchain_tx = result['tx_hash']
    claim.save(update_fields=['blockchain_hash', 'blockchain_tx'])

    AuditLog.objects.create(
        event_type='claim_anchored',
        target_model='Claim',
        target_id=claim.claim_id,
        metadata={
            'tx_hash': result['tx_hash'],
            'network': result['network'],
            'block_number': result['block_number'],
            'simulated': result['simulated'],
        },
    )
    logger.info('Claim %s anchored: %s (%s)', claim_id, result['tx_hash'], result['network'])
