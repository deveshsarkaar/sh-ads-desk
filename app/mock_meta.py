"""Mock Meta client — SH Ads Desk Step 1 (MOCK build).

Stands in for the Meta Marketing API. Creates campaign / ad set / ad objects
with fake IDs, is idempotency-key aware (the same key never creates a
duplicate), records a change history per object (used by rollback), and
supports fresh-state reads. NO network calls, NO real Meta account.
"""
import uuid


class MockMetaClient:
    def __init__(self):
        self.objects = {}          # id -> object dict
        self._idem = {}            # idempotency_key -> object id
        self._counters = {"campaign": 0, "adset": 0, "ad": 0}
        self.requests = []         # fake request log (request IDs, redacted-safe)

    def _request_id(self):
        rid = "mock_req_" + uuid.uuid4().hex[:10]
        self.requests.append(rid)
        return rid

    def _create(self, kind, payload, idempotency_key):
        if idempotency_key and idempotency_key in self._idem:
            return self.objects[self._idem[idempotency_key]]  # no duplicate
        self._counters[kind] += 1
        oid = "mock_%s_%d" % (kind, self._counters[kind])
        obj = {"id": oid, "kind": kind, "status": "PAUSED", "history": []}
        obj.update(payload)
        obj["history"].append({
            "field": "status", "old": None, "new": "PAUSED",
            "request_id": self._request_id(),
        })
        self.objects[oid] = obj
        if idempotency_key:
            self._idem[idempotency_key] = oid
        return obj

    def create_campaign(self, name, idempotency_key=None, budget=None):
        return self._create("campaign", {"name": name, "budget": budget}, idempotency_key)

    def create_adset(self, campaign_id, name, idempotency_key=None, budget=None):
        return self._create("adset", {"campaign_id": campaign_id, "name": name, "budget": budget},
                            idempotency_key)

    def create_ad(self, adset_id, name, creative_text, idempotency_key=None):
        return self._create("ad", {"adset_id": adset_id, "name": name, "creative_text": creative_text},
                            idempotency_key)

    def get_object(self, object_id):
        """Fresh-state read (a copy, so callers see current values)."""
        obj = self.objects.get(object_id)
        if obj is None:
            return None
        copy = dict(obj)
        copy["history"] = list(obj["history"])
        return copy

    def _change(self, object_id, field, new_value):
        obj = self.objects[object_id]
        old = obj.get(field)
        obj[field] = new_value
        entry = {"field": field, "old": old, "new": new_value, "request_id": self._request_id()}
        obj["history"].append(entry)
        return entry

    def set_status(self, object_id, status):
        return self._change(object_id, "status", status)

    def set_budget(self, object_id, budget):
        obj = self.objects[object_id]
        if obj["kind"] == "ad":
            raise ValueError("Budgets live at campaign or ad-set level only, never per ad.")
        return self._change(object_id, "budget", budget)

    def pause_all(self):
        changed = []
        for oid, obj in self.objects.items():
            if obj.get("status") != "PAUSED":
                self.set_status(oid, "PAUSED")
                changed.append(oid)
        return changed

    def count(self, kind=None):
        if kind is None:
            return len(self.objects)
        return sum(1 for o in self.objects.values() if o["kind"] == kind)
