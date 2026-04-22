from app.utils.state_machine import ALLOWED_TRANSITIONS, can_transition, next_statuses


def test_no_backward_transition():
    assert not can_transition('disposed', 'stored')
    assert not can_transition('archived', 'disposed')


def test_forward_chain():
    assert can_transition('registered', 'stored')
    assert can_transition('stored', 'pending_transfer')
    assert can_transition('pending_transfer', 'in_transit')
    assert can_transition('in_transit', 'received_by_disposal_vendor')
    assert can_transition('received_by_disposal_vendor', 'disposed')
    assert can_transition('disposed', 'archived')


def test_next_statuses_registered():
    assert next_statuses('registered') == {'stored'}


def test_archived_terminal():
    assert ALLOWED_TRANSITIONS['archived'] == set()
