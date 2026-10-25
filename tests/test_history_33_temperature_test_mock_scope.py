"""History: keep chat mocked while run_benchmark executes in its test."""

from pathlib import Path


SOURCE = (Path(__file__).parent / "test_temperature_column.py").read_text(encoding="utf-8")


def test_run_benchmark_call_is_inside_chat_mock_context():
    patch_start = SOURCE.index('with patch("homebench.chat"')
    benchmark_call = SOURCE.index("run_benchmark(", patch_start)
    rows_read = SOURCE.index("rows =", benchmark_call)
    assert patch_start < benchmark_call < rows_read
