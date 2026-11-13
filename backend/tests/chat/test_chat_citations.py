from app.modules.chat import citations


def test_reads_latin_and_arabic_indic_citation_numbers():
    assert citations.cited_numbers("أ [1]، ب [٢].") == {1, 2}


def test_accepts_citations_that_point_at_given_sources():
    assert citations.check_citations("أ [2] ب [1].", source_count=3) == [1, 2]


def test_rejects_an_answer_without_citations():
    assert citations.check_citations("إجازتك ٣٠ يوماً.", source_count=3) is None


def test_rejects_the_whole_answer_when_one_citation_is_invented():
    answer = "إجازتك ٢١ يوماً [1]، وبدل السكن ٥٠٠ ريال [7]."

    assert citations.check_citations(answer, source_count=3) is None


def test_renumbers_citations_to_match_the_sources_shown():
    assert citations.renumber("يومين [3]، عبر VPN [3].", cited=[3]) == "يومين [1]، عبر VPN [1]."
