from statics_diagrams import (
    DEFAULT_STYLE,
    Diagram,
    ElementStyle,
    RenderOptions,
    SupportKind,
    render_matplotlib,
    render_svg,
)

options: RenderOptions = RenderOptions(width=6.0, background=None)
diagram: Diagram = (
    Diagram(title="Typed example")
    .beam((0.0, 0.0), (4.0, 0.0), style=ElementStyle(line_width=2.0))
    .support((0.0, 0.0), SupportKind.PIN)
    .force(at=(2.0, 0.0), direction=(0.0, -1.0), length=1.0)
)
svg: str = render_svg(diagram, style=DEFAULT_STYLE, options=options).content
figure = render_matplotlib(diagram, options=options)
assert svg
assert figure is not None
