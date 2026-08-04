"""Route-level tests for the queue UI: grouped list, item detail with
evidence preview, and that decisions only ever happen through a real POST
with an explicit decided_by.

Setup in these tests uses the queue_store/spine fixtures (their own
connections, opened in the test's thread) rather than anything shared
from `client`/`flask_app` — the app opens a fresh, thread-local connection
per request (see src/dispatch/queue/app.py's docstring for why), so there
is no single shared store instance to reach into from outside a request.
Both connections point at the same sandboxed SQLite file, which is all
that's needed for setup-then-assert-via-HTTP to work.
"""
from __future__ import annotations


def test_index_groups_items_by_priority(client, queue_store):
    queue_store.create(
        type="review", source_worker="receipt", priority="urgent", subject="Urgent thing"
    )
    queue_store.create(
        type="approval", source_worker="ifta", priority="whenever", subject="Someday thing"
    )

    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Urgent thing" in body
    assert "Someday thing" in body


def test_index_status_filter(client, queue_store):
    item = queue_store.create(
        type="review", source_worker="receipt", priority="today", subject="Filter me"
    )
    queue_store.approve(item["queue_item_id"], decided_by="human:mike")

    open_only = client.get("/?status=open")
    assert "Filter me" not in open_only.get_data(as_text=True)

    approved_only = client.get("/?status=approved")
    assert "Filter me" in approved_only.get_data(as_text=True)

    unfiltered = client.get("/")
    assert "Filter me" in unfiltered.get_data(as_text=True)


def test_item_detail_shows_metadata(client, queue_store):
    item = queue_store.create(
        type="review", source_worker="receipt", priority="today", subject="Detail view test"
    )
    response = client.get(f"/items/{item['queue_item_id']}")
    assert response.status_code == 200
    assert "Detail view test" in response.get_data(as_text=True)


def test_item_detail_404_for_unknown_id(client):
    response = client.get("/items/01UNKNOWNULIDDOESNOTEXIST0")
    assert response.status_code == 404


def test_evidence_preview_for_a_real_evidence_record(client, queue_store, spine, tmp_path):
    doc = tmp_path / "receipt.txt"
    doc.write_text("a real receipt")
    record = spine.register(doc, "pump_receipt", {"document_date": "2026-08-01"})

    item = queue_store.create(
        type="review",
        source_worker="receipt",
        priority="today",
        subject="Review this receipt",
        payload_refs=[record["evidence_record_id"]],
    )

    response = client.get(f"/items/{item['queue_item_id']}")
    body = response.get_data(as_text=True)
    assert "hash verified" in body
    assert "pump_receipt" in body


def test_evidence_preview_for_a_nonexistent_ref_does_not_crash(client, queue_store):
    item = queue_store.create(
        type="review",
        source_worker="receipt",
        priority="today",
        subject="Bogus ref",
        payload_refs=["not_a_real_evidence_id"],
    )
    response = client.get(f"/items/{item['queue_item_id']}")
    assert response.status_code == 200
    assert "No evidence record found" in response.get_data(as_text=True)


def test_evidence_preview_for_a_tampered_record_shows_integrity_warning(
    client, queue_store, spine, tmp_path
):
    doc = tmp_path / "receipt.txt"
    doc.write_text("a real receipt")
    record = spine.register(doc, "pump_receipt", {"document_date": "2026-08-01"})

    archived = spine._archive_root / record["archive_path"]
    archived.chmod(0o600)
    archived.write_bytes(b"tampered")

    item = queue_store.create(
        type="review",
        source_worker="receipt",
        priority="today",
        subject="Tampered evidence",
        payload_refs=[record["evidence_record_id"]],
    )
    response = client.get(f"/items/{item['queue_item_id']}")
    assert response.status_code == 200
    assert "integrity check failed" in response.get_data(as_text=True)


def test_approve_requires_decided_by(client, queue_store):
    item = queue_store.create(type="approval", source_worker="ifta", priority="urgent", subject="x")

    response = client.post(f"/items/{item['queue_item_id']}/approve", data={})
    assert response.status_code == 400
    assert queue_store.get(item["queue_item_id"])["status"] == "open"


def test_approve_with_decided_by_succeeds_and_redirects(client, queue_store):
    item = queue_store.create(type="approval", source_worker="ifta", priority="urgent", subject="x")

    response = client.post(
        f"/items/{item['queue_item_id']}/approve",
        data={"decided_by": "human:mike", "decision_note": "looks good"},
    )
    assert response.status_code == 302
    updated = queue_store.get(item["queue_item_id"])
    assert updated["status"] == "approved"
    assert updated["decided_by"] == "human:mike"
    assert updated["decision_note"] == "looks good"


def test_reject_with_decided_by_succeeds(client, queue_store):
    item = queue_store.create(type="review", source_worker="receipt", priority="today", subject="x")

    response = client.post(
        f"/items/{item['queue_item_id']}/reject", data={"decided_by": "human:mike"}
    )
    assert response.status_code == 302
    assert queue_store.get(item["queue_item_id"])["status"] == "rejected"


def test_start_review_route(client, queue_store):
    item = queue_store.create(type="review", source_worker="receipt", priority="today", subject="x")

    response = client.post(f"/items/{item['queue_item_id']}/start_review")
    assert response.status_code == 302
    assert queue_store.get(item["queue_item_id"])["status"] == "in_review"


def test_decision_route_on_decided_item_returns_400(client, queue_store):
    item = queue_store.create(type="approval", source_worker="ifta", priority="urgent", subject="x")
    queue_store.approve(item["queue_item_id"], decided_by="human:mike")

    response = client.post(
        f"/items/{item['queue_item_id']}/reject", data={"decided_by": "human:mike"}
    )
    assert response.status_code == 400
    assert queue_store.get(item["queue_item_id"])["status"] == "approved"
