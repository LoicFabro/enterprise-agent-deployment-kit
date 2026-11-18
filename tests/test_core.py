import json
import tempfile
import unittest
from pathlib import Path
from eadk.cli import scaffold, main
from eadk.core import EADKError, dependency_impact, findings, load, merge, plan
from eadk.providers import deploy

class EADKTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        scaffold(self.root)
    def tearDown(self):
        self.tmp.cleanup()
    def test_merge(self):
        self.assertEqual(merge({'a':{'x':1},'z':2},{'a':{'y':3}}), {'a':{'x':1,'y':3},'z':2})
    def test_valid_all_environments(self):
        for env in ('development','staging','production'):
            self.assertFalse([f for f in findings(load(self.root,'acme',env)) if f.level=='ERROR'])
    def test_dry_run_and_apply(self):
        d = load(self.root,'acme','staging')
        self.assertEqual(plan(d)['change'],'CREATE')
        deploy(d, False)
        self.assertEqual(plan(d)['change'],'CREATE')
        deploy(d, True)
        self.assertEqual(plan(d)['change'],'NO_CHANGE')
        conf = self.root/'tenants/acme/staging.json'
        conf.write_text('{"agent":{"name":"Updated Agent"}}')
        self.assertEqual(plan(load(self.root,'acme','staging'))['change'],'UPDATE')
    def test_production_approval(self):
        p = self.root/'tenants/acme/production.json'
        p.write_text('{"governance":{"require_approval":false}}')
        self.assertIn('APPROVAL', [f.code for f in findings(load(self.root,'acme','production'))])
    def test_authentication_required(self):
        p = self.root/'tenants/acme/staging.json'
        p.write_text('{"security":{"require_authentication":false}}')
        self.assertIn('SECURITY_REQUIRE_AUTHENTICATION', [f.code for f in findings(load(self.root,'acme','staging'))])
    def test_embedded_secret(self):
        p = self.root/'tenants/acme/staging.json'
        p.write_text('{"integrations":{"api_key":"plainsecret"}}')
        self.assertIn('EMBEDDED_SECRET', [f.code for f in findings(load(self.root,'acme','staging'))])
    def test_impact(self):
        refs = dependency_impact(self.root,'create_ticket')
        self.assertEqual(len(refs),3)
        self.assertEqual({x['risk'] for x in refs},{'HIGH','MEDIUM'})
    def test_traversal_prevented(self):
        with self.assertRaises(EADKError): load(self.root,'../other','staging')
    def test_provider_native_project_rejected(self):
        p = self.root/'tenants/acme/staging.json'
        p.write_text('{"provider":"elevenlabs", "native_project":"../../other"}')
        self.assertIn('NATIVE_PROJECT',[f.code for f in findings(load(self.root,'acme','staging'))])
    def test_cli_validate(self):
        self.assertEqual(main(['--project',str(self.root),'validate']),0)
    def test_cli_prod_guard(self):
        self.assertEqual(main(['--project',str(self.root),'deploy','--env','production','--apply']),2)

if __name__ == '__main__': unittest.main()
