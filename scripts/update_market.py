"""Attach a compatible market denominator to an existing dated snapshot."""
import argparse,json
from pathlib import Path
from build_snapshot import ROOT,attach_market,save
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--date',required=True);ap.add_argument('--market',type=Path,required=True);args=ap.parse_args()
path=ROOT/'data'/'snapshots'/f'{args.date}.json'
snapshot=json.loads(path.read_text(encoding='utf-8'));attach_market(snapshot,json.loads(args.market.read_text(encoding='utf-8')));save(snapshot,replace=True);print('Denominadores atualizados para '+args.date)
