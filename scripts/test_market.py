import json,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class MarketTests(unittest.TestCase):
 def test_supplied_market(self):
  s=json.loads((root/'data/snapshots/2026-09-08.json').read_text(encoding='utf8'))
  rows=s['marketGeography'];self.assertEqual(len(rows),497);self.assertEqual(len({r['name'] for r in rows}),497)
  self.assertEqual(sum(r['industry'] for r in rows),24592)
  self.assertEqual(sum(r['potential'] for r in rows),69709)
  self.assertEqual(sum(r['rule']=='EAD' for r in rows),391)
  for r in rows:self.assertEqual(r['rule'],'EAD' if r['potential']<=100 else 'Presencial')
  self.assertTrue(any(r['potential']==100 and r['rule']=='EAD' for r in rows))
  self.assertEqual(s['slices']['all']['market']['caged'],21880)
  self.assertEqual(sum(r['caged'] for r in rows)-21880,s['marketAudit']['difference'])
  self.assertEqual(s['marketAudit']['difference'],3)
  self.assertEqual(s['slices']['all']['market']['referenceMode'],'latest_available')
  self.assertEqual(s['marketSources']['mteCompetence'],'2026-07')
if __name__=='__main__':unittest.main()
