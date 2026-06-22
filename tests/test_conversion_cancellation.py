import subprocess
import unittest
from unittest.mock import Mock, patch

from components.shared.atomic_output import OutputCancelled
from App_ConversorPDF.services.process_control import run_cancellable_process


class ConversionCancellationTests(unittest.TestCase):
    def test_cancellation_terminates_running_process(self):
        process = Mock()
        process.poll.return_value = None
        process.communicate.side_effect = subprocess.TimeoutExpired(["soffice"], 0.15)
        process.wait.return_value = 0
        cancel_states = iter((False, True))

        with (
            patch("App_ConversorPDF.services.process_control.subprocess.Popen", return_value=process),
            patch("App_ConversorPDF.services.process_control.os.name", "posix"),
            self.assertRaises(OutputCancelled),
        ):
            run_cancellable_process(
                ["soffice", "--headless"],
                timeout_seconds=10,
                cancel_check=lambda: next(cancel_states),
            )

        process.terminate.assert_called_once_with()
        process.wait.assert_called_once()


if __name__ == "__main__":
    unittest.main()
