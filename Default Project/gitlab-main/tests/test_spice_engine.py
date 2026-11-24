import math
import unittest
from unittest.mock import patch

import spice_engine as se
from app import LAB4_DEFAULTS, LAB4_UNITS, app


def lab4_form(**overrides):
    form = dict(LAB4_DEFAULTS, analysis="dc")
    for field, unit in LAB4_UNITS.items():
        form[f"{field}_unit"] = unit
    form.update(overrides)
    return form


PARAMS = {
    "vcc": 12.0, "r1": 100e3, "r2": 22e3, "rc": 2.2e3, "re": 1e3,
    "rl": 10e3, "cin": 10e-6, "cout": 10e-6, "bf": 100.0, "vaf": 100.0,
    "isat": 1e-14, "amp": 10e-3, "freq": 1e3, "ac_fmin": 0.1,
    "ac_fmax": 10e6, "ac_per_dec": 20, "tran_stop": 3e-3,
    "model_name": "QNPN", "model_params": "",
}


class TestNetlist(unittest.TestCase):
    def test_dc_netlist_has_required_directives(self):
        netlist = se.build_netlist(PARAMS, "dc")
        self.assertIn("VCC VCC 0 DC 12", netlist)
        self.assertIn("Q1 COLL BASE EMIT QNPN", netlist)
        self.assertIn(".model QNPN NPN(BF=100 VAF=100 IS=1e-14)", netlist)
        self.assertIn(".op", netlist)
        self.assertTrue(netlist.rstrip().endswith(".end"))

    def test_ac_netlist_prints_gain_and_phase_reference(self):
        netlist = se.build_netlist(PARAMS, "ac")
        self.assertIn(".ac dec 20 0.1 10000000", netlist)
        self.assertIn(".print ac vdb(out) vp(out)", netlist)
        self.assertIn(".print ac vdb(base) vp(base)", netlist)

    def test_tran_netlist_uses_sin_source_and_print(self):
        netlist = se.build_netlist(PARAMS, "tran")
        self.assertIn("SIN(0 0.01 1000)", netlist)
        self.assertIn(".tran 3e-06 0.003", netlist)
        self.assertIn(".print tran v(base) v(out)", netlist)

    def test_instructor_model_params_are_used(self):
        p = dict(PARAMS, model_name="2N2222", model_params="BF=180 VAF=100 IS=1e-15")
        netlist = se.build_netlist(p, "dc")
        self.assertIn(".model 2N2222 NPN(BF=180 VAF=100 IS=1e-15)", netlist)
        self.assertIn("Q1 COLL BASE EMIT 2N2222", netlist)

    def test_unsafe_model_text_is_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.build_netlist(dict(PARAMS, model_name="Q1\n.end"), "dc")
        with self.assertRaises(se.SpiceError):
            se.build_netlist(dict(PARAMS, model_params="BF=100\n.end"), "dc")


class TestParsers(unittest.TestCase):
    def test_parse_op_matches_analytical_baseline(self):
        log = "v(vcc) = 12\nv(base) = 1.942\nv(emit) = 1.242\nv(coll) = 9.294\n"
        op = se.parse_op(log, PARAMS)
        self.assertAlmostEqual(op["ic_ma"], 1.23, places=2)
        self.assertAlmostEqual(op["vce"], 8.052, places=3)
        self.assertEqual(op["region"], "active")

    def test_parse_op_accepts_two_column_table(self):
        log = "Node        Voltage\nbase        1.942\nemit        1.242\ncoll        9.294\n"
        op = se.parse_op(log, PARAMS)
        self.assertAlmostEqual(op["vce"], 8.052, places=3)
        self.assertAlmostEqual(op["ic_ma"], 1.23, places=2)

    def test_parse_op_requires_all_nodes(self):
        with self.assertRaises(se.SpiceError):
            se.parse_op("v(base) = 1.9\n", PARAMS)

    def test_parse_ac_gain_phase_and_cutoffs(self):
        log = "\n".join([
            "Index frequency vdb(out) vp(out) vdb(base) vp(base)",
            "0 1.000e-01 -10.0 -170.0 0.0 0.0",
            "1 1.000e+00 2.0 -179.0 0.0 0.0",
            "2 1.000e+03 4.85 -180.0 0.0 0.0",
            "3 1.000e+07 4.85 -180.0 0.0 0.0",
        ])
        ac = se.parse_ac(log)
        self.assertEqual(ac["points"], 4)
        self.assertAlmostEqual(ac["midband_gain_db"], 4.85, places=2)
        self.assertAlmostEqual(ac["gain_db"][2], 4.85, places=2)
        self.assertAlmostEqual(ac["phase_deg"][2], -180.0, places=1)
        self.assertIsNone(ac["f_high_hz"])

    def test_parse_ac_reads_two_ngspice41_tables(self):
        log = "\n".join([
            "Index   frequency       vdb(out)        vp(out)",
            "0 1.000e+02 10.0 -175.0",
            "1 1.000e+03 20.0 -180.0",
            "2 1.000e+04 20.0 -180.0",
            "Index   frequency       vdb(base)       vp(base)",
            "0 1.000e+02 0.0 0.0",
            "1 1.000e+03 0.0 0.0",
            "2 1.000e+04 0.0 0.0",
        ])
        ac = se.parse_ac(log)
        self.assertEqual(ac["points"], 3)
        self.assertAlmostEqual(ac["midband_gain_db"], 20.0, places=2)
        self.assertAlmostEqual(ac["phase_deg"][1], -180.0, places=1)

    def test_parse_ac_rejects_empty_output(self):
        with self.assertRaises(se.SpiceError):
            se.parse_ac("Index frequency vdb(out) vp(out) vdb(base) vp(base)")

    def test_parse_tran_reports_inverting_phase(self):
        times = [i / 20000 for i in range(200)]
        log = "Index time v(base) v(out)\n" + "\n".join(
            f"{i} {t:.9e} {0.01 * math.sin(2 * math.pi * 1000 * t):.6e} "
            f"{-0.017 * math.sin(2 * math.pi * 1000 * t):.6e}"
            for i, t in enumerate(times)
        )
        tran = se.parse_tran(log, PARAMS)
        self.assertEqual(tran["points"], 200)
        self.assertAlmostEqual(tran["vin_peak_mv"], 10.0, places=1)
        self.assertAlmostEqual(tran["vout_peak_mv"], 17.0, places=1)
        self.assertTrue(tran["relationship"].startswith("inverting"))

    def test_parse_tran_removes_dc_offset_before_gain(self):
        times = [i / 20000 for i in range(200)]
        log = "Index time v(base) v(out)\n" + "\n".join(
            f"{i} {t:.9e} {1.95 + 0.01 * math.sin(2 * math.pi * 1000 * t):.6e} "
            f"{-0.02 * math.sin(2 * math.pi * 1000 * t):.6e}"
            for i, t in enumerate(times)
        )
        tran = se.parse_tran(log, PARAMS)
        self.assertAlmostEqual(tran["vin_peak_mv"], 10.0, places=1)
        self.assertAlmostEqual(tran["vout_peak_mv"], 20.0, places=1)
        self.assertAlmostEqual(tran["gain_db"], 20 * math.log10(2), places=1)

    def test_missing_engine_raises_spice_error(self):
        with patch.object(se, "find_ngspice", side_effect=se.SpiceError("missing")):
            with self.assertRaises(se.SpiceError):
                se.run_analysis(PARAMS, "dc")


class TestLab4Routes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_lab4_page_has_form_and_provenance(self):
        body = self.client.get("/lab4").get_data(as_text=True)
        self.assertIn('name="analysis"', body)
        self.assertIn('name="re"', body)
        self.assertIn("ngspice", body)
        self.assertIn("Provenance", body)

    def test_invalid_re_shows_error_without_running_engine(self):
        data = lab4_form(re="0")
        with patch.object(se, "run_analysis") as run:
            body = self.client.post("/lab4/run", data=data).get_data(as_text=True)
        run.assert_not_called()
        self.assertIn("Must be greater than 0.", body)
        self.assertIn("Run failed", body)
        self.assertNotIn("Midband gain", body)

    def test_engine_error_is_visible(self):
        with patch.object(se, "run_analysis", side_effect=se.SpiceError("engine down")):
            body = self.client.post("/lab4/run", data=lab4_form()).get_data(as_text=True)
        self.assertIn("engine down", body)
        self.assertNotIn("DC node voltages", body)

    def test_success_payload_is_rendered_and_embedded(self):
        fake = {
            "engine": "ngspice", "version": "test", "status": "success",
            "mode": "dc", "model": ".model QNPN NPN(BF=100)",
            "netlist": "* fake netlist\n.end\n", "log_excerpt": "...",
            "reference": "test reference",
            "provenance": "test provenance",
            "data": {
                "vb": 1.94, "ve": 1.24, "vc": 9.29, "vce": 8.05,
                "ic_ma": 1.23, "ib_ua": 12.3, "region": "active",
            },
        }
        with patch.object(se, "run_analysis", return_value=fake):
            body = self.client.post("/lab4/run", data=lab4_form()).get_data(as_text=True)
        self.assertIn("DC operating point", body)
        self.assertIn("1.2300 mA", body)
        self.assertIn("window.LAB4_SIM", body)
        self.assertIn("test provenance", body)

    def test_health_reports_missing_engine(self):
        with patch.object(se, "find_ngspice", side_effect=se.SpiceError("missing")):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.get_json()["ngspice"])


if __name__ == "__main__":
    unittest.main()
