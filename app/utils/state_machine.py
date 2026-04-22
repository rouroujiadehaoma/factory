"""Legal waste batch status transitions (server-side source of truth)."""

ALLOWED_TRANSITIONS = {
    'registered': {'stored'},
    'stored': {'pending_transfer'},
    'pending_transfer': {'in_transit'},
    'in_transit': {'received_by_disposal_vendor'},
    'received_by_disposal_vendor': {'disposed'},
    'disposed': {'archived'},
    'archived': set(),
}


def can_transition(from_status: str, to_status: str) -> bool:
    if not from_status or not to_status:
        return False
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def next_statuses(from_status: str) -> set:
    return set(ALLOWED_TRANSITIONS.get(from_status or '', set()))
