import json, subprocess, sys, datetime, time, os
OUT = os.path.dirname(os.path.abspath(__file__))
Q = '''query($q:String!,$cursor:String){ search(query:$q,type:ISSUE,first:100,after:$cursor){ issueCount pageInfo{hasNextPage endCursor}
 nodes{ ... on PullRequest { number mergedAt authorAssociation author{ login __typename } } } } }'''
def gql(q, cursor=None):
    args = ['gh','api','graphql','-f','query='+Q,'-f','q='+q]
    if cursor: args += ['-f','cursor='+cursor]
    for attempt in range(5):
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0: return json.loads(r.stdout)['data']['search']
        print('retry', q, r.stderr[:200], file=sys.stderr); time.sleep(20*(attempt+1))
    raise SystemExit('failed '+q)
def fetch_slice(repo, a, b):
    q = f'repo:{repo} is:pr is:merged merged:{a}..{b}'
    rows=[]; cursor=None; count=None
    while True:
        s = gql(q, cursor); count = s['issueCount']
        if count >= 1000: return None, count
        rows += s['nodes']
        if not s['pageInfo']['hasNextPage']: break
        cursor = s['pageInfo']['endCursor']
    return rows, count
repo = sys.argv[1]
start = datetime.date(2025,11,1); end = datetime.date(2026,10,31)
allrows=[]; log=[]
d = start
while d <= end:
    e = min(d+datetime.timedelta(days=6), end)
    rows, count = fetch_slice(repo, d.isoformat(), e.isoformat())
    if rows is None:  # split daily
        dd = d
        while dd <= e:
            r2, c2 = fetch_slice(repo, dd.isoformat(), dd.isoformat())
            assert r2 is not None, (repo, dd, c2)
            log.append((dd.isoformat(), dd.isoformat(), c2, len(r2))); allrows += r2; dd += datetime.timedelta(days=1)
    else:
        log.append((d.isoformat(), e.isoformat(), count, len(rows))); allrows += rows
    d = e + datetime.timedelta(days=1)
json.dump({'rows':allrows,'log':log}, open(os.path.join(OUT, repo.replace('/','_')+'.json'),'w'))
print(repo, len(allrows), 'slices', len(log), 'mismatch', [l for l in log if l[2]!=l[3]])
