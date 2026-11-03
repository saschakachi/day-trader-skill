#!/usr/bin/env python3
"""Deterministic V1 workflow state machine. It never submits live orders."""

STATES = ("DISCOVERED", "WATCHING", "TRIGGERED", "APPROVED", "PAPER_OPEN", "PAPER_CLOSED", "JOURNALED")
TRANSITIONS = {
    "DISCOVERED": {"WATCHING"},
    "WATCHING": {"TRIGGERED"},
    "TRIGGERED": {"APPROVED", "WATCHING"},
    "APPROVED": {"PAPER_OPEN"},
    "PAPER_OPEN": {"PAPER_CLOSED"},
    "PAPER_CLOSED": {"JOURNALED"},
    "JOURNALED": set(),
}


def transition(ticket, target, risk_verdict=None, user_approved=False):
    current = ticket.get("state", "DISCOVERED")
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError("invalid transition: %s -> %s" % (current, target))
    if target == "APPROVED":
        if risk_verdict != "PASS":
            raise PermissionError("risk gate must PASS before approval")
        if not user_approved:
            raise PermissionError("explicit user approval required")
    if target == "PAPER_OPEN":
        if ticket.get("mode", "paper") != "paper":
            raise PermissionError("V1 permits paper execution only")
        if ticket.get("risk_verdict") != "PASS":
            raise PermissionError("risk PASS is immutable execution prerequisite")
        if not ticket.get("user_approved"):
            raise PermissionError("user approval is immutable execution prerequisite")
    updated = dict(ticket)
    updated["state"] = target
    if target == "APPROVED":
        updated["risk_verdict"] = "PASS"
        updated["user_approved"] = True
        updated["mode"] = "paper"
    return updated
