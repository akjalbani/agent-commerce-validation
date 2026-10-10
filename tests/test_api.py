import unittest
from app import app

class ApiTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_health(self): self.assertFalse(self.client.get('/api/health').json['real_payments'])
    def test_suite(self):
        r=self.client.get('/api/suite'); self.assertEqual(r.status_code,200);self.assertEqual(r.json['passed'],16)
    def test_custom(self):
        payload={'request':{'txn':'X','principal':'research-user','payee':'bad','asset':'USD','amount':'10','rail':'card','quote_expiry':150,'terms_hash':'x'}}
        self.assertEqual(self.client.post('/api/simulate',json=payload).json['observed'],'REJECT_PAYEE')
if __name__=='__main__':unittest.main()
