import json, subprocess, os, sys
users=set()
for r in ['dotnet_roslyn','dotnet_runtime','dotnet_sdk']:
    for x in json.load(open(r+'.json'))['rows']:
        if x['author']['__typename']=='User': users.add(x['author']['login'])
path='profiles.json'
prof=json.load(open(path)) if os.path.exists(path) else {}
def status(url):
    r=subprocess.run(['gh','api','-i',url],capture_output=True,text=True,encoding='utf-8',errors='replace')
    line=(r.stdout or '').splitlines()[:1]
    return line[0].split()[1] if line else 'ERR'
for i,u in enumerate(sorted(users)):
    if u in prof: continue
    r=subprocess.run(['gh','api','users/'+u],capture_output=True,text=True,encoding='utf-8',errors='replace')
    p=json.loads(r.stdout) if r.returncode==0 else {}
    prof[u]={'company':p.get('company'),'bio':p.get('bio'),'name':p.get('name'),'type':p.get('type'),
             'ms_public':status('orgs/microsoft/public_members/'+u),'dotnet_public':status('orgs/dotnet/public_members/'+u)}
    if i%50==0: json.dump(prof,open(path,'w')); print(i,len(users),file=sys.stderr)
json.dump(prof,open(path,'w')); print('users',len(users))
