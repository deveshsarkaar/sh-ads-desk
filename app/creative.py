"""Creative Studio logic — SH Ads Desk (full build).

SCRIPT/BRIEF vs GENERATED ASSET (brief rule):
- Copy, poster briefs and reel scripts are TEXT produced by Roles 6-9
  (templates, no LLM keys, no paid calls) and are labelled as such.
- GENERATED assets (image/video files, API copy) are produced ONLY through
  the owner's OWN connected APIs (app/providers.py — API Providers page).
  The system itself selects NO vendor and holds NO key of its own: the
  owner pastes his Higgsfield/Kling/OpenAI/Claude key, generation runs
  through his account, and cost is recorded as "unknown — provider
  billing" (never an invented price). UNTESTED against real providers.
- Manual upload stays available (ManualUploadAdapter). Every asset —
  uploaded or generated — must pass the owner's visual check before it
  can enter the approval queue, and generated copy still passes Role 10
  (policy checker) exactly like template copy.
"""
import base64
import json

from . import policy_checker, providers, roles

VISUAL_CHECKLIST = [
    "readable text",
    "correct product names/logos",
    "no misleading claims",
    "no unauthorized brand marks",
]


class CreativeProviderAdapter:
    """Legacy manual adapter interface (kept for the upload flow).

    Generation itself now lives in app/providers.py and runs only through
    an API the OWNER connected on the API Providers page — the system
    never chooses or signs up for a vendor."""

    vendor = None  # no vendor selected by the system — owner connects his own

    def generate_image(self, brief):
        raise NotImplementedError(
            "Generation runs through the owner's connected API — see the "
            "API Providers page (app/providers.py).")

    def generate_video(self, script):
        raise NotImplementedError(
            "Generation runs through the owner's connected API — see the "
            "API Providers page (app/providers.py).")


class ManualUploadAdapter(CreativeProviderAdapter):
    """The shipped adapter: the owner creates assets himself (any tool he
    already has) and uploads the files in the Creative Studio."""

    vendor = "NONE — manual upload by owner"

    def describe_upload(self, filename, kind):
        return {
            "filename": filename, "kind": kind, "source": "manual upload (owner)",
            "visual_check": "PENDING", "checklist": list(VISUAL_CHECKLIST),
            "note": "Asset stays out of the approval queue until every "
                    "visual-check item is ticked by the owner.",
        }


def generate_creative_set(product, segment="students", settings=None):
    """Run Roles 6-9 for one product and gate the copy through Role 10.
    Returns a dict of TEXT artefacts + the policy result. If the eligibility
    gate fails, copy is still shown as a draft preview but is marked BLOCKED
    and can never enter the approval queue."""
    angles = roles.role_06_angle_generator(segment)["output"]["angles"]
    angle = angles[0]
    copy = roles.role_07_copywriter(angle)["output"]
    brief = roles.role_08_visual_poster_brief(angle)["output"]
    script = roles.role_09_reel_script(angle)["output"]
    text = copy["hinglish"]["headline"] + " " + copy["hinglish"]["text"]
    policy = policy_checker.check_creative(product, text, settings=settings)
    return {
        "product": product, "segment": segment, "angle": angle,
        "copy": copy, "poster_brief": brief, "reel_script": script,
        "policy": policy, "source": "templates",
        "label": "TEXT drafts (SCRIPT/BRIEF) — not generated image/video assets",
    }


# ---------------------------------------------------------------------------
# API wiring — used by the Creative Studio "Generate with API" actions.
# Every helper raises providers.NotConfigured when the capability is not
# connected, so the UI can show "API not connected" and nothing breaks.
# ---------------------------------------------------------------------------
COPY_PROMPT = (
    "Write one short Meta ad for the product '{product}' (Software Hub) for "
    "the audience segment '{segment}'. {instruction}"
    "Rules: no lifetime/guaranteed/official-reseller claims, no percentage-off "
    "or earnings claims, no fake urgency. Reply with ONLY a JSON object: "
    "{{\"hinglish\": {{\"headline\": \"...\", \"text\": \"...\", \"cta\": \"Learn More\"}}, "
    "\"english\": {{\"headline\": \"...\", \"text\": \"...\", \"cta\": \"Learn More\"}}}}"
)


def generate_copy_with_api(product, segment="students", settings=None,
                           instruction="", http=None, data_dir_override=None):
    """Copy via the owner's Text provider when connected; otherwise fall
    back to the template creative set, clearly labelled. Either way the
    copy passes the same Role 10 policy check before it is returned."""
    if not providers.is_configured("text", data_dir_override):
        result = generate_creative_set(product, segment, settings=settings)
        result["source"] = "templates"
        result["label"] = ("API not connected — template drafts use hue "
                           "(API Providers page se Text API connect karo)")
        return result
    adapter = providers.text_adapter(http=http, data_dir_override=data_dir_override)
    prompt = COPY_PROMPT.format(product=product, segment=segment,
                                instruction=(instruction + " ") if instruction else "")
    out = adapter.generate(prompt)
    raw = out["text"]
    parsed = None
    try:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end + 1])
    except ValueError:
        parsed = None
    copy = parsed if isinstance(parsed, dict) and "hinglish" in parsed else {
        "hinglish": {"headline": "", "text": raw, "cta": "Learn More"},
        "english": {"headline": "", "text": "", "cta": "Learn More"},
        "raw_model_output": raw,
    }
    text = ((copy.get("hinglish") or {}).get("headline", "") + " "
            + (copy.get("hinglish") or {}).get("text", "")).strip() or raw
    policy = policy_checker.check_creative(product, text, settings=settings)
    return {
        "product": product, "segment": segment, "angle": instruction or "API copy",
        "copy": copy, "poster_brief": None, "reel_script": None,
        "policy": policy, "source": "api",
        "provider": out["provider"], "model": out["model"],
        "request_id": out["request_id"], "cost_note": providers.COST_NOTE,
        "label": "API-generated copy via %s (%s) — cost %s"
                 % (out["provider"], out["model"], providers.COST_NOTE),
    }


def generate_poster_image(prompt, http=None, data_dir_override=None):
    """One image via the owner's Image provider → saved under
    data/generated/. Returns the asset metadata dict."""
    adapter = providers.image_adapter(http=http, data_dir_override=data_dir_override)
    out = adapter.generate(prompt)
    if out["kind"] == "b64":
        filename = providers.save_generated_file(
            base64.b64decode(out["value"]), "png", data_dir_override)
        remote_url = None
    else:
        filename, _ext = providers.fetch_result_file(
            out["value"], http=http, data_dir_override=data_dir_override)
        remote_url = out["value"]
    return {"filename": filename, "provider": out["provider"],
            "model": out["model"], "request_id": out["request_id"],
            "remote_url": remote_url, "cost_note": providers.COST_NOTE}


def generate_carousel_images(slides, http=None, data_dir_override=None):
    """Carousel = one image generation per slide brief. Returns a list of
    asset metadata dicts (same shape as generate_poster_image)."""
    results = []
    for slide in slides:
        results.append(generate_poster_image(slide, http=http,
                                              data_dir_override=data_dir_override))
    return results


def submit_reel_video(prompt, image_url=None, duration=None, aspect=None,
                      http=None, data_dir_override=None):
    adapter = providers.video_adapter(http=http, data_dir_override=data_dir_override)
    return adapter.submit(prompt, image_url=image_url, duration=duration,
                          aspect=aspect)


def poll_reel_video(job_id, http=None, data_dir_override=None):
    adapter = providers.video_adapter(http=http, data_dir_override=data_dir_override)
    return adapter.poll_once(job_id)
