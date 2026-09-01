# Visual review: renderer quality revision

The visual smoke test in `tests/test_visual_gallery.py` creates PNG and SVG
output for five diagrams:

1. Simply supported beam with point, distributed, and reaction loads.
2. Inclined member with a rotated fixed support.
3. A standalone applied moment.
4. A dense annotated truss.
5. A portal frame using the print theme.

## Issues found during review and corrected

- Support labels could overlap roller circles and ground hatching. Their
  default clearance is now based on the full support envelope.
- A truss-joint label could sit on a point-load arrow. The automatic label
  resolver now evaluates cardinal and diagonal alternatives, using a
  centre-aligned side label when that is clearer.
- The example's explicit beam label and moment location competed with force
  graphics. The test gallery now demonstrates their intended anchor controls
  instead of encoding a collision as a reference image.
- Creating a Matplotlib figure could select a Tk backend and fail in a
  headless environment. The renderer now creates an Agg-backed figure.

## Final inspection

All five figures have complete framing, readable titles, distinguishable load
and reaction colours where applicable, and no observed label/symbol overlap.
The moment-only output is deliberately close to square because it preserves an
equal coordinate aspect around a circular moment marker; it is not clipped.

## Residual limitation

An explicit `label_offset` or non-`"auto"` `label_position` is treated as an
authorial placement choice and is not moved by collision avoidance. Use
`label_position="auto"` when the library should choose a clear alternative.
