import json, subprocess, collections
s=json.load(open('summary.json'))
REPOS=['dotnet_roslyn','dotnet_runtime','dotnet_sdk']
data={r:json.load(open(r+'.json'))['rows'] for r in REPOS}
cands=set(l for r in REPOS for l,_ in s[r]['outside'])
targets=[]  # (repo, number, login), up to 10 PRs per login per repo
for r in REPOS:
    per=collections.Counter()
    for x in data[r]:
        lg=x['author']['login']
        if lg in cands and per[lg]<10: per[lg]+=1; targets.append((r,x['number'],lg))
emails=collections.defaultdict(set)
for i in range(0,len(targets),25):
    chunk=targets[i:i+25]; parts=[]
    for j,(r,n,lg) in enumerate(chunk):
        o,nm=r.split('_')
        parts.append(f'p{j}: repository(owner:"{o}",name:"{nm}"){{pullRequest(number:{n}){{commits(first:30){{nodes{{commit{{author{{email user{{login}}}} committer{{email}}}}}}}}}}}}')
    q='query{'+' '.join(parts)+'}'
    res=subprocess.run(['gh','api','graphql','-f','query='+q],capture_output=True,text=True,encoding='utf-8',errors='replace')
    d=json.loads(res.stdout)['data']
    for j,(r,n,lg) in enumerate(chunk):
        for c in d[f'p{j}']['pullRequest']['commits']['nodes']:
            a=c['commit']['author']
            if (a.get('user') or {}).get('login')==lg:
                emails[lg].add(a['email'].lower())
json.dump({k:sorted(v) for k,v in emails.items()},open('emails.json','w'),indent=1)
ms={k:[e for e in v if 'microsoft.com' in e] for k,v in emails.items()}
print(len(cands), 'with ms email:', sorted(k for k,v in ms.items() if v))
