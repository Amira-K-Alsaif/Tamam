"""Pipeline step 6: check the model's citations before trusting its answer.

An answer is accepted only if it cites at least one source and every number it
cites points at a source we actually gave the model. Anything else is rejected
as a whole, because one invented sentence next to a real citation would still
look trustworthy to the reader.
"""

import re

_CITATION = re.compile(r"\[(\d+)\]")


def cited_numbers(answer: str) -> set[int]:
    """The source numbers cited in the answer, such as {1, 3} for "... [1] ... [3]"."""
    # \d also matches Arabic-Indic digits, and int() reads them, so [١] counts as [1].
    return {int(number) for number in _CITATION.findall(answer)}


def check_citations(answer: str, source_count: int) -> list[int] | None:
    """The cited numbers in order, or None when the answer must be rejected."""
    cited = cited_numbers(answer)
    if not cited or not cited <= set(range(1, source_count + 1)):
        return None
    return sorted(cited)


def renumber(answer: str, cited: list[int]) -> str:
    """Rewrites the citations as [1], [2], ... in the order of `cited`, so they match
    the list of sources the reader sees under the answer."""
    new_numbers = {old: new for new, old in enumerate(cited, start=1)}
    return _CITATION.sub(lambda match: f"[{new_numbers[int(match[1])]}]", answer)
