from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")

SCORE_MATCH = 16
GAP_START = -3
GAP_EXTENSION = -1
BONUS_BOUNDARY = 8
BONUS_CAMEL = 7
BONUS_CONSECUTIVE = 4
FIRST_CHAR_MULTIPLIER = 2
SEPARATORS = set(" -_./:@\\")


@dataclass(frozen=True)
class Term:
    text: str
    kind: str = "fuzzy"
    negate: bool = False

    @property
    def case_sensitive(self) -> bool:
        return self.text != self.text.lower()


@dataclass(frozen=True)
class Match:
    score: int
    positions: frozenset[int]


def parse_query(query: str) -> list[Term]:
    terms = []
    for token in query.split():
        negate = token.startswith("!")
        if negate:
            token = token[1:]
        kind = "exact" if negate else "fuzzy"
        if token.startswith("'"):
            kind, token = "exact", token[1:]
        elif token.startswith("^"):
            kind, token = "prefix", token[1:]
        elif token.endswith("$") and len(token) > 1:
            kind, token = "suffix", token[:-1]
        if token:
            terms.append(Term(token, kind, negate))
    return terms


def _bonus(text: str, index: int) -> int:
    if index == 0:
        return BONUS_BOUNDARY
    previous, current = text[index - 1], text[index]
    if previous in SEPARATORS:
        return BONUS_BOUNDARY
    if previous.islower() and current.isupper():
        return BONUS_CAMEL
    if current.isdigit() and not previous.isdigit():
        return BONUS_CAMEL
    return 0


def _score(text: str, positions: list[int]) -> int:
    score = 0
    previous = None
    for order, position in enumerate(positions):
        bonus = _bonus(text, position)
        if previous is not None:
            if position == previous + 1:
                bonus = max(bonus, BONUS_CONSECUTIVE)
            else:
                score += GAP_START + GAP_EXTENSION * (position - previous - 2)
        if order == 0:
            bonus *= FIRST_CHAR_MULTIPLIER
        score += SCORE_MATCH + bonus
        previous = position
    return score


def _fuzzy(pattern: str, haystack: str) -> list[int] | None:
    end = -1
    cursor = 0
    for index, char in enumerate(haystack):
        if char == pattern[cursor]:
            cursor += 1
            if cursor == len(pattern):
                end = index
                break
    if end < 0:
        return None
    cursor = len(pattern) - 1
    start = end
    for index in range(end, -1, -1):
        if haystack[index] == pattern[cursor]:
            cursor -= 1
            if cursor < 0:
                start = index
                break
    positions = []
    cursor = 0
    for index in range(start, end + 1):
        if cursor < len(pattern) and haystack[index] == pattern[cursor]:
            positions.append(index)
            cursor += 1
    return positions


def _match_term(term: Term, text: str) -> list[int] | None:
    pattern = term.text if term.case_sensitive else term.text.lower()
    haystack = text if term.case_sensitive else text.lower()
    if term.kind == "fuzzy":
        return _fuzzy(pattern, haystack)
    if term.kind == "prefix":
        start = 0 if haystack.startswith(pattern) else -1
    elif term.kind == "suffix":
        start = len(haystack) - len(pattern) if haystack.endswith(pattern) else -1
    else:
        start = haystack.find(pattern)
    if start < 0:
        return None
    return list(range(start, start + len(pattern)))


def match(terms: list[Term], text: str) -> Match | None:
    score = 0
    positions: set[int] = set()
    for term in terms:
        found = _match_term(term, text)
        if term.negate:
            if found is not None:
                return None
            continue
        if found is None:
            return None
        score += _score(text, found)
        positions.update(found)
    return Match(score, frozenset(positions))


def filter_items(
    query: str, items: Iterable[T], key: Callable[[T], str]
) -> list[tuple[T, frozenset[int]]]:
    terms = parse_query(query)
    if not terms:
        return [(item, frozenset()) for item in sorted(items, key=lambda item: key(item).lower())]
    scored = []
    for item in items:
        text = key(item)
        result = match(terms, text)
        if result is not None:
            scored.append((-result.score, len(text), text.lower(), item, result.positions))
    scored.sort(key=lambda row: row[:3])
    return [(item, positions) for *_, item, positions in scored]
