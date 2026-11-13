from app.modules.chat import ranking


def test_tokenize_matches_spelling_variants_and_the_definite_article():
    assert ranking.tokenize("الإجازة السنوية") == ranking.tokenize("اجازه سنويه")


def test_tokenize_ignores_common_words():
    assert ranking.tokenize("أبي أشتغل من البيت") == ["اشتغل", "بيت"]


def test_bm25_scores_only_documents_that_share_a_word():
    documents = [
        ranking.tokenize("الاتصال عبر VPN أثناء العمل عن بعد"),
        ranking.tokenize("إجازة سنوية مدتها ٢١ يوماً"),
    ]

    scores = ranking.bm25(ranking.tokenize("VPN"), documents)

    assert scores[0] > 0
    assert scores[1] == 0


def test_bm25_favours_rare_words():
    documents = [
        ranking.tokenize("طلب صلاحية نظام"),
        ranking.tokenize("طلب إجازة"),
        ranking.tokenize("طلب تدريب"),
    ]

    rare_word_score = ranking.bm25(ranking.tokenize("صلاحية"), documents)[0]
    common_word_score = ranking.bm25(ranking.tokenize("طلب"), documents)[0]

    assert rare_word_score > common_word_score


def test_reciprocal_rank_fusion_rewards_items_ranked_high_in_both_lists():
    merged = ranking.reciprocal_rank_fusion([["a", "b", "c"], ["b", "d"]])

    assert merged[0] == "b"
    assert set(merged) == {"a", "b", "c", "d"}
