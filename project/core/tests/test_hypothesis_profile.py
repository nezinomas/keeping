from hypothesis import settings

MAX_EXAMPLES = {"dev": 20, "gate": 100}


def test_profile_runs_its_examples_without_a_deadline(request):
    profile = request.config.getoption("--hypothesis-profile") or "dev"

    assert settings.get_current_profile_name() == profile
    assert settings().max_examples == MAX_EXAMPLES[profile]
    assert settings().deadline is None
