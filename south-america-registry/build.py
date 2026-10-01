#!/usr/bin/env python3
"""Build and verify the source-preserving South America GeoNames pack."""
import argparse, csv, gzip, io, json, re, zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import geonames_core as core
from materialize import materialize_country

ROOT = Path(__file__).resolve().parent
SCOPE = {'AR','BO','BV','BR','CL','CO','EC','FK','GF','GS','GY','PE','PY','SR','UY','VE'}
PENDING = {'AR','PY'}
PUBLISHED_SCOPE = SCOPE - PENDING
ALIAS_RAW = 'alternate_name_id geonameid language value preferred short colloquial historic from_period to_period'.split()
ALIAS_FIELDS = ['id','entity_id','value_type'] + ALIAS_RAW
SPECIAL_CODES = {'post':'postal_code','iata':'airport_code','icao':'airport_code','faac':'airport_code','abbr':'abbreviation','link':'link','wkdt':'wikidata_id'}

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr': self.row=[]
        elif tag=='td' and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        elif tag=='tr' and self.row is not None:
            self.rows.append(self.row); self.row=None

def countries(inputs):
    parser=TableParser(); parser.feed((inputs/'m49.html').read_text())
    source_rows=[r[:12] for r in parser.rows if len(r)>=12 and r[6]=='005' and r[7]=='South America']
    assert len(source_rows)==16 and {r[10] for r in source_rows}==SCOPE
    info={}
    for line in (inputs/'countryInfo.txt').read_text().splitlines():
        if not line or line.startswith('#'): continue
        r=line.split('\t'); info[r[0]]=r
    records=[]
    for r in source_rows:
        cc=r[10]; ci=info[cc]
        records.append(dict(country=cc,id='country:'+cc,name_en=r[8],m49=r[9],alpha3=r[11],region='South America',region_m49='005',geonames_id=ci[16],geonames_continent=ci[8],source_country_languages=ci[15].split(',') if ci[15] else [],status='source_country_or_area'))
    return sorted(records,key=lambda c:c['country']),source_rows

def aliases(path, cc, ids):
    values=[]; total=0
    with zipfile.ZipFile(path) as z:
        with z.open(cc+'.txt') as f:
            for line in io.TextIOWrapper(f,encoding='utf-8'):
                parts=line.rstrip('\r\n').split('\t'); assert len(parts)==10
                total+=1; raw=dict(zip(ALIAS_RAW,parts))
                if raw['geonameid'] not in ids: continue
                assert re.fullmatch('[1-9][0-9]*',raw['alternate_name_id']) and raw['value']
                for flag in ['preferred','short','colloquial','historic']: assert raw[flag] in ('','1')
                typ=SPECIAL_CODES.get(raw['language'],'language_name' if raw['language'] else 'untyped_name')
                values.append(dict(id='gn-alt:'+raw['alternate_name_id'],entity_id='gn:'+raw['geonameid'],value_type=typ,**raw))
    values.sort(key=lambda r:int(r['alternate_name_id']))
    assert len(values)==len({r['id'] for r in values})
    return values,total

def snapshot(path,url,retrieved):
    return dict(url=url,retrieved_on=retrieved,sha256=core.sha(path.read_bytes()),bytes=path.stat().st_size)

def build(inputs, output, retrieved, selected):
    if selected and not set(selected).issubset(PUBLISHED_SCOPE):
        raise ValueError('Requested countries are outside this 14-area publication; AR/PY are pending')
    scope,source_rows=countries(inputs)
    output.mkdir(parents=True,exist_ok=True)
    core.write_json(output/'scope.json',dict(schema_version=1,source_url=core.M49_URL,retrieved_on=retrieved,scope_m49='005',m49_country_area_count=16,source_rows=source_rows,countries=[c for c in scope if c['country'] in PUBLISHED_SCOPE],published_country_area_count=14,pending_countries=[dict(country='AR',name_en='Argentina',status='publication_pending'),dict(country='PY',name_en='Paraguay',status='publication_pending')],related_separate_layers=[dict(country='BR',layer='official-registry/countries/BR',note='Existing official IBGE municipality layer; not duplicated or reconciled with this pack.')] ))
    for c in scope:
        cc=c['country']
        if cc not in PUBLISHED_SCOPE or (selected and cc not in selected): continue
        path=inputs/(cc+'.zip'); raw=list(core.source_rows(path,cc))
        rows=core.build_rows([r for r in raw if r['feature_class'] in ('A','P')],cc)
        sm=snapshot(path,core.SOURCE_URL+cc+'.zip',retrieved)
        sm.update(source_rows=len(raw),retained_rows=len(rows),discarded_feature_classes=dict(Counter(r['feature_class'] for r in raw if r['feature_class'] not in ('A','P'))))
        core.write_country(rows,cc,output,sm,c)
        d=output/'countries'/cc; meta=json.loads((d/'metadata.json').read_text())
        ap=inputs/(cc+'-alternatenames.zip'); values,alias_total=aliases(ap,cc,{r['geonameid'] for r in rows})
        payload=core.csv_bytes(values,ALIAS_FIELDS); encoded=core.compressed(payload); (d/'alternate-values.csv.gz').write_bytes(encoded)
        meta['alternate_values_file']=dict(filename='alternate-values.csv.gz',rows=len(values),bytes=len(encoded),sha256=core.sha(encoded),uncompressed_sha256=core.sha(payload))
        meta['alternate_values_source']=snapshot(ap,core.SOURCE_URL+'alternatenames/'+cc+'.zip',retrieved)
        meta['alternate_values_source'].update(source_rows=alias_total,retained_rows=len(values),source_columns=10)
        langs={v['entity_id'] for v in values if v['value_type']=='language_name'}
        english={v['entity_id'] for v in values if v['language']=='en' and v['historic']!='1' and not v['to_period']}
        country_langs={l.split('-')[0] for l in c['source_country_languages']}
        native={v['entity_id'] for v in values if v['language'].split('-')[0] in country_langs and v['historic']!='1' and not v['to_period']}
        meta['label_coverage']=dict(language_tagged_name_entities=len(langs),current_english_name_entities=len(english),current_country_language_name_entities=len(native),missing_english_name_entities=len(rows)-len(english),missing_country_language_name_entities=len(rows)-len(native),native_label_rule='Exact source language tag matched against countryInfo language list; no language is inferred from primary name, ASCII, spelling or script. Country-language match is not proof of each place\'s indigenous language.')
        meta['postal_coverage']=dict(source_postal_value_rows=sum(v['value_type']=='postal_code' for v in values),postal_validation=False,postal_deliverability_verified=False,note='Only source post-tag values, if any; not joined by place name and not delivery validation.')
        core.write_json(d/'metadata.json',meta)
        print(json.dumps(dict(**meta['counts'],alternate_values=len(values),**meta['label_coverage']),ensure_ascii=False),flush=True)

def verify(output):
    scope=json.loads((output/'scope.json').read_text()); reports=[]; allids=set(); aliasids=set()
    assert {c['country'] for c in scope['countries']} == PUBLISHED_SCOPE
    assert {p.name for p in (output/'countries').iterdir() if p.is_dir()} == PUBLISHED_SCOPE
    for c in scope['countries']:
        cc=c['country']; d=output/'countries'/cc
        assert d.is_dir(), ('missing published country',cc)
        materialize_country(output,cc)
        meta=json.loads((d/'metadata.json').read_text()); rows=list(core.read_csv(d/'entities.csv.gz')); by={r['id']:r for r in rows}
        assert len(by)==len(rows); assert not allids.intersection(by); allids.update(by)
        assert rows==core.build_rows([{k:r[k] for k in core.RAW} for r in rows],cc)
        fi=meta['files']['entities.csv.gz']; data=(d/'entities.csv.gz').read_bytes()
        assert len(rows)==fi['rows']==meta['source_file']['retained_rows']
        assert core.sha(data)==fi['sha256'] and core.sha(gzip.decompress(data))==fi['uncompressed_sha256']
        for r in rows:
            assert r['country_code']==cc
            pid=r['parent_id']; assert not pid or pid=='country:'+cc or pid in by
            seen={r['id']}; node=pid
            while node in by:
                assert node not in seen;seen.add(node);p=by[node]
                assert p['kind']=='admin_subdivision';node=p['parent_id']
            if pid in by:
                p=by[pid];assert core.code_key(r,int(p['admin_level']))==core.code_key(p,int(p['admin_level']))
                if r['admin_level']: assert int(p['admin_level'])==int(r['admin_level'])-1
            assert not r['state_id'] or (r['state_id'] in by and by[r['state_id']]['admin_level']=='1')
            for f in ['parent_candidates_json','state_candidates_json']: assert all(i in by for i in json.loads(r[f]))
        assert (d/'admin1.csv').read_bytes()==core.csv_bytes([r for r in rows if r['admin_level']=='1'])
        av=list(core.read_csv(d/'alternate-values.csv.gz')); fi=meta['alternate_values_file'];data=(d/'alternate-values.csv.gz').read_bytes()
        assert len(av)==fi['rows'] and core.sha(data)==fi['sha256'] and core.sha(gzip.decompress(data))==fi['uncompressed_sha256']
        for a in av:
            assert a['entity_id'] in by and a['id'] not in aliasids;aliasids.add(a['id'])
            assert a['id']=='gn-alt:'+a['alternate_name_id'] and a['entity_id']=='gn:'+a['geonameid']
        assert not {'address1','street','house_number'}.intersection(rows[0] if rows else {})
        reports.append(dict(country=cc,rows=len(rows),alternate_values=len(av),integrity='passed',derived_columns_replay='exact',**{k:v for k,v in meta['counts'].items() if k not in ('country','name_en','region')}))
    report=dict(status='passed',scope_countries=14,m49_country_area_count=16,pending_country_codes=['AR','PY'],prepared_countries=len(reports),rows=len(allids),alternate_values=len(aliasids),errors=0,no_address1=True,reports=reports,current_official_hierarchy_verified=False,full_municipality_coverage_verified=False)
    core.write_json(output/'verification.json',report)
    counts=[json.loads((output/'countries'/r['country']/'metadata.json').read_text())['counts'] for r in reports]
    if counts: (output/'coverage.csv').write_bytes(core.csv_bytes(counts,list(counts[0])))
    core.write_json(output/'manifest.json',dict(schema_version=1,source='GeoNames',data_license='CC-BY-4.0',scope_m49='005',m49_country_area_count=16,pack_country_area_count=len(reports),external_country_area_count=0,pending_country_codes=['AR','PY'],pending_country_area_count=2,complete_pack=False,complete_published_subset=len(reports)==14,complete_official_country_coverage=False,counts=report,countries=[dict(country=r['country'],metadata_sha256=core.sha((output/'countries'/r['country']/'metadata.json').read_bytes())) for r in reports]))
    print(json.dumps({k:v for k,v in report.items() if k!='reports'}));return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','verify']);p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path,default=ROOT);p.add_argument('--retrieved-on',default='2026-10-01');p.add_argument('--countries',nargs='+');a=p.parse_args()
    if a.command=='build':
        if a.inputs is None:p.error('--inputs required')
        build(a.inputs,a.output,a.retrieved_on,a.countries)
    else:verify(a.output)
if __name__=='__main__':main()
