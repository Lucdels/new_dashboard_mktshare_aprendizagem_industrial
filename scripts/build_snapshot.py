"""Read a source workbook locally and publish aggregate snapshots only. Python 3 + lxml."""
import argparse,collections,datetime as dt,hashlib,json,re,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
COLS={'CODFILIAL':'A','NOMEFANTASIA':'B','RA':'C','CPF':'X','CURSO':'AA','MODALIDADE':'AO','CNPJ_EMPRESA':'BR','DATA_INI_CONTRATOAPR':'BU','DATA_FIM_CONTRATOAPR':'BV','STATUS_CURSO':'BX','CODTURMA':'AY','ID_MATRIZ_APLICADA':'CC'}
def read_source(path):
 from lxml import etree as E
 z=zipfile.ZipFile(path);ss=[]
 for _,e in E.iterparse(z.open('xl/sharedStrings.xml'),events=('end',),tag=NS+'si'):
  ss.append(''.join(e.itertext()));e.clear()
  while e.getprevious() is not None:del e.getparent()[0]
 wb=E.fromstring(z.read('xl/workbook.xml'));sheet=wb.find(NS+'sheets')[0].get('name')
 selected=[];count=0;indices=None
 for _,e in E.iterparse(z.open('xl/worksheets/sheet1.xml'),events=('end',),tag=NS+'row'):
  r={}
  for c in e:
   col=re.sub(r'\d','',c.get('r',''))
   if indices is not None and col not in indices:continue
   v=c.find(NS+'v')
   if v is not None and v.text is not None:r[col]=ss[int(v.text)] if c.get('t')=='s' else v.text
  if indices is None:
   headers={str(v).strip():k for k,v in r.items()}
   missing=set(COLS)-headers.keys()
   if missing:raise ValueError('Colunas obrigatórias ausentes: '+', '.join(sorted(missing)))
   indices={headers[name]:canonical for name,canonical in COLS.items()}
  else:
   count+=1;r={indices[k]:v for k,v in r.items()}
   if 'aprendizagem industrial' in r.get('AO','').lower():selected.append(r)
  e.clear()
  while e.getprevious() is not None:del e.getparent()[0]
 return selected,count,sheet

def excel_date(v):
 if not v:return None
 try:return (dt.datetime(1899,12,30)+dt.timedelta(days=float(v))).date()
 except (ValueError,OverflowError):
  try:return dt.date.fromisoformat(v[:10])
  except ValueError:return None

def clean_cnpj(v):
 if not v or not str(v).strip():return ''
 value=re.sub(r'\D','',str(v))
 return value.zfill(14) if len(value)<=14 else value

def valid_cnpj(s):
 if len(s)!=14 or not s.isdigit() or len(set(s))==1:return False
 def digit(base,weights):
  rem=sum(int(a)*b for a,b in zip(base,weights))%11
  return str(0 if rem<2 else 11-rem)
 return s[12]==digit(s[:12],[5,4,3,2,9,8,7,6,5,4,3,2]) and s[13]==digit(s[:13],[6,5,4,3,2,9,8,7,6,5,4,3,2])

def prepare(rows,asof,mapping):
 result=[]
 for i,r in enumerate(rows):
  if r.get('BX','').strip().lower()!='matriculado':continue
  cpf=re.sub(r'\D','',r.get('X',''))
  person=('cpf:'+cpf) if cpf and len(set(cpf))>1 else ('ra:'+r['C'].strip()) if r.get('C') else ('missing:'+str(i))
  cnpj=clean_cnpj(r.get('BR'));start=excel_date(r.get('BU'));end=excel_date(r.get('BV'))
  region=mapping.get('regions',{}).get(r.get('A'),[])
  region=region[0] if len(region)==1 else 'Sem mapeamento regional'
  unit=r.get('B','Unidade não informada').strip();course=r.get('AA','Curso não informado').strip()
  if not cnpj or set(cnpj)=={'0'}:status='missing'
  elif not valid_cnpj(cnpj):status='invalid_cnpj'
  elif not start or not end or start>end:status='invalid_dates'
  elif start>asof:status='future'
  elif end<asof:status='expired'
  else:status='active'
  result.append({'person':person,'cnpj':cnpj,'start':start,'end':end,'status':status,'region':region,'unit':unit,'unitCode':r.get('A',''),'course':course,'modality':'technical' if 'técnica' in r.get('AO','').lower() else 'basic','key':(person,cnpj,str(start),str(end))})
 return result

def aggregate(rows,asof):
 people={r['person'] for r in rows};active={r['key']:r for r in rows if r['status']=='active'};actpeople={r['person'] for r in active.values()};missing={r['person'] for r in rows if r['status']=='missing'}
 companies=collections.Counter(r['cnpj'] for r in active.values());shares=sorted(companies.values(),reverse=True);future={r['key'] for r in rows if r['status']=='future'};expired={r['key'] for r in rows if r['status']=='expired'}
 metrics={'students':len(people),'records':len(rows),'activeContracts':len(active),'activeStudents':len(actpeople),'companies':len(companies),'noContractStudents':len(missing),'exclusiveNoContractStudents':len(missing-actpeople),'overlapStudents':len(missing&actpeople),'futureContracts':len(future),'expiredContracts':len(expired),'invalidCnpjRows':sum(r['status']=='invalid_cnpj' for r in rows),'invalidDateRows':sum(r['status']=='invalid_dates' for r in rows),'expiring90':sum(0<=(r['end']-asof).days<=90 for r in active.values()),'top1Share':shares[0]/len(active)*100 if active else None,'top5Share':sum(shares[:5])/len(active)*100 if active else None}
 months=dict(sorted(collections.Counter(r['end'].isoformat()[:7] for r in active.values()).items()))
 return metrics,months

def make_node(rows,asof,label,kind,path,market=None):
 metrics,months=aggregate(rows,asof);node={'id':hashlib.sha256('/'.join(path).encode()).hexdigest()[:12],'label':label,'type':kind,'metrics':metrics,'months':months,'children':[]}
 if market:node['market']=market
 nextfield={'state':'region','region':'unit','unit':'course'}.get(kind)
 if nextfield:
  groups=collections.defaultdict(list)
  for r in rows:groups[r[nextfield]].append(r)
  for name,rs in sorted(groups.items()):node['children'].append(make_node(rs,asof,name,{'region':'region','unit':'unit','course':'course'}[nextfield],path+[name]))
 return node

def attach_market(snapshot,market):
 if market.get('competence')!=snapshot['date'][:7] and market.get('referenceMode')!='latest_available':raise ValueError('Competência diferente exige referenceMode latest_available explícito.')
 if market.get('competence','9999')>snapshot['date'][:7]:raise ValueError('Base de mercado posterior à fotografia.')
 if not market.get('source'):raise ValueError('Informe a fonte da base de mercado.')
 root=snapshot['slices']['all'];regions=market.get('regions',{})
 unknown=set(regions)-{r['label'] for r in root['children']}
 if unknown:raise ValueError('Regiões do mercado sem correspondência: '+', '.join(sorted(unknown)))
 for node in [root,*root['children']]:
  values=market.get('state') if node is root else regions.get(node['label'])
  if not values:continue
  for key in ['caged','mte']:
   if values.get(key) is not None and (not isinstance(values[key],(int,float)) or isinstance(values[key],bool) or values[key]<0):raise ValueError('Denominador inválido: '+key)
  node['market']={**values,'competence':market['competence'],'source':market['source'],'referenceMode':market.get('referenceMode','same_month')}
 if 'municipalities' in market:snapshot['marketGeography']=market['municipalities']
 if 'audit' in market:snapshot['marketAudit']=market['audit']
 if 'sources' in market:snapshot['marketSources']=market['sources']

def build(rows,source_rows,source,sheet,date,mapping,market=None):
 asof=dt.date.fromisoformat(date);prepared=prepare(rows,asof,mapping)
 slices={name:make_node(prepared if name=='all' else [r for r in prepared if r['modality']==name],asof,'Rio Grande do Sul','state',['RS']) for name in ['all','basic','technical']}
 m=slices['all']['metrics'];result={'schemaVersion':1,'date':date,'source':source,'sheet':sheet,'sourceRows':source_rows,'learningRows':len(rows),'rulesVersion':'1.0.0','slices':slices,'quality':{'extraPersonRows':m['records']-m['students'],'invalidCnpjRows':m['invalidCnpjRows'],'invalidDateRows':m['invalidDateRows'],'futureContracts':m['futureContracts'],'expiredContracts':m['expiredContracts'],'unmappedRows':sum(r['region']=='Sem mapeamento regional' for r in prepared),'missingPersonRows':sum(r['person'].startswith('missing:') for r in prepared),'duplicateActiveRows':sum(r['status']=='active' for r in prepared)-m['activeContracts']}}
 if market:attach_market(result,market)
 return result

def save(snapshot,replace=False):
 path=ROOT/'data'/'snapshots'/f"{snapshot['date']}.json";path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and not replace:raise ValueError('Data já existe. Use --replace somente para corrigir essa fotografia explicitamente.')
 path.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 allsnaps=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(path.parent.glob('*.json'))]
 (ROOT/'dist'/'data.js').write_text('window.DASHBOARD_DATA = '+json.dumps(allsnaps,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';\n',encoding='utf-8')
 return path

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('workbook',type=Path);ap.add_argument('--date',required=True);ap.add_argument('--market',type=Path);ap.add_argument('--replace',action='store_true');args=ap.parse_args()
 mapping=json.loads((ROOT/'data'/'region-map.json').read_text(encoding='utf-8'));market=json.loads(args.market.read_text(encoding='utf-8')) if args.market else None
 rows,count,sheet=read_source(args.workbook);result=build(rows,count,args.workbook.name,sheet,args.date,mapping,market);print(save(result,args.replace));print(json.dumps(result['slices']['all']['metrics'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
