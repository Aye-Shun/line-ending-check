from pathlib import Path
import subprocess
import tempfile
import unittest


PROGRAM = Path(__file__).resolve().with_name("line-ending-check")


def run(*args, data=b""):
    return subprocess.run(
        [str(PROGRAM), *map(str, args)], input=data, capture_output=True, timeout=5
    )


class LineEndingCheckTests(unittest.TestCase):
    def check_counts(self, data, style, lf, crlf, cr):
        result = run("-", data=data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(
            result.stdout,
            f"Style: {style}\nLF: {lf}\nCRLF: {crlf}\nCR: {cr}\n".encode(),
        )

    def test_empty(self):
        self.check_counts(b"", "empty", 0, 0, 0)

    def test_nonempty_without_endings(self):
        self.check_counts("caf\u00e9".encode(), "no line endings", 0, 0, 0)

    def test_uniform_styles(self):
        for ending, style, counts in (
            (b"\n", "LF", (2, 0, 0)),
            (b"\r\n", "CRLF", (0, 2, 0)),
            (b"\r", "CR", (0, 0, 2)),
        ):
            with self.subTest(style=style):
                self.check_counts(b"a" + ending + b"b" + ending, style, *counts)

    def test_mixed_and_adjacent_endings(self):
        self.check_counts(b"\r\r\n\ntext\r", "mixed", 1, 1, 2)

    def test_crlf_across_read_boundary(self):
        self.check_counts(b"x" * 4095 + b"\r\n" + b"y" * 4094 + b"\r",
                          "mixed", 0, 1, 1)

    def test_boundary_cr_before_text(self):
        self.check_counts(b"x" * 4095 + b"\rz\n", "mixed", 1, 0, 1)

    def test_nul_discards_earlier_counts(self):
        result = run("-", data=b"\n" * 5000 + b"\0\r\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"NUL byte", result.stderr)

    def test_file_remains_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "mixed lines.txt"
            content = b"alpha\nbeta\r\n"
            path.write_bytes(content)
            result = run(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b"Style: mixed\nLF: 1\nCRLF: 1\nCR: 0\n")
            self.assertEqual(path.read_bytes(), content)

    def test_file_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            for path in (Path(folder) / "missing", Path(folder)):
                with self.subTest(path=path):
                    result = run(path)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertIn(b"line-ending-check:", result.stderr)

    def test_usage_and_help(self):
        for args in ((), ("one", "two")):
            result = run(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"Usage:", result.stderr)
        result = run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"Usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
