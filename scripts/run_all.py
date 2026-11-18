"""Collect and classify everything again from GitHub, then compare with the archived data.

Needs Python 3.10+ and the GitHub CLI (gh) signed in. Takes about 15 minutes.
    python scripts/run_all.py
Writes data/merged-prs-rerun.csv. The archived data/merged-prs.csv is never touched.
"""
import csv, collections, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
PY = sys.executable
RERUN = os.path.join(HERE, '..', 'data', 'merged-prs-rerun.csv')
ARCHIVE = os.path.join(HERE, '..', 'data', 'merged-prs.csv')
env = dict(os.environ, OUT_CSV=RERUN)


def step(title, *args):
    print(f'\n== {title}', flush=True)
    subprocess.run([PY, *args], check=True, env=env)


for f in ('emails.json', 'mergedby.json'):  # a clean run starts without the step 3 and 4 results
    if os.path.exists(f):
        os.remove(f)
for repo in ('dotnet/roslyn', 'dotnet/runtime', 'dotnet/sdk'):
    step(f'1. merged pull requests, {repo}', 'fetch.py', repo)
step('2. public profiles and organization membership', 'profiles.py')
step('first classification (needed by steps 3 and 4)', 'classify.py')
step('3. commit emails of authors with no profile signal', 'emails.py')
step('4. who merged each contributor pull request', 'mergedby.py')
step('5. final classification', 'classify.py')
step('tables from this run', 'check_tables.py', RERUN)

new = {(r['repo'], r['pr_number']): r['group'] for r in csv.DictReader(open(RERUN, encoding='utf-8'))}
old = {(r['repo'], r['pr_number']): r['group'] for r in csv.DictReader(open(ARCHIVE, encoding='utf-8'))}
changed = collections.Counter((old[k], new[k]) for k in old.keys() & new.keys() if old[k] != new[k])
print(f'\n== compared with the archive: {len(old.keys() & new.keys()):,} pull requests in both, '
      f'{len(new.keys() - old.keys())} only in this run, {len(old.keys() - new.keys())} only in the archive')
print('group changes:', dict(changed) if changed else 'none')
print('Profiles and memberships change over time, so small differences are expected.')
