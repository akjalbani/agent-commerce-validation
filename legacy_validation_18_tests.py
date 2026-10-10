"""Synthetic validation of selected rail-neutral agent-payment policy rules.
No live provider integration, cryptography, or real settlement is performed.
Run: python3 agent_payment_validation.py
"""
from dataclasses import dataclass
from decimal import Decimal
from threading import Lock, Thread
import unittest

@dataclass(frozen=True)
class Mandate:
    principal: str
    payee: str
    currency: str
    max_single: Decimal
    total_limit: Decimal
    expiry: int
    allowed_rails: frozenset

@dataclass(frozen=True)
class Request:
    txn: str
    principal: str
    payee: str
    currency: str
    amount: Decimal
    rail: str
    quote_expiry: int
    terms_hash: str

class PolicyModel:
    def __init__(self, mandate):
        self.mandate = mandate
        self.lock = Lock()
        self.reserved = Decimal('0')
        self.records = {}

    def authorize(self, request, now):
        with self.lock:
            if request.txn in self.records:
                previous = self.records[request.txn]
                if previous['request'] != request:
                    return 'REJECT_ID_COLLISION'
                return previous['status']
            m = self.mandate
            if now >= m.expiry or now >= request.quote_expiry:
                return 'REJECT_EXPIRED'
            if request.principal != m.principal:
                return 'REJECT_PRINCIPAL'
            if request.payee != m.payee:
                return 'REJECT_PAYEE'
            if request.currency != m.currency:
                return 'REJECT_ASSET'
            if request.rail not in m.allowed_rails:
                return 'REJECT_RAIL'
            if not request.terms_hash:
                return 'REJECT_TERMS'
            if request.amount <= 0 or request.amount > m.max_single:
                return 'REJECT_AMOUNT'
            if self.reserved + request.amount > m.total_limit:
                return 'REJECT_BUDGET'
            self.reserved += request.amount
            self.records[request.txn] = {'request': request, 'status': 'APPROVED'}
            return 'APPROVED'

    def mark_submitted(self, txn):
        with self.lock:
            if txn not in self.records:
                return 'UNKNOWN'
            if self.records[txn]['status'] != 'APPROVED':
                return self.records[txn]['status']
            self.records[txn]['status'] = 'SUBMITTED'
            return 'SUBMITTED'

    def mark_unknown(self, txn):
        with self.lock:
            if txn not in self.records:
                return 'UNKNOWN'
            if self.records[txn]['status'] != 'SUBMITTED':
                return self.records[txn]['status']
            self.records[txn]['status'] = 'PENDING_RECONCILIATION'
            return 'PENDING_RECONCILIATION'

    def finalize(self, txn, provider_status):
        with self.lock:
            if txn not in self.records or self.records[txn]['status'] not in ('SUBMITTED', 'PENDING_RECONCILIATION'):
                return 'INVALID_TRANSITION'
            if provider_status not in ('CONFIRMED', 'FAILED'):
                return 'INVALID_PROVIDER_STATUS'
            self.records[txn]['status'] = provider_status
            if provider_status == 'FAILED':
                self.reserved -= self.records[txn]['request'].amount
            return provider_status

class Validation(unittest.TestCase):
    def setUp(self):
        self.m = Mandate('owner','merchant','USD',Decimal('50'),Decimal('80'),200,frozenset({'card','stablecoin'}))
        self.model = PolicyModel(self.m)
        self.q = Request('T1','owner','merchant','USD',Decimal('30'),'card',150,'hash-of-terms')

    def test_01_valid_card(self): self.assertEqual(self.model.authorize(self.q, 100),'APPROVED')
    def test_02_valid_stablecoin(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'rail':'stablecoin'}),100),'APPROVED')
    def test_03_payee_substitution(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'payee':'attacker'}),100),'REJECT_PAYEE')
    def test_04_exceeded_single_limit(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'amount':Decimal('60')}),100),'REJECT_AMOUNT')
    def test_05_unapproved_rail(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'rail':'bank'}),100),'REJECT_RAIL')
    def test_06_expired_quote(self): self.assertEqual(self.model.authorize(self.q,150),'REJECT_EXPIRED')
    def test_07_expired_mandate(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'quote_expiry':250}),200),'REJECT_EXPIRED')
    def test_08_missing_quote_binding(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'terms_hash':''}),100),'REJECT_TERMS')
    def test_09_replay_same_id(self):
        self.assertEqual(self.model.authorize(self.q,100),'APPROVED')
        self.assertEqual(self.model.authorize(self.q,101),'APPROVED')
        self.assertEqual(self.model.reserved, Decimal('30'))
    def test_10_id_collision_modified_payment(self):
        self.model.authorize(self.q,100)
        self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'amount':Decimal('40')}),101),'REJECT_ID_COLLISION')
    def test_11_insufficient_aggregate_budget(self):
        self.model.authorize(self.q,100)
        self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'txn':'T2', 'amount':Decimal('51')}),100),'REJECT_AMOUNT')
        self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'txn':'T2', 'amount':Decimal('50')}),100),'APPROVED')
        self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'txn':'T3', 'amount':Decimal('1')}),100),'REJECT_BUDGET')
    def test_12_unknown_provider_result_does_not_release_funds(self):
        self.model.authorize(self.q,100)
        self.assertEqual(self.model.mark_submitted('T1'),'SUBMITTED')
        self.assertEqual(self.model.mark_unknown('T1'),'PENDING_RECONCILIATION')
        self.assertEqual(self.model.authorize(self.q,101),'PENDING_RECONCILIATION')
        self.assertEqual(self.model.reserved,Decimal('30'))
    def test_13_confirmed_payment_retains_used_allowance(self):
        self.model.authorize(self.q,100)
        self.model.mark_submitted('T1')
        self.assertEqual(self.model.finalize('T1','CONFIRMED'),'CONFIRMED')
        self.assertEqual(self.model.reserved,Decimal('30'))
    def test_14_provider_failure_releases_reservation(self):
        self.model.authorize(self.q,100)
        self.model.mark_submitted('T1')
        self.assertEqual(self.model.finalize('T1','FAILED'),'FAILED')
        self.assertEqual(self.model.reserved,Decimal('0'))
    def test_15_parallel_requests_cannot_overspend(self):
        results=[]
        def task(i): results.append(self.model.authorize(Request(**{**self.q.__dict__, 'txn':f'T{i}', 'amount':Decimal('50')}),100))
        workers=[Thread(target=task,args=(i,)) for i in range(8)]
        for w in workers: w.start()
        for w in workers: w.join()
        self.assertEqual(results.count('APPROVED'),1)
        self.assertEqual(results.count('REJECT_BUDGET'),7)
        self.assertEqual(self.model.reserved,Decimal('50'))
    def test_16_principal_substitution(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'principal':'other'}),100),'REJECT_PRINCIPAL')
    def test_17_asset_substitution(self): self.assertEqual(self.model.authorize(Request(**{**self.q.__dict__, 'currency':'EUR'}),100),'REJECT_ASSET')
    def test_18_invalid_status_transition(self):
        self.model.authorize(self.q,100)
        self.assertEqual(self.model.finalize('T1','CONFIRMED'),'INVALID_TRANSITION')

if __name__=='__main__': unittest.main(verbosity=2)
