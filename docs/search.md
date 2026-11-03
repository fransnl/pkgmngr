# Search

The search box filters the active tab by package name. The matcher lives in `tui/fuzzy.py`, and its syntax and scoring follow fzf.

## Syntax

Space-separated terms must all match.

| Term | Meaning |
| --- | --- |
| `abc` | Fuzzy: the characters appear in order, with anything in between |
| `'abc` | Exact substring |
| `^abc` | Name starts with `abc` |
| `abc$` | Name ends with `abc` |
| `!abc` | Name does not contain `abc` |

Matching is smart-case: a term is case-insensitive unless it contains an uppercase letter.

## Scoring

Each fuzzy term is matched with fzf's v1 algorithm. The first left-to-right subsequence match is found, then the matcher scans backwards from its end to find the tightest window. The matched positions are scored as follows:

- `+16` per matched character
- `+8` when a character starts a word (string start, or after one of `` -_./:@\``), and `+7` at camelCase or digit boundaries
- `+4` for a character that follows the previous match directly, when that is larger than its boundary bonus
- The first matched character's bonus is doubled
- Gaps cost `-3` for the first skipped character and `-1` for each additional one

Results are sorted by total score, then by shorter name, then alphabetically. With an empty query, packages are listed alphabetically. Matched characters are highlighted in the table.
