import unittest
from decimal import Decimal
from threading import Thread
from simulator.core import Engine, request_for, run_suite

class CoreTests(unittest.TestCase):
    def test_scenarios(self):
        suite=run_suite()
        self.assertEqual(suite['total'],16)
        self.assertEqual(suite['passed'],suite['total'])

    def test_state_machine(self):
        e=Engine()
        self.assertEqual(e.authorize(request_for()),'APPROVED')
        self.assertEqual(e.submit('TX-001'),'SUBMITTED')
        self.assertEqual(e.uncertain('TX-001'),'PENDING_RECONCILIATION')
        self.assertEqual(e.settle('TX-001','CONFIRMED'),'CONFIRMED')
        self.assertEqual(e.reserved,Decimal('30'))
        self.assertEqual(e.settle('TX-001','FAILED'),'INVALID_TRANSITION')

    def test_expired_mandate(self):
        e=Engine()
        self.assertEqual(e.authorize(request_for(quote_expiry=250),now=200),'REJECT_EXPIRED')

    def test_unauthorized_rail(self):
        e=Engine()
        self.assertEqual(e.authorize(request_for(rail='unlisted')),'REJECT_RAIL')

    def test_nonfinite_amount(self):
        e=Engine()
        self.assertEqual(e.authorize(request_for(amount='NaN')),'REJECT_FORMAT')

    def test_concurrent_budget(self):
        e=Engine()
        answers=[]
        def worker(i): answers.append(e.authorize(request_for(f'T{i}',amount='50')))
        threads=[Thread(target=worker,args=(i,)) for i in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(answers.count('APPROVED'),1)
        self.assertEqual(answers.count('REJECT_BUDGET'),7)

if __name__=='__main__': unittest.main()
