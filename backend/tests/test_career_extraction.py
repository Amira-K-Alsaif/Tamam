from app.modules.career.extraction import KeywordExtractor, load_dictionary
from app.modules.career.text_ar import normalize

EXTRACTOR = KeywordExtractor(load_dictionary())


def keys(text: str) -> dict:
    return {s.skill_key: s for s in EXTRACTOR.extract(text)}


def test_normalize_treats_alef_forms_as_one_word():
    assert normalize("إدارة") == normalize("ادارة") == normalize("اِدارة")


def test_arabic_and_english_names_map_to_one_skill():
    assert "python" in keys("خبرة في بايثون")
    assert "python" in keys("Experience with Python")


def test_a_plus_skill_is_preferred():
    assert keys("إجادة اللغة الإنجليزية ميزة إضافية")["english"].importance == "preferred"


def test_required_wins_over_preferred():
    found = keys("يشترط إجادة الإنجليزية. الإنجليزية ميزة")
    assert found["english"].importance == "required"


def test_short_arabic_alias_needs_a_whole_word():
    found = keys("مهارات تحليلية قوية وخبرة في الحسابات")
    assert "hr_systems" not in found  # «قوية» is not «قوى»
    assert "erp" not in found  # «الحسابات» is not «ساب»


def test_driving_licence_is_not_leadership():
    found = keys("يشترط رخصة قيادة سارية")
    assert "driving_license" in found
    assert "team_leadership" not in found


def test_source_span_keeps_the_matching_sentence():
    found = keys("المهام: إعداد التسويات البنكية. دوام مرن")
    assert "التسويات" in found["reconciliation"].source_span
