import src.run_pipeline as run_pipeline

def test_main_runs_fetch_then_load(monkeypatch):
    calls = []

    def fake_run_script(script_name):
        calls.append(script_name)
        return 0

    monkeypatch.setattr(run_pipeline, "run_script", fake_run_script)

    result = run_pipeline.main()

    assert result == 0 
    assert calls == ["fetch_weather.py", "load_weather.py"]

def test_main_stops_when_fetch_fails(monkeypatch):
    calls = []

    def fake_run_script(script_name):
        calls.append(script_name)
        return 1

    monkeypatch.setattr(run_pipeline,"run_script", fake_run_script)

    result = run_pipeline.main()

    assert result == 1
    assert calls == ["fetch_weather.py"]

def test_main_returns_loader_failure(monkeypatch):
    calls = []

    def fake_run_script(script_name):
        calls.append(script_name)
        if script_name == "fetch_weather.py":
            return 0
        return 2

    monkeypatch.setattr(run_pipeline, "run_script", fake_run_script)

    result = run_pipeline.main()

    assert result == 2
    assert calls == ["fetch_weather.py", "load_weather.py"]


def test_run_script_builds_correct_command(monkeypatch):
    captured = {}

    def fake_subprocess_run(command,cwd):
        captured["command"] = command
        captured["cwd"] = cwd

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        run_pipeline.subprocess,
        "run",
        fake_subprocess_run,
    )

    result = run_pipeline.run_script("fetch_weather.py")

    expected_script = (
        run_pipeline.PROJECT_ROOT / "src" / "fetch_weather.py"
    )

    assert result == 0
    assert captured["command"] == [
        run_pipeline.sys.executable,
        str(expected_script)
    ]
    assert captured["cwd"] == run_pipeline.PROJECT_ROOT
    




