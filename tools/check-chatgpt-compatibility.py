#!/usr/bin/env python3
"""Check both manual ChatGPT installation routes and exact kit provenance."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import zipfile
from docx import Document

ROOT=Path(__file__).resolve().parents[1]

def check():
    spec=importlib.util.spec_from_file_location('chatgpt_build',ROOT/'tools/build-chatgpt.py')
    builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    expected=builder.files()
    sources=builder.doctrine()
    with zipfile.ZipFile(ROOT/'career-engine-chatgpt.zip') as kit:
        actual={name:kit.read(name) for name in kit.namelist()}
        if len(actual)!=len(kit.namelist()) or actual!=expected:
            raise ValueError('ChatGPT kit is stale, incomplete, or has unexpected files; rebuild both packages')
    manifest=json.loads(actual['manifest.json'])
    if manifest['installation_routes']!=['custom-gpt','project']:
        raise ValueError('Both ChatGPT installation routes are required')
    for path,info in manifest['source_index'].items():
        section=re.search(r'^=== SOURCE: '+re.escape(path)+r' ===\n(.*?)\n=== END SOURCE ===$',actual[info['knowledge_file']].decode(),re.M|re.S)
        if not section or section.group(1)!=sources[path].rstrip():
            raise ValueError('Missing or truncated doctrine: '+path)
        if hashlib.sha256(sources[path].encode()).hexdigest()!=info['sha256']:
            raise ValueError('Stale source hash: '+path)
    for name,sha in manifest['file_sha256'].items():
        if hashlib.sha256(actual[name]).hexdigest()!=sha:
            raise ValueError('Stale kit hash: '+name)
    for name in ('detailed-cv','brief-cv','cover-letter'):
        Document(io.BytesIO(actual['templates/'+name+'.docx']))
    schema=json.loads(actual['actions/notion-openapi.json'])
    def check_objects(value):
        if isinstance(value,dict):
            if value.get('type')=='object' and not isinstance(value.get('properties'),dict):
                raise ValueError('Actions object schemas must explicitly declare properties')
            for child in value.values():
                check_objects(child)
        elif isinstance(value,list):
            for child in value:
                check_objects(child)
    check_objects(schema)
    operation_ids=[op['operationId'] for path in schema['paths'].values() for verb,op in path.items() if verb in ('get','post','patch')]
    if len(operation_ids)!=len(set(operation_ids)) or not {'queryDataSource','createTrackerPage','updateTrackerPage','appendPageBlocks'}.issubset(operation_ids):
        raise ValueError('Notion schema lacks unique required operations')
    print('ChatGPT offline compatibility passed: both routes,',len(manifest['source_index']),'source sections, templates, instructions, hashes. Live UI/tools: NOT RUN.')

if __name__=='__main__':
    check()
