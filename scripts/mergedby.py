import json, subprocess, collections
# Step 4: for every pull request by an outside contributor, read who merged it.
# An author who merged some of their own pull requests has write access.
# Needs summary.json from a first classify.py run. Writes mergedby.json: {author: {merger: count}}.
s = json.load(open('summary.json'))
REPOS = ['dotnet_roslyn', 'dotnet_runtime', 'dotnet_sdk']
data = {r: json.load(open(r + '.json'))['rows'] for r in REPOS}
cands = set(l for r in REPOS for l, _ in s[r]['outside'])
targets = [(r, x['number'], x['author']['login']) for r in REPOS for x in data[r] if x['author']['login'] in cands]
merged_by = collections.defaultdict(collections.Counter)
for i in range(0, len(targets), 50):
    chunk = targets[i:i + 50]
    parts = []
    for j, (r, n, _) in enumerate(chunk):
        o, nm = r.split('_')
        parts.append(f'p{j}: repository(owner:"{o}",name:"{nm}"){{pullRequest(number:{n}){{mergedBy{{login}}}}}}')
    q = 'query{' + ' '.join(parts) + '}'
    res = subprocess.run(['gh', 'api', 'graphql', '-f', 'query=' + q], capture_output=True, text=True, encoding='utf-8', errors='replace')
    d = json.loads(res.stdout)['data']
    for j, (r, n, lg) in enumerate(chunk):
        who = ((d[f'p{j}']['pullRequest'] or {}).get('mergedBy') or {}).get('login', '')
        merged_by[lg][who] += 1
json.dump({k: dict(v) for k, v in merged_by.items()}, open('mergedby.json', 'w'), indent=1)
print(len(cands), 'authors,', len(targets), 'pull requests, self-merged by:',
      sorted(k for k, v in merged_by.items() if v.get(k, 0) > 0))
