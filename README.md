# geohash

Encode and decode geohashes using the standard base32 alphabet. Zero dependencies, standard library only.

```python
from geohash import encode, decode_bbox, decode_center, decode_range

h = encode(-122.3, 47.6, 12)        # -> "c22uzn5h2x2e"
lon_min, lat_min, lon_max, lat_max = decode_bbox(h)
clon, clat = decode_center(h)
(lon_rng, lat_rng) = decode_range(h)   # ((lon_min, lon_max), (lat_min, lat_max))
```

## Why

A small, dependency-free encoder/decoder for code that needs geohash strings without pulling in a full GIS stack. Precision is configurable (1-12 characters); 12 gives roughly sub-meter resolution, which is enough for most coordinate use cases and is the default.

## Edge cases

Decoding returns a **bounding box**, not a point. `decode_center` returns the box's midpoint, which is only an approximation of the original coordinate. If you need exact round-tripping, use `decode_range`: at precision 12, the lower bound of the box equals the coordinate passed to `encode` (because `encode` chooses the upper half when the coordinate is `>=` the midpoint, so the coordinate lands on the lower edge of the selected cell).

Latitude is clamped to [-90, 90] and longitude to [-180, 180]; out-of-range inputs raise `ValueError`. NaN and infinities are rejected. Input hashes are case-insensitive and leading/trailing whitespace is stripped.
