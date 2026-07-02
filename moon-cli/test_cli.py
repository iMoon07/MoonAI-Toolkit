import unittest
from unittest.mock import patch, MagicMock, call
import time

# Assuming tests are run from the project root, e.g., `python -m unittest discover`
# This allows for correct package imports.
# Tests should be run from the project root using pytest.
# This allows for correct package imports when tests are in a top-level `tests` directory.
from moon_cli import cli
from moon_core.models import ChatRequest, Module


class TestCliHelpers(unittest.TestCase):
    """Unit tests for helper functions in cli.py."""

    def test_sanitize_input(self):
        """Tests the input sanitization function."""
        self.assertEqual(cli.sanitize_input("  hello world  "), "hello world")
        self.assertEqual(cli.sanitize_input("test\x00string"), "teststring")
        self.assertEqual(cli.sanitize_input("\ufeffbom here"), "bom here")
        self.assertEqual(cli.sanitize_input("zero\u200bwidth"), "zerowidth")
        self.assertEqual(cli.sanitize_input("  "), "")
        self.assertEqual(cli.sanitize_input("你好"), "你好")
        # The cli.py uses .encode().decode() which doesn't remove \r\n, but strip() does.
        self.assertEqual(cli.sanitize_input("test\r\n  "), "test")

    @patch('moon_cli.cli.console')
    def test_render_header(self, mock_console):
        """Tests the header rendering function."""
        cli.render_header("test-model")
        calls = [
            call.print("[bold cyan]🌙 Moon CLI[/bold cyan]"),
            call.print("[dim]test-model[/dim]\n")
        ]
        mock_console.print.assert_has_calls(calls)

    @patch('moon_cli.cli.console')
    def test_render_prompt_header(self, mock_console):
        """Tests the prompt header rendering function."""
        cli.render_prompt_header()
        mock_console.print.assert_called_once_with("\n[bold cyan]🌙 Moon[/bold cyan]\n")

    @patch('moon_cli.cli.console')
    @patch('time.time')
    def test_render_footer(self, mock_time, mock_console):
        """Tests the footer rendering function."""
        mock_time.side_effect = [1000.0, 1002.5]  # start_time, end_time
        start_time = time.time()
        # time.time() is called again inside the function
        cli.render_footer(tokens=50, start=start_time)

        elapsed = 2.5
        speed = 50 / elapsed

        mock_console.print.assert_called_once_with(f"\n\n[dim]✓ {elapsed:.1f}s | 50 tokens | {speed:.1f} tokens/s[/dim]\n")


@patch('moon_cli.cli.settings')
@patch('moon_cli.cli.console')
@patch('moon_cli.cli.moon_router')
@patch('moon_cli.cli.PromptSession')
class TestCliRunLoop(unittest.TestCase):
    """Unit tests for the main run() loop in cli.py."""

    def test_run_loop_exit_command(self, mock_prompt_session, mock_router, mock_console, mock_settings):
        """Tests if the main loop exits correctly on 'exit' command."""
        mock_session_instance = mock_prompt_session.return_value
        mock_session_instance.prompt.side_effect = ["exit"]

        cli.run()

        mock_console.print.assert_any_call("\n[dim]Sampai jumpa, kapten![/dim]")

    def test_run_loop_quit_command(self, mock_prompt_session, mock_router, mock_console, mock_settings):
        """Tests if the main loop exits correctly on 'quit' command."""
        mock_session_instance = mock_prompt_session.return_value
        mock_session_instance.prompt.side_effect = ["quit"]

        cli.run()
        mock_console.print.assert_any_call("\n[dim]Sampai jumpa, kapten![/dim]")

    def test_run_loop_clear_command(self, mock_prompt_session, mock_router, mock_console, mock_settings):
        """Tests the /clear command functionality."""
        mock_settings.model_name = "test-model"
        expected_header_str = f"{mock_settings.model_name} | [bold green]Developed By iMoon07[/bold green]"

        mock_session_instance = mock_prompt_session.return_value
        mock_session_instance.prompt.side_effect = ["/clear", EOFError("stop loop")]

        with self.assertRaises(EOFError):
            cli.run()

        # run() clears the console at the start, and the /clear command clears it again.
        self.assertEqual(mock_console.clear.call_count, 2)
        # render_header is called at start and after /clear. We check for the call's output.
        mock_console.print.assert_any_call(f"[dim]{expected_header_str}[/dim]\n")

    @patch('builtins.print')
    def test_run_loop_stream_handling(self, mock_builtin_print, mock_prompt_session, mock_router, mock_console, mock_settings):
        """Tests the stream handling and rendering logic."""
        mock_settings.model_name = "test-model"
        mock_session_instance = mock_prompt_session.return_value
        mock_session_instance.prompt.side_effect = ["hello", EOFError("stop loop")]

        mock_stream_generator = iter(["hello ", "world"])
        mock_router.chat_stream.return_value = mock_stream_generator

        mock_status = MagicMock()
        mock_console.status.return_value = mock_status

        with self.assertRaises(EOFError):
            cli.run()

        # 1. Check if router was called with correct ChatRequest
        self.assertTrue(mock_router.chat_stream.called)
        request_arg = mock_router.chat_stream.call_args[0][0]
        self.assertIsInstance(request_arg, ChatRequest)
        self.assertEqual(request_arg.content, "hello")
        self.assertEqual(request_arg.display_name, "Raja")
        self.assertEqual(request_arg.module, Module.CLI)

        # 2. Check spinner logic
        mock_status.start.assert_called_once()
        mock_status.stop.assert_called()

        # 3. Check that prompt header was rendered after first token
        mock_console.print.assert_any_call("\n[bold cyan]🌙 Moon[/bold cyan]\n")

        # 4. Check that stream output was printed directly via built-in print
        print_calls = [
            call("hello ", end="", flush=True),
            call("world", end="", flush=True)
        ]
        mock_builtin_print.assert_has_calls(print_calls, any_order=False)

        # 5. Check footer rendering
        footer_call_found = any(
            "tokens/s" in c.args[0] for c in mock_console.print.call_args_list if c.args
        )
        self.assertTrue(footer_call_found, "Footer was not rendered")

    def test_empty_input_continues_loop(self, mock_prompt_session, mock_router, mock_console, mock_settings):
        """Tests that empty input doesn't trigger an API call and continues the loop."""
        mock_session_instance = mock_prompt_session.return_value
        mock_session_instance.prompt.side_effect = ["   ", EOFError("stop loop")]

        with self.assertRaises(EOFError):
            cli.run()

        mock_router.chat_stream.assert_not_called()


if __name__ == '__main__':
    unittest.main()