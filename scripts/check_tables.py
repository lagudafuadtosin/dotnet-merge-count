"""Rebuild every number in the article from data/merged-prs.csv.

No GitHub sign-in needed. Run from the repository root or the scripts folder:
    python scripts/check_tables.py            # print the tables
    python scripts/check_tables.py --verify   # also compare with the published numbers, exit 1 on any difference
    python scripts/check_tables.py path/to/other.csv   # check a CSV from your own run
"""
import csv, collections, os, sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
here = os.path.dirname(os.path.abspath(__file__))
path = args[0] if args else os.path.join(here, '..', 'data', 'merged-prs.csv')
rows = list(csv.DictReader(open(path, encoding='utf-8')))
REPOS = ['dotnet/roslyn', 'dotnet/runtime', 'dotnet/sdk']

got = {}
print(f'Table 1. Merged pull requests by group, 1 November 2025 to 31 October 2026 ({os.path.basename(path)})')
print(f"{'repository':16}{'merged':>8}{'staff':>16}{'bots':>16}{'copilot':>16}{'contributors':>16}")
for r in REPOS:
    rr = [x for x in rows if x['repo'] == r]
    n = len(rr)
    c = collections.Counter(x['group'] for x in rr)
    cell = lambda g: f"{c[g]:,} ({100 * c[g] / n:.1f}%)"
    print(f"{r:16}{n:>8,}{cell('microsoft_staff'):>16}{cell('bot'):>16}{cell('copilot'):>16}{cell('contributor'):>16}")
    got[r] = {'merged': n, **{g: c[g] for g in ('microsoft_staff', 'bot', 'copilot', 'contributor')}}

print('\nTable 2. Contributors who had a pull request merged, and how many had only one')
for r in REPOS:
    per = collections.Counter(x['author_login'] for x in rows if x['repo'] == r and x['group'] == 'contributor')
    ones = sum(1 for v in per.values() if v == 1)
    print(f"{r:16}{len(per):>6} contributors{ones:>6} with one merge  {100 * ones / len(per):.0f}%")
    got[r].update(people=len(per), ones=ones)

print('\nCases public data cannot settle (contributor count as a range)')
for r in REPOS:
    rr = [x for x in rows if x['repo'] == r]
    contrib = sum(1 for x in rr if x['group'] == 'contributor')
    low = contrib - sum(1 for x in rr if x['group'] == 'contributor' and 'write access' in x['uncertain'])
    high = contrib + sum(1 for x in rr if x['group'] == 'microsoft_staff' and 'dotnet org member, no Microsoft signal' in x['uncertain'])
    cop = got[r]['copilot']
    print(f"{r:16} contributors {low:,} to {high:,}   copilot to contributors {cop / high:.2f} to {cop / low:.2f}")
    got[r].update(low=low, high=high)

PUBLISHED = {
    'dotnet/roslyn': dict(merged=2783, microsoft_staff=1683, bot=651, copilot=167, contributor=282, people=52, ones=41, low=85, high=283),
    'dotnet/runtime': dict(merged=7500, microsoft_staff=4716, bot=906, copilot=1101, contributor=777, people=183, ones=108, low=606, high=959),
    'dotnet/sdk': dict(merged=2943, microsoft_staff=1404, bot=1291, copilot=201, contributor=47, people=36, ones=29, low=47, high=61),  # 61: corrected 18 Nov 2026 from 60, see README
}
if '--verify' in sys.argv:
    diffs = [(r, k, v, got[r][k]) for r in REPOS for k, v in PUBLISHED[r].items() if got[r][k] != v]
    print()
    if diffs:
        for r, k, want, have in diffs:
            print(f'DIFFERENT {r} {k}: published {want}, this CSV {have}')
        sys.exit(1)
    print('All published numbers reproduced exactly.')
