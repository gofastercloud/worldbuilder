"""Tests for webapp/app.py — request hardening, project resolution, input validation."""

import app as webapp
import imagegen
import pytest
import voicegen


@pytest.fixture
def client(tmp_project, monkeypatch):
    """Flask test client whose only project root is the tmp_project's parent."""
    monkeypatch.setattr(webapp, "PROJECTS_ROOTS", [tmp_project.parent])
    monkeypatch.setattr(webapp, "PLAYGROUND_DIR", tmp_project.parent / "playground" / "images")
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


# ── Host / origin checks ─────────────────────────────────────────────────────

class TestHostCheck:
    @pytest.mark.parametrize("host", ["localhost", "localhost:5000", "127.0.0.1:5000", "[::1]:5000"])
    def test_local_hosts_allowed(self, client, host):
        res = client.get("/api/projects", headers={"Host": host})
        assert res.status_code == 200

    @pytest.mark.parametrize("host", ["evil.example.com", "evil.example.com:5000", "127.0.0.1.evil.com"])
    def test_other_hosts_rejected(self, client, host):
        """DNS rebinding: a hostile domain resolving to 127.0.0.1 must not reach the API."""
        res = client.get("/api/projects", headers={"Host": host})
        assert res.status_code == 403

    def test_form_post_rejected(self, client):
        """A cross-site HTML form can't send application/json, so form posts must be refused."""
        res = client.post("/api/project/test-project/voices/generate-all", data={"force": "true"})
        assert res.status_code == 415

    def test_json_post_allowed_through(self, client):
        res = client.post("/api/project/test-project/voices/generate-all", json={})
        assert res.status_code == 200
        assert res.get_json()["submitted"] == 0

    def test_security_headers(self, client):
        res = client.get("/api/projects")
        csp = res.headers["Content-Security-Policy"]
        assert "connect-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert res.headers["X-Content-Type-Options"] == "nosniff"


# ── Project resolution ───────────────────────────────────────────────────────

class TestProjectResolution:
    def test_known_project(self, client):
        res = client.get("/api/project/test-project/entities/character")
        assert res.status_code == 200
        assert [e["slug"] for e in res.get_json()] == ["test-hero"]

    def test_unknown_project_is_json_404(self, client):
        res = client.get("/api/project/nope/entities/character")
        assert res.status_code == 404
        assert res.get_json() == {"error": "Project not found"}

    def test_unknown_project_voice_file_is_404(self, client):
        res = client.get("/api/project/nope/voices/x.mp3")
        assert res.status_code == 404

    @pytest.mark.parametrize("slug", ["..", ".", "a/b", "../test-project", ".hidden", ""])
    def test_resolve_rejects_non_component_slugs(self, tmp_project, monkeypatch, slug):
        monkeypatch.setattr(webapp, "PROJECTS_ROOTS", [tmp_project.parent / "sub"])
        # Even with a project.yaml one level up, ".." must not resolve to it
        (tmp_project.parent / "project.yaml").write_text("title: parent\n")
        assert webapp.resolve_project_dir(slug) is None


# ── Image request validation ─────────────────────────────────────────────────

class TestImageValidation:
    def test_unknown_style_maps_to_default(self):
        assert imagegen.normalise_style("photorealistic") == "photorealistic"
        assert imagegen.normalise_style("x" * 50) == "default"
        assert imagegen.normalise_style(None) == "default"
        assert imagegen.normalise_style(["x"]) == "default"
        assert imagegen.normalise_style({"preset": "x"}) == "default"

    def test_defaults_valid(self):
        assert imagegen.validate_params() == (
            imagegen.DEFAULT_STEPS, imagegen.DEFAULT_WIDTH, imagegen.DEFAULT_HEIGHT, None
        )

    def test_numeric_strings_accepted(self):
        assert imagegen.validate_params("9", "1024", "512", "42") == (9, 1024, 512, 42)

    @pytest.mark.parametrize("kwargs", [
        {"steps": 0}, {"steps": 1000}, {"steps": "abc"}, {"steps": True}, {"steps": 2.5},
        {"width": 20000}, {"height": 100}, {"width": 1000},  # not a multiple of 16
        {"seed": -1}, {"seed": 2**40}, {"seed": [1]},
    ])
    def test_invalid_rejected(self, kwargs):
        with pytest.raises(ValueError):
            imagegen.validate_params(**kwargs)

    def test_playground_bad_params_400(self, client):
        res = client.post("/api/imagegen/playground", json={"prompt": "a cat", "width": 20000})
        assert res.status_code == 400
        assert "width" in res.get_json()["error"]

    def test_finished_jobs_pruned(self, monkeypatch):
        monkeypatch.setattr(imagegen, "_jobs", {})
        monkeypatch.setattr(imagegen, "MAX_FINISHED_JOBS", 3)
        for i in range(5):
            imagegen._jobs[f"j{i}"] = {"job_id": f"j{i}", "status": "complete", "completed_at": i}
        imagegen._jobs["running"] = {"job_id": "running", "status": "running"}
        with imagegen._jobs_lock:
            imagegen._prune_finished_jobs()
        assert sorted(imagegen._jobs) == ["j2", "j3", "j4", "running"]


# ── Voice request validation ─────────────────────────────────────────────────

class TestVoiceValidation:
    def test_valid(self):
        assert voicegen.validate_request("Hello there.", 1) == ("Hello there.", 1.0)

    @pytest.mark.parametrize("text,speed", [
        ("", 1.0), ("   ", 1.0), (None, 1.0), (123, 1.0),
        ("x" * (voicegen.MAX_TEXT_CHARS + 1), 1.0),
        ("hi", 0.1), ("hi", 5), ("hi", "fast"), ("hi", True),
    ])
    def test_invalid_rejected(self, text, speed):
        with pytest.raises(ValueError):
            voicegen.validate_request(text, speed)

    def test_route_rejects_long_text(self, client):
        res = client.post(
            "/api/project/test-project/entity/character/test-hero/voice",
            json={"text": "x" * (voicegen.MAX_TEXT_CHARS + 1)},
        )
        assert res.status_code == 400
        assert "at most" in res.get_json()["error"]

    def test_route_rejects_non_string_text(self, client):
        res = client.post("/api/project/test-project/entity/character/test-hero/voice", json={"text": 5})
        assert res.status_code == 400
        assert res.get_json()["error"] == "text and instruct must be strings"

    def test_finished_jobs_pruned(self, monkeypatch):
        monkeypatch.setattr(voicegen, "_jobs", {})
        monkeypatch.setattr(voicegen, "MAX_FINISHED_JOBS", 2)
        for i in range(4):
            voicegen._jobs[f"j{i}"] = {"job_id": f"j{i}", "status": "completed", "completed_at": i}
        voicegen._jobs["q"] = {"job_id": "q", "status": "queued", "created_at": 0}
        with voicegen._job_lock:
            voicegen._prune_finished_jobs()
        assert sorted(voicegen._jobs) == ["j2", "j3", "q"]

    def test_get_job_returns_copy(self, monkeypatch):
        monkeypatch.setattr(voicegen, "_jobs", {"a": {"job_id": "a", "status": "queued"}})
        snapshot = voicegen.get_job("a")
        assert snapshot is not None
        snapshot["status"] = "tampered"
        assert voicegen._jobs["a"]["status"] == "queued"


class TestBadRequestBodies:
    @pytest.mark.parametrize("body", ['["not", "an", "object"]', '"string"', "42"])
    def test_non_object_json_is_400(self, client, body):
        res = client.post("/api/imagegen/playground", data=body, content_type="application/json")
        assert res.status_code == 400
        assert res.get_json() == {"error": "Request body must be a JSON object"}

    def test_infinite_steps_is_400(self, client):
        res = client.post("/api/imagegen/playground", data='{"prompt": "x", "steps": Infinity}',
                          content_type="application/json")
        assert res.status_code == 400

    def test_non_string_prompt_is_400(self, client):
        res = client.post("/api/imagegen/playground", json={"prompt": ["x"]})
        assert res.status_code == 400

    def test_long_prompt_is_400(self, client):
        res = client.post("/api/imagegen/playground", json={"prompt": "x" * (imagegen.MAX_PROMPT_CHARS + 1)})
        assert res.status_code == 400

    def test_non_string_style_is_400_not_500(self, client):
        """A list style used to crash with TypeError; it now maps to the default preset."""
        res = client.post("/api/imagegen/playground", json={"prompt": "x", "style": ["x"], "width": 1})
        assert res.status_code == 400
        assert "width" in res.get_json()["error"]

    def test_long_instruct_is_400(self, client):
        res = client.post("/api/project/test-project/entity/character/test-hero/voice",
                          json={"text": "Hello.", "instruct": "x" * (voicegen.MAX_INSTRUCT_CHARS + 1)})
        assert res.status_code == 400


class TestQueueCap:
    def test_voice_queue_full_rejected(self, tmp_project, monkeypatch):
        monkeypatch.setattr(voicegen, "_jobs", {})
        monkeypatch.setattr(voicegen, "_job_queue", [])
        monkeypatch.setattr(voicegen, "_worker_started", True)  # don't start a real worker
        monkeypatch.setattr(voicegen, "MAX_QUEUED_JOBS", 2)
        results = [voicegen.submit_job(f"line {i}", "calm", tmp_project, "p", "e", "E", "character")
                   for i in range(3)]
        assert [r["status"] for r in results] == ["queued", "queued", "failed"]
        assert len(voicegen._job_queue) == 2
