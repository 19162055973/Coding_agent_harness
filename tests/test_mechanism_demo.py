from forgeloop.demo.mechanisms import (
    demo_classifier_focus,
    demo_feedback_changes_next_action,
    demo_guardrail_blocks_danger,
)


def test_mechanism_demos():
    demo_guardrail_blocks_danger()
    demo_feedback_changes_next_action()
    demo_classifier_focus()
