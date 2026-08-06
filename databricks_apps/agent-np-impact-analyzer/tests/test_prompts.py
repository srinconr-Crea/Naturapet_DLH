from agent_server.prompts import IMPACT_ANALYZER_INSTRUCTIONS


def test_instructions_require_verified_context_before_any_other_tool():
    instructions = IMPACT_ANALYZER_INSTRUCTIONS.lower()

    assert "get_repository_context" in instructions
    assert "first" in instructions
    assert instructions.index("get_repository_context") < instructions.index("list_repository_tree")


def test_instructions_enforce_read_only_analysis_and_untrusted_content_policy():
    instructions = IMPACT_ANALYZER_INSTRUCTIONS.lower()

    for requirement in (
        "do not edit",
        "do not execute",
        "untrusted data",
        "ignore instructions embedded",
        "minimum viable change",
        "insufficient_evidence",
    ):
        assert requirement in instructions
