#!/usr/bin/env python3
"""Restore exact large-file bytes from bounded local parts, without network access."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

ROOT=Path(__file__).resolve().parent

def safe_path(root,name):
    rel=PurePosixPath(name)
    if rel.is_absolute() or not name or '\\' in name or any(x in ('','.', '..') for x in name.split('/')):
        raise ValueError('unsafe package path')
    root=root.resolve()
    current=root
    for part in rel.parts:
        current=current/part
        if current.is_symlink():raise ValueError('symlink package path')
    return root.joinpath(*rel.parts)

def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def restore(root,entry):
    target=safe_path(root,entry['path'])
    if not isinstance(entry['bytes'],int) or not 0<=entry['bytes']<=256*1024*1024:
        raise ValueError('unexpected reconstructed size')
    if target.exists():
        if not target.is_file() or target.stat().st_size!=entry['bytes'] or sha_file(target)!=entry['sha256']:
            raise ValueError('existing output differs; refusing to overwrite')
        return target
    parts=[];total=0
    for part in entry['parts']:
        path=safe_path(root,part['path'])
        if not path.is_file() or path.stat().st_size!=part['bytes'] or sha_file(path)!=part['sha256']:
            raise ValueError('part size/checksum mismatch')
        if not 0<part['bytes']<=512*1024:raise ValueError('unexpected part size')
        total+=part['bytes'];parts.append(path)
    if total!=entry['bytes']:raise ValueError('part aggregate size mismatch')
    target.parent.mkdir(parents=True,exist_ok=True)
    # Re-check the parent after creation, before writing.
    safe_path(root,entry['path'])
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.'+target.name+'.',delete=False) as f:
            tmp=Path(f.name)
            for path in parts:
                with path.open('rb') as source:
                    for b in iter(lambda:source.read(1024*1024),b''):f.write(b)
        if tmp.stat().st_size!=entry['bytes'] or sha_file(tmp)!=entry['sha256']:
            raise ValueError('reconstructed checksum mismatch')
        # Never overwrite an independently existing file.
        os.link(tmp,target)
        tmp.unlink();tmp=None
        return target
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)

def manifest(root):
    path=root/'split_manifest.json'
    if not path.exists():return []
    entries=json.loads(path.read_text())['files']
    if len({e['path'] for e in entries})!=len(entries):raise ValueError('duplicate file path')
    return entries

def materialize_country(root,country):
    if not re.fullmatch('[A-Z]{2}',country):raise ValueError('invalid country')
    out=[]
    for entry in manifest(root):
        if entry.get('country')==country:out.append(restore(root,entry))
    return out

def ensure_file(path,root=ROOT):
    if path.exists():return path
    try:relative=path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:return path
    for entry in manifest(root):
        if entry['path']==relative:return restore(root,entry)
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--country',required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    for path in materialize_country(a.root,a.country):print(path.relative_to(a.root))
