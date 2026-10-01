"""Geohash encode/decode using the standard base32 alphabet.

Decoding returns a bounding box (min/max lon-lat) rather than a single point.
The center of that box is available separately. Floats are compared by
exact string reconstruction, so decode_range(encode(lon, lat, n), n)
round-trips for the coordinates that encode() was given.
"""

# Standard geohash base32 alphabet (lowercase). The alphabet is a spec-defined
# ordering, not something derived; hardcoding it is the correct choice.
_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

# Map char -> 5-bit value. Used during decode.
_DECODE = {c: i for i, c in enumerate(_BASE32)}

# Lon/lat range. Geohash covers the whole globe; poles are at +-90 latitude.
_LON = (-180.0, 180.0)
_LAT = (-90.0, 90.0)


def encode(lon: float, lat: float, precision: int = 12) -> str:
    """Encode a coordinate into a geohash string.

    Args:
        lon: Longitude in degrees [-180, 180].
        lat: Latitude in degrees [-90, 90].
        precision: Number of base32 characters in the output (1..12).

    Returns:
        A lowercase geohash string of exactly `precision` characters.

    Raises:
        ValueError: If precision is out of range or coordinates are NaN/inf
            or outside their valid domain.
    """
    if not isinstance(precision, int) or isinstance(precision, bool):
        raise TypeError("precision must be an int")
    if precision < 1 or precision > 12:
        raise ValueError("precision must be in [1, 12]")

    # math.isnan rejects non-numbers (strings, None) via the same TypeError path
    # as a plain comparison would, and handles NaN/inf explicitly.
    import math
    for name, v, (lo, hi) in (("lon", lon, _LON), ("lat", lat, _LAT)):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError(f"{name} must be a real number")
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"{name} must be finite")
        if not (lo <= v <= hi):
            raise ValueError(f"{name} must be in [{lo}, {hi}]")

    chars = []
    bit = 0
    # 0 = longitude bit, 1 = latitude bit. Start with longitude, alternate.
    ch = 0
    lon_lo, lon_hi = _LON
    lat_lo, lat_hi = _LAT
    even = True

    while len(chars) < precision:
        if even:
            mid = (lon_lo + lon_hi) / 2
            if lon >= mid:
                ch = (ch << 1) | 1
                lon_lo = mid
            else:
                ch = (ch << 1)
                lon_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if lat >= mid:
                ch = (ch << 1) | 1
                lat_lo = mid
            else:
                ch = (ch << 1)
                lat_hi = mid

        even = not even
        bit += 1
        if bit == 5:
            chars.append(_BASE32[ch])
            bit = 0
            ch = 0

    return "".join(chars)


def decode_bbox(hashstr: str):
    """Decode a geohash into its bounding box.

    Args:
        hashstr: A geohash string (lowercase or uppercase).

    Returns:
        A tuple (lon_min, lat_min, lon_max, lat_max).

    Raises:
        ValueError: If the string is empty or contains non-base32 characters.
    """
    s = _normalize(hashstr)
    if not s:
        raise ValueError("hash must be non-empty")
    if any(c not in _DECODE for c in s):
        raise ValueError("hash contains invalid base32 characters")

    lon_lo, lon_hi = _LON
    lat_lo, lat_hi = _LAT
    even = True

    for c in s:
        val = _DECODE[c]
        for i in range(4, -1, -1):
            bit = (val >> i) & 1
            if even:
                mid = (lon_lo + lon_hi) / 2
                if bit:
                    lon_lo = mid
                else:
                    lon_hi = mid
            else:
                mid = (lat_lo + lat_hi) / 2
                if bit:
                    lat_lo = mid
                else:
                    lat_hi = mid
            even = not even

    return (lon_lo, lat_lo, lon_hi, lat_hi)


def decode_center(hashstr: str):
    """Decode a geohash to the center of its bounding box.

    Returns a tuple (lon, lat). The center is exact only to the cell's
    resolution; for most uses, decode_range is more informative.
    """
    lon_min, lat_min, lon_max, lat_max = decode_bbox(hashstr)
    return ((lon_min + lon_max) / 2, (lat_min + lat_max) / 2)


def decode_range(hashstr: str):
    """Decode a geohash into inclusive (lon_min, lon_max) and (lat_min, lat_max) ranges.

    Returns ((lon_min, lon_max), (lat_min, lat_max)).
    """
    lon_min, lat_min, lon_max, lat_max = decode_bbox(hashstr)
    return ((lon_min, lon_max), (lat_min, lat_max))


def _normalize(hashstr: str) -> str:
    if not isinstance(hashstr, str):
        raise TypeError("hash must be a string")
    return hashstr.lower().strip()
