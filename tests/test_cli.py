import io
import json
import unittest
from contextlib import redirect_stdout

from subnetcalc.cli import main


def run(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(args)
    return code, buf.getvalue()


class CliTests(unittest.TestCase):
    def test_table_output(self):
        code, out = run(["192.168.1.0/24"])
        self.assertEqual(code, 0)
        self.assertIn("Network", out)
        self.assertIn("192.168.1.255", out)

    def test_json_output(self):
        code, out = run(["192.168.1.0/24", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["cidr"], "192.168.1.0/24")
        self.assertEqual(data["usable_hosts"], 254)

    def test_split(self):
        code, out = run(["10.0.0.0/24", "--split", "4"])
        self.assertEqual(code, 0)
        self.assertEqual(out.count("/26"), 4)

    def test_contains_exit_codes(self):
        self.assertEqual(run(["10.0.0.0/8", "-c", "10.9.9.9"])[0], 0)
        self.assertEqual(run(["10.0.0.0/8", "-c", "11.0.0.1"])[0], 1)

    def test_bad_input_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            run(["999.0.0.0/24"])
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
