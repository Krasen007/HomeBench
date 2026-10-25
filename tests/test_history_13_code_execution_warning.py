"""History: warn users that generated code executes locally."""

from pathlib import Path
import inspect

from tasks import code_task


HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_web_ui_warns_about_running_model_generated_python():
    assert "model-generated Python locally" in HTML
    assert "Only run models" in HTML


def test_code_task_documents_that_it_executes_generated_python():
    source = inspect.getsource(code_task._code_status)
    assert "subprocess.run([sys.executable, path]" in source
