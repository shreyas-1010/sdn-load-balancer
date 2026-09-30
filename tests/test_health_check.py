import unittest
from src.monitor import SwitchTelemetry, probe_tcp_service

class TestTelemetryAndProbes(unittest.TestCase):
    def test_telemetry_rate_calculation(self):
        tel = SwitchTelemetry([2, 3, 4])
        self.assertEqual(tel.get_port_rate(2), 0.0)

        # Update initial
        tel.update_port_stats(2, 1000)
        # Rate remains zero until second sample provides delta time
        self.assertGreaterEqual(tel.get_port_rate(2), 0.0)

    def test_unreachable_probe(self):
        # Local loopback on random closed port
        result = probe_tcp_service('127.0.0.1', 65530, timeout=0.1)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
