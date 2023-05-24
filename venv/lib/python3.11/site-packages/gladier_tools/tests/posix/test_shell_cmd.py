import os
import subprocess
import tempfile
from typing import Any, Dict, List, NamedTuple, Optional, Type, Union

import pytest
from gladier_tools.posix.shell_cmd import shell_cmd


class Case(NamedTuple):
    args: Union[str, List[str]]
    capture_output: Optional[bool] = None
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    input_path: Optional[str] = None
    output_path: Optional[bool] = None
    error_path: Optional[bool] = None
    exception_on_error: Optional[bool] = None
    expected_returncode: int = 0
    expected_exception: Optional[Type[Exception]] = None
    expected_stdout: Optional[str] = None

    def to_call_dict(self) -> Dict[str, Any]:
        r_dict = {
            k: v
            for k, v in self._asdict().items()
            if not k.startswith("expected") and v is not None
        }
        # Default behavior is to capture output if the test case defines
        # required stdout
        if self.capture_output is None and self.expected_stdout is not None:
            r_dict["capture_output"] = True
        return r_dict


cases = [
    Case(args="ls"),
    Case(args=["ls", "-a"], expected_stdout=".."),
    Case(args=["ls", "-a"], expected_stdout="..", output_path=True),
    Case(args="pwd", expected_stdout="/", cwd="~/"),
    Case(
        args=["echo in_cmd", "pos1", "pos2"],
        expected_stdout="in_cmd pos1 pos2",
    ),
    Case(args="cat", expected_stdout="pytest", input_path=os.path.abspath(__file__)),
    Case(args="NoT_ReallY_A_Cmd", expected_exception=subprocess.CalledProcessError),
    Case(
        args="NoT_ReallY_A_Cmd",
        exception_on_error=False,
        expected_returncode=127,
    ),
    Case(
        args="echo $TEST_VAR", env={"TEST_VAR": "test_val"}, expected_stdout="test_val"
    ),
]


@pytest.mark.parametrize("test_case", cases)
def test_shell_cmd(test_case: Case):
    call_args = test_case.to_call_dict()
    try:
        if test_case.output_path:
            output_file, output_path = tempfile.mkstemp()
            call_args["output_path"] = output_path
            call_args["capture_output"] = False
        if test_case.error_path:
            error_file, error_path = tempfile.mkstemp()
            call_args["error_path"] = error_path
            call_args["capture_output"] = False
        returncode, stdout, stderr = shell_cmd(**call_args)
        if test_case.output_path:
            stdout = os.read(output_file, 1024 * 1024)
            stdout = stdout.decode("utf-8")
            os.close(output_file)
            os.remove(output_path)
        if test_case.error_path:
            stderr = os.read(output_file, 1024 * 1024)
            stderr = stderr.decode("utf-8")
            os.close(error_file)
            os.remove(error_path)
    except Exception as e:
        assert type(e) == test_case.expected_exception
        return

    # These test assertions need to be outside the try/except above
    assert test_case.expected_exception is None
    assert test_case.expected_returncode == returncode
    if test_case.expected_stdout is not None:
        assert test_case.expected_stdout in stdout
