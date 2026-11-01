import json, collections, csv, re
REPOS=['dotnet_roslyn','dotnet_runtime','dotnet_sdk']
prof=json.load(open('profiles.json'))
EM=json.load(open('emails.json'))
MB=json.load(open('mergedby.json'))
data={r:json.load(open(r+'.json')) for r in REPOS}
AUTOMATION={'dotnet-bot','dotnet-maestro','github-actions','dependabot','dotnet-maestro-bot','dotnet-policy-service','msftbot','dotnet-issue-labeler','dotnet-release-bot','dotnet-oneloc-localization','csigs','vs-mobiletools-engineering-service2'}
COPILOT={'copilot-swe-agent','Copilot','copilot'}
# org membership signal from authorAssociation across all three repos (all are dotnet org repos)
member=collections.defaultdict(set)
for r in REPOS:
    for x in data[r]['rows']: member[x['author']['login']].add(x['authorAssociation'])
MSRE=re.compile(r'microsoft|msft|@dotnet\b|\.net team', re.I)
EXRE=re.compile(r'\b(ex|former|formerly|previously|prev|past)\b[^.]{0,25}(microsoft|msft)(?! mvp)', re.I)
def classify(login, typ):
    if typ!='User' or login.endswith('[bot]'):
        return ('COPILOT AGENT' if login in COPILOT else 'BOT'), 'type '+typ, ''
    if login in COPILOT: return 'COPILOT AGENT','login',''
    if login in AUTOMATION or re.search(r'(^|-)bot$', login): return 'BOT','automation account',''
    p=prof.get(login,{})
    comp=p.get('company') or ''; bio=p.get('bio') or ''
    txt=comp+' '+bio
    rules=[]
    if MSRE.search(comp): rules.append('company: '+comp.strip())
    elif MSRE.search(bio) and not EXRE.search(bio): rules.append('bio mentions Microsoft')
    if p.get('ms_public')=='204': rules.append('public member of microsoft org')
    mse=[e for e in EM.get(login,[]) if e.endswith('@microsoft.com')]
    if mse: rules.append('commit email @microsoft.com'+(' (v- vendor address)' if any(e.startswith('v-') for e in mse) else ''))
    if re.search(r'msft', login, re.I) and not mse: rules.append('login contains MSFT')
    assoc=member[login]
    if assoc & {'MEMBER','OWNER'}: rules.append('dotnet org MEMBER')
    unc=[]
    if EXRE.search(txt): unc.append('ex-Microsoft in profile')
    if 'dotnet org MEMBER' in rules and len(rules)==1:
        unc.append('dotnet MEMBER only, company: '+(comp.strip() or 'blank'))
    if rules: return 'MICROSOFT STAFF', '; '.join(rules), '; '.join(unc)
    if not comp.strip() and not bio.strip(): unc.append('blank profile')
    if ALL[login]>=10 and not comp.strip(): unc.append('high volume ('+str(ALL[login])+' merges in 3 repos), no stated employer')
    if 'COLLABORATOR' in assoc: unc.append('repo COLLABORATOR')
    mb=MB.get(login,{})
    if mb.get(login,0)>0: unc.append('WRITE ACCESS: self-merged %d of %d own PRs'%(mb[login],sum(mb.values())))
    TOT[login]=TOT.get(login,0)
    return 'OUTSIDE HUMAN', 'no Microsoft signal (company: '+(comp.strip() or 'blank')+')', '; '.join(unc)
TOT={}
ALL=collections.Counter(x['author']['login'] for r in REPOS for x in data[r]['rows'])
out={}; csvrows=[]
for r in REPOS:
    rows=data[r]['rows']; per=collections.Counter(); auth=collections.Counter(); ev={}; month=collections.Counter(); bots=collections.Counter()
    for x in rows:
        lg=x['author']['login']; b,rule,unc=classify(lg,x['author']['__typename'])
        per[b]+=1; ev[lg]=(b,rule,unc)
        if b=='OUTSIDE HUMAN': auth[lg]+=1
        if b=='COPILOT AGENT': month[x['mergedAt'][:7]]+=1
        if b=='BOT': bots[lg]+=1
        csvrows.append([r.replace('_','/'),x['number'],lg,x['author']['__typename'],x['authorAssociation'],x['mergedAt'],b=='COPILOT AGENT',b,rule,unc])
    staffauth=len({l for l,(b,_,_) in ev.items() if b=='MICROSOFT STAFF'})
    out[r]=dict(total=len(rows),buckets=dict(per),bots=dict(bots),outside=auth.most_common(),ev={l:ev[l] for l in auth},
                wa=sum(c for l,c in auth.items() if 'WRITE ACCESS' in ev[l][2]),wa_people=[l for l in auth if 'WRITE ACCESS' in ev[l][2]],ones=sum(1 for v in auth.values() if v==1),month=dict(sorted(month.items())),staff_authors=staffauth,
                staff_uncertain=sorted([(l,ev[l][2]) for l in ev if ev[l][0]=='MICROSOFT STAFF' and ev[l][2]]),
                slices=data[r]['log'])
json.dump(out,open('summary.json','w'),indent=1)
with open('../data/merged-prs.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['repo','pr_number','author_login','author_type','author_association','merged_at','is_copilot_agent','bucket','rule_matched','uncertain'])
    w.writerows(csvrows)
for r in REPOS:
    o=out[r]; t=o['total']
    print(r,t,{k:(v,round(100*v/t,1)) for k,v in o['buckets'].items()},'outsiders',len(o['outside']),'ones',o['ones'],'staff authors',o['staff_authors'])
    print(' top',o['outside'][:8]); print(' month',o['month']); print(' bots',o['bots'])
    print(' fuad',dict(o['outside']).get('lagudafuadtosin'))
    print(' outside uncertain',[(l,o['ev'][l][2]) for l,_ in o['outside'] if o['ev'][l][2]][:40])
    print(' staff uncertain',len(o['staff_uncertain']))
