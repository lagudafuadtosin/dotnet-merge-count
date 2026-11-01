# dotnet-merge-count

Who wrote the pull requests merged into three .NET repositories over one year, 1 November 2025 to 31 October 2026.

Repositories: dotnet/roslyn, dotnet/runtime, dotnet/sdk. 13,226 merged pull requests.

## Groups

Each merged pull request is in exactly one group, decided by its author.

- **bot**: automation accounts, mostly the dependency flow service that updates versions across repositories, plus GitHub Actions and similar accounts.
- **copilot**: GitHub's Copilot coding agent (copilot-swe-agent).
- **microsoft_staff**: a person whose public GitHub profile, public Microsoft organization membership or commit email says they work at Microsoft, or who is a member of the dotnet organization.
- **contributor**: everyone else.

## Results

| Repository | Merged pull requests | Microsoft staff | Bots | Copilot | Contributors |
|---|---|---|---|---|---|
| dotnet/roslyn | 2,783 | 1,683 (60.5%) | 651 (23.4%) | 167 (6.0%) | 282 (10.1%) |
| dotnet/runtime | 7,500 | 4,716 (62.9%) | 906 (12.1%) | 1,101 (14.7%) | 777 (10.4%) |
| dotnet/sdk | 2,943 | 1,404 (47.7%) | 1,291 (43.9%) | 201 (6.8%) | 47 (1.6%) |

Contributors who had a pull request merged, and how many had only one:

| Repository | Contributors with a merge | Only one merge | Share |
|---|---|---|---|
| dotnet/roslyn | 52 | 41 | 79% |
| dotnet/runtime | 183 | 108 | 59% |
| dotnet/sdk | 36 | 29 | 81% |

## Cases public data cannot settle

Two groups change the contributor count, so the result is given as a range.

1. Contributors with write access (they merged some of their own pull requests). Counted as contributors above. Moved to staff, the contributor counts become roslyn 85, runtime 606, sdk 47.
2. dotnet organization members with no Microsoft signal. Counted as staff above. Moved to contributors, the counts become roslyn 283, runtime 959, sdk 60.

| Repository | Copilot | Contributors, low | Contributors, high | Copilot to contributors |
|---|---|---|---|---|
| dotnet/roslyn | 167 | 85 | 283 | 0.59 to 1.96 |
| dotnet/runtime | 1,101 | 606 | 959 | 1.15 to 1.82 |
| dotnet/sdk | 201 | 47 | 60 | 3.35 to 4.28 |

Rows in either group are marked in the `uncertain` column of the data.

## Data

`data/merged-prs.csv`, one row per merged pull request:

- `repo`, `pr_number`, `author_login`, `author_type`, `author_association`, `merged_at`
- `group`: bot, copilot, microsoft_staff or contributor
- `rule_matched`: which public signal put the author in the group
- `uncertain`: why the group could be argued, if it could

No email addresses or profile text are included, only the kind of signal that matched.

## Method

1. `scripts/fetch.py <owner/repo>` lists merged pull requests with the GitHub GraphQL search API in weekly slices, split into days where a week reaches the 1,000 result cap. Every slice's reported count is checked against the rows returned.
2. `scripts/profiles.py` reads each human author's public profile (company, bio) and public membership of the microsoft and dotnet organizations.
3. `scripts/emails.py` reads commit author emails on up to 10 pull requests per author who had no profile signal, looking for @microsoft.com.
4. The merged-by login of each contributor pull request was read with a separate GraphQL query to find authors who merge their own work (`mergedby.json`, not included).
5. `scripts/classify.py` applies the rules and writes the CSV.

The scripts need the GitHub CLI (`gh`) signed in. They were run on 31 October 2026. Profiles and memberships change, so a later run may differ slightly.

## Author

Fuad Laguda. I am one of the contributors counted here: 6 merged pull requests in dotnet/roslyn and 5 in dotnet/runtime during the period.
