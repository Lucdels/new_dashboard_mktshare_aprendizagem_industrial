import datetime as dt,unittest
from build_snapshot import prepare,aggregate,build,attach_market

class SnapshotTests(unittest.TestCase):
 def setUp(self):self.day=dt.date(2026,9,8);self.mapping={'regions':{'1':['Região A'],'2':['Região B']}}
 def row(self,**changes):
  r={'A':'1','B':'Unidade A','C':'1','X':'12345678901','AA':'Curso','AO':'Aprendizagem Industrial básica','BR':'11.222.333/0001-81','BU':'2026-01-01','BV':'2026-12-31','BX':'Matriculado'};r.update(changes);return r
 def test_distinct_people_contracts_companies(self):
  rows=[self.row(),self.row(AA='Outro curso'),self.row(A='2',B='Unidade B')];p=prepare(rows,self.day,self.mapping);m,_=aggregate(p,self.day)
  self.assertEqual((m['records'],m['students'],m['activeContracts'],m['companies']),(3,1,1,1))
 def test_zero_company_and_overlap(self):
  rows=[self.row(),self.row(BR='',BU='',BV=''),self.row(C='2',X='98765432100',BR='0',BU='',BV='')];m,_=aggregate(prepare(rows,self.day,self.mapping),self.day)
  self.assertEqual(m['companies'],1);self.assertEqual(m['noContractStudents'],2);self.assertEqual(m['exclusiveNoContractStudents'],1)
 def test_temporal_boundaries(self):
  rows=[self.row(BU='2026-09-08',BV='2026-09-08'),self.row(C='2',X='98765432100',BU='2026-09-09'),self.row(C='3',X='12398745600',BV='2026-09-07')]
  m,_=aggregate(prepare(rows,self.day,self.mapping),self.day);self.assertEqual((m['activeContracts'],m['futureContracts'],m['expiredContracts']),(1,1,1))
 def test_invalid_data_excluded(self):
  rows=[self.row(BR='123'),self.row(BV=''),self.row(BU='2027-01-01',BV='2026-01-01')];m,_=aggregate(prepare(rows,self.day,self.mapping),self.day)
  self.assertEqual(m['activeContracts'],0);self.assertEqual(m['invalidCnpjRows'],1);self.assertEqual(m['invalidDateRows'],2)
 def test_matriculado_only_and_unknown_region(self):
  p=prepare([self.row(BX='Concluinte'),self.row(A='9')],self.day,self.mapping);self.assertEqual(len(p),1);self.assertEqual(p[0]['region'],'Sem mapeamento regional')
 def test_no_stale_denominator(self):
  s=build([self.row()],1,'test.xlsx','Sheet','2026-09-08',self.mapping)
  self.assertNotIn('market',s['slices']['all'])
  with self.assertRaises(ValueError):attach_market(s,{'competence':'2026-06','source':'test','state':{'caged':100}})
  attach_market(s,{'competence':'2026-09','source':'test','state':{'caged':100,'mte':120},'regions':{'Região A':{'caged':100}}})
  self.assertEqual(s['slices']['all']['market']['caged'],100);self.assertNotIn('market',s['slices']['basic'])
  attach_market(s,{'competence':'2026-07','referenceMode':'latest_available','source':'test','state':{'caged':100}})
  self.assertEqual(s['slices']['all']['market']['competence'],'2026-07')
  with self.assertRaises(ValueError):attach_market(s,{'competence':'2026-10','referenceMode':'latest_available','source':'test','state':{'caged':100}})
 def test_months_reconcile_and_no_identifiers(self):
  s=build([self.row()],1,'test.xlsx','Sheet','2026-09-08',self.mapping);n=s['slices']['all'];self.assertEqual(sum(n['months'].values()),n['metrics']['activeContracts'])
  import json
  output=json.dumps(s);self.assertNotIn('12345678901',output);self.assertNotIn('11222333000181',output)

if __name__=='__main__':unittest.main()
