from app.modules.chat import retrieval


def test_tokenize_matches_spelling_variants_and_the_definite_article():
    assert retrieval.tokenize("الإجازة السنوية") == retrieval.tokenize("اجازه سنويه")


def test_bm25_scores_only_documents_that_share_a_word():
    documents = [
        retrieval.tokenize("الاتصال عبر VPN أثناء العمل عن بعد"),
        retrieval.tokenize("إجازة سنوية مدتها ٢١ يوماً"),
    ]

    scores = retrieval.bm25(retrieval.tokenize("VPN"), documents)

    assert scores[0] > 0
    assert scores[1] == 0


def test_bm25_favours_rare_words():
    documents = [
        retrieval.tokenize("طلب صلاحية نظام"),
        retrieval.tokenize("طلب إجازة"),
        retrieval.tokenize("طلب تدريب"),
    ]

    rare_word_score = retrieval.bm25(retrieval.tokenize("صلاحية"), documents)[0]
    common_word_score = retrieval.bm25(retrieval.tokenize("طلب"), documents)[0]

    assert rare_word_score > common_word_score


def test_reciprocal_rank_fusion_rewards_items_ranked_high_in_both_lists():
    merged = retrieval.reciprocal_rank_fusion([["a", "b", "c"], ["b", "d"]])

    assert merged[0] == "b"
    assert set(merged) == {"a", "b", "c", "d"}


def test_tokenize_ignores_common_words():
    assert retrieval.tokenize("أبي أشتغل من البيت") == ["اشتغل", "بيت"]
