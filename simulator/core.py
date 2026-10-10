"""Rail-neutral synthetic payment simulation. No real money or integrations."""
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from threading import RLock
from datetime import datetime, timezone
import hashlib
import json

RAILS = ('card', 'bank', 'stablecoin', 'channel')

@dataclass(frozen=True)
class Mandate:
    principal: str = 'research-user'
    payee: str = 'approved-api'
    asset: str = 'USD'
    max_single: str = '50.00'
    total_limit: str = '80.00'
    expires_at: int = 200
    rails: tuple = ('card','bank','stablecoin','channel')

class Engine:
    """Stateful deterministic reference control, not secure transaction software."""
    def __init__(self, mandate=None):
        self.mandate = mandate or Mandate()
        self.records = {}
        self.reserved = Decimal('0')
        self.events = []
        self.lock = RLock()

    def _event(self, txn, action, result, detail=''):
        entry = {'step': len(self.events)+1, 'transaction':txn, 'action':action, 'result':result, 'detail':detail}
        self.events.append(entry)
        return result

    def authorize(self, request, now=100):
        with self.lock:
            txn = str(request.get('txn','')).strip()
            if not txn: return self._event('', 'policy', 'REJECT_ID')
            try:
                amount = Decimal(str(request.get('amount','')))
                max_single = Decimal(self.mandate.max_single)
                total = Decimal(self.mandate.total_limit)
                now = int(now)
                quote_expiry = int(request.get('quote_expiry',150))
                if not amount.is_finite(): raise InvalidOperation
            except (ValueError, TypeError, InvalidOperation):
                return self._event(txn,'policy','REJECT_FORMAT')
            normalized = {'txn': txn, 'principal':str(request.get('principal','')),
                          'payee':str(request.get('payee','')),'asset':str(request.get('asset','')),
                          'rail':str(request.get('rail','')),'amount':format(amount,'f'),
                          'quote_expiry':quote_expiry,'terms_hash':str(request.get('terms_hash',''))}
            if txn in self.records:
                old = self.records[txn]
                return self._event(txn,'replay', old['status'] if normalized == old['request'] else 'REJECT_ID_COLLISION')
            m = self.mandate
            checks = [
                (now >= m.expires_at or now >= quote_expiry,'REJECT_EXPIRED'),
                (normalized['principal'] != m.principal,'REJECT_PRINCIPAL'),
                (normalized['payee'] != m.payee,'REJECT_PAYEE'),
                (normalized['asset'] != m.asset,'REJECT_ASSET'),
                (normalized['rail'] not in m.rails,'REJECT_RAIL'),
                (not normalized['terms_hash'],'REJECT_TERMS'),
                (amount <= 0 or amount > max_single,'REJECT_AMOUNT'),
                (self.reserved + amount > total,'REJECT_BUDGET'),
            ]
            for condition, result in checks:
                if condition: return self._event(txn,'policy',result)
            self.reserved += amount
            self.records[txn] = {'request':normalized,'status':'APPROVED','amount':amount}
            return self._event(txn,'policy','APPROVED','Funds reserved in simulated budget')

    def submit(self, txn):
        with self.lock:
            record = self.records.get(txn)
            if not record: return self._event(txn,'submit','UNKNOWN')
            if record['status'] != 'APPROVED': return self._event(txn,'submit','INVALID_TRANSITION')
            record['status']='SUBMITTED'
            return self._event(txn,'submit','SUBMITTED','Synthetic rail dispatch')

    def uncertain(self, txn):
        with self.lock:
            record=self.records.get(txn)
            if not record or record['status']!='SUBMITTED': return self._event(txn,'reconcile','INVALID_TRANSITION')
            record['status']='PENDING_RECONCILIATION'
            return self._event(txn,'reconcile','PENDING_RECONCILIATION','Budget retained until outcome known')

    def settle(self, txn, outcome):
        with self.lock:
            record=self.records.get(txn)
            if not record or record['status'] not in ('SUBMITTED','PENDING_RECONCILIATION'):
                return self._event(txn,'settle','INVALID_TRANSITION')
            if outcome not in ('CONFIRMED','FAILED'):
                return self._event(txn,'settle','INVALID_OUTCOME')
            record['status']=outcome
            if outcome=='FAILED': self.reserved-=record['amount']
            return self._event(txn,'settle',outcome,'Simulated outcome; no provider contacted')

    def snapshot(self):
        return {'mandate':asdict(self.mandate),'reserved':str(self.reserved),
                'available':str(Decimal(self.mandate.total_limit)-self.reserved),
                'records':{k:{'status':v['status'],'request':v['request']} for k,v in self.records.items()},
                'events':list(self.events),'simulation_only':True}

def request_for(txn='TX-001', **kwargs):
    request={'txn':txn,'principal':'research-user','payee':'approved-api','asset':'USD',
             'amount':'30.00','rail':'card','quote_expiry':150,'terms_hash':'demo-terms-sha256-placeholder'}
    request.update(kwargs)
    return request

SCENARIOS = [
 {'id':'approved-card','title':'Approved card purchase','expected':'APPROVED','request':request_for()},
 {'id':'approved-bank','title':'Approved bank purchase','expected':'APPROVED','request':request_for(rail='bank')},
 {'id':'approved-stablecoin','title':'Approved stablecoin purchase','expected':'APPROVED','request':request_for(rail='stablecoin')},
 {'id':'approved-channel','title':'Approved channel purchase','expected':'APPROVED','request':request_for(rail='channel')},
 {'id':'wrong-payee','title':'Payee substitution','expected':'REJECT_PAYEE','request':request_for(payee='untrusted-merchant')},
 {'id':'over-limit','title':'Above single-payment limit','expected':'REJECT_AMOUNT','request':request_for(amount='60')},
 {'id':'expired-quote','title':'Expired quote','expected':'REJECT_EXPIRED','request':request_for(quote_expiry=90)},
 {'id':'missing-terms','title':'Missing terms binding','expected':'REJECT_TERMS','request':request_for(terms_hash='')},
 {'id':'wrong-principal','title':'Wrong principal','expected':'REJECT_PRINCIPAL','request':request_for(principal='other-user')},
 {'id':'wrong-asset','title':'Wrong asset','expected':'REJECT_ASSET','request':request_for(asset='EUR')},
 {'id':'invalid-amount','title':'Zero-value request','expected':'REJECT_AMOUNT','request':request_for(amount='0')},
]

def run_scenario(case):
    engine=Engine()
    result=engine.authorize(case['request'],case.get('now',100))
    return {'id':case['id'],'title':case['title'],'expected':case['expected'],
            'observed':result,'passed':result==case['expected'],'snapshot':engine.snapshot()}

def run_suite():
    results=[run_scenario(case) for case in SCENARIOS]
    e=Engine(); r1=e.authorize(request_for('B1',amount='50'));r2=e.authorize(request_for('B2',amount='40'))
    results.append({'id':'aggregate-budget','title':'Aggregate mandate budget','expected':'REJECT_BUDGET', 'observed':r2,'passed':r1=='APPROVED' and r2=='REJECT_BUDGET','snapshot':e.snapshot()})
    e=Engine();q=request_for();e.authorize(q);again=e.authorize(q)
    results.append({'id':'idempotency','title':'Identical repeated request','expected':'APPROVED (one reservation)','observed':f'{again} ({e.reserved} reserved)','passed':again=='APPROVED' and e.reserved==Decimal('30'),'snapshot':e.snapshot()})
    e=Engine();e.authorize(request_for());observed=e.authorize(request_for(amount='31'))
    results.append({'id':'collision','title':'Modified request with same ID','expected':'REJECT_ID_COLLISION','observed':observed,'passed':observed=='REJECT_ID_COLLISION','snapshot':e.snapshot()})
    e=Engine();e.authorize(request_for());e.submit('TX-001');observed=e.uncertain('TX-001')
    results.append({'id':'uncertain-outcome','title':'Unknown provider outcome holds budget','expected':'PENDING_RECONCILIATION','observed':observed,'passed':observed=='PENDING_RECONCILIATION' and e.reserved==Decimal('30'),'snapshot':e.snapshot()})
    e=Engine();e.authorize(request_for());e.submit('TX-001');observed=e.settle('TX-001','FAILED')
    results.append({'id':'failed-releases','title':'Confirmed failure releases budget','expected':'FAILED (zero reservation)','observed':f'{observed} ({e.reserved} reserved)','passed':observed=='FAILED' and e.reserved==0,'snapshot':e.snapshot()})
    return {'model':'synthetic-policy-v1','results':results,'passed':sum(x['passed'] for x in results),'total':len(results), 'limitations':'Synthetic logical tests only; no cryptographic validation, real providers, or financial settlement.'}
