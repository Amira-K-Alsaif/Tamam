from app.modules.chat.prompts import build_system_prompt, build_user_prompt


def test_the_assistant_introduces_itself_with_the_configured_company():
    assert "شركة الواحة" in build_system_prompt("شركة الواحة")


def test_sources_are_numbered_and_wrapped_as_data(chunks):
    prompt = build_user_prompt("كم يوم إجازتي؟", chunks)

    assert prompt.startswith("<sources>")
    assert "[1] (سياسة الإجازات · الإجازة السنوية)" in prompt
    assert "[2] (سياسة العمل عن بعد · الأهلية)" in prompt
    assert prompt.endswith("السؤال: كم يوم إجازتي؟")
