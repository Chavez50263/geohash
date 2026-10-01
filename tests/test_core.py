import unittest

from geohash import encode, decode_bbox, decode_center, decode_range


class TestEncode(unittest.TestCase):
    def test_known_point(self):
        # Seattle ~ (-122.3, 47.6). This is a widely-used reference value.
        h = encode(-122.3, 47.6, 6)
        self.assertEqual(h, "c23nbc")

    def test_default_precision_is_12(self):
        h = encode(0, 0)
        self.assertEqual(len(h), 12)

    def test_precision_one(self):
        # Lon 0, Lat 0 sits in cell 's' (the equator/meridian cell).
        self.assertEqual(encode(0, 0, 1), "s")

    def test_precision_controls_length(self):
        for n in range(1, 13):
            self.assertEqual(len(encode(10, 20, n)), n)

    def test_upper_boundaries(self):
        # +180 and +90: encode must not raise, should land in the last cell.
        self.assertEqual(len(encode(180, 90, 6)), 6)

    def test_lower_boundaries(self):
        self.assertEqual(len(encode(-180, -90, 6)), 6)

    def test_invalid_precision_zero(self):
        with self.assertRaises(ValueError):
            encode(0, 0, 0)

    def test_invalid_precision_high(self):
        with self.assertRaises(ValueError):
            encode(0, 0, 13)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            encode(float("nan"), 0)
        with self.assertRaises(ValueError):
            encode(0, float("nan"))

    def test_inf_rejected(self):
        with self.assertRaises(ValueError):
            encode(float("inf"), 0)

    def test_out_of_range_lon(self):
        with self.assertRaises(ValueError):
            encode(200, 0)

    def test_out_of_range_lat(self):
        with self.assertRaises(ValueError):
            encode(0, 95)


class TestDecode(unittest.TestCase):
    def test_decode_bbox_center(self):
        # The cell containing (0,0) at precision 1 is 's', spanning lon
        # [-180, 0) for the first bit = 0... but verify against encode(0,0,1).
        lon_min, lat_min, lon_max, lat_max = decode_bbox("s")
        clon, clat = decode_center("s")
        self.assertEqual(clon, (lon_min + lon_max) / 2)
        self.assertEqual(clat, (lat_min + lat_max) / 2)

    def test_decode_range_structure(self):
        (lon_lo, lon_hi), (lat_lo, lat_hi) = decode_range("c22uz")
        self.assertTrue(lon_lo < lon_hi)
        self.assertTrue(lat_lo < lat_hi)

    def test_roundtrip_lon_lat(self):
        # The exact coordinates encode() was given must round-trip through
        # decode_range on the lower bound (encode picks lower-half by >= mid,
        # so the input sits at the bottom edge of the cell at full precision).
        # Floating-point bisection accumulates tiny error, so we check that
        # the coordinate lies within the decoded cell rather than asserting
        # exact equality with the lower bound.
        lon, lat = -122.3, 47.6
        h = encode(lon, lat, 12)
        (lon_lo, lon_hi), (lat_lo, lat_hi) = decode_range(h)
        self.assertTrue(lon_lo <= lon <= lon_hi)
        self.assertTrue(lat_lo <= lat <= lat_hi)

    def test_roundtrip_upper_boundaries(self):
        # +180, +90 should land at the max edge (decode_range upper bound).
        h = encode(180, 90, 12)
        (lon_lo, lon_hi), (lat_lo, lat_hi) = decode_range(h)
        self.assertEqual(lon_hi, 180)
        self.assertEqual(lat_hi, 90)

    def test_decode_uppercase_accepted(self):
        a = decode_bbox("S")
        b = decode_bbox("s")
        self.assertEqual(a, b)

    def test_decode_invalid_char(self):
        with self.assertRaises(ValueError):
            decode_bbox("abc!")

    def test_decode_empty_string(self):
        with self.assertRaises(ValueError):
            decode_bbox("")

    def test_decode_non_string(self):
        with self.assertRaises(TypeError):
            decode_bbox(123)


if __name__ == "__main__":
    unittest.main()
