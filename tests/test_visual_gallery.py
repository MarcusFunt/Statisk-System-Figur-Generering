from statics_diagrams import (
    COLORBLIND_STYLE,
    PRINT_STYLE,
    Diagram,
    RenderOptions,
    SupportKind,
    render_matplotlib,
    render_svg,
)


def _cases():
    return {
        'beam': Diagram(title='Simply supported beam').beam((0,0),(8,0),label='AB').support((0,0),SupportKind.PIN,label='A').support((8,0),SupportKind.ROLLER,label='B').force(at=(2.8,0),direction=(0,-1),length=1.6,label='P').udl((4.6,0),(7.2,0),direction=(0,-1),height=1.2,label='q').reaction((0,0),(0,1.1),label='Aᵧ').reaction((8,0),(0,1.1),label='Bᵧ').dimension((0,-1.5),(8,-1.5),'L = 8 m'),
        'rotated': Diagram(title='Inclined fixed support').beam((0,0),(5,2.2),label='Member').support((0,0),SupportKind.FIXED,fixed_side='left',angle=30,label='A').support((5,2.2),SupportKind.ROLLER,angle=30,label='B').force(at=(2.5,1.1),direction=(-.3,-1),length=1.4,label='F'),
        'moment': Diagram(title='Applied moment').moment((10,10),radius=2,clockwise=True,label='M'),
        'dense': Diagram(title='Annotated truss').beam((0,0),(3,2.3),kind='bar').beam((3,2.3),(6,0),kind='bar').beam((0,0),(6,0),kind='bar').hinge((0,0),label='A').hinge((3,2.3),label='C').hinge((6,0),label='B').support((0,0),SupportKind.PIN).support((6,0),SupportKind.ROLLER).force(at=(3,2.3),direction=(0,-1),length=1.6,label='P',label_position='right').dimension((0,-.9),(6,-.9),'6 m'),
        'portal': Diagram(title='Portal-frame load case').beam((0,0),(0,4)).beam((0,4),(6,4)).beam((6,4),(6,0)).support((0,0),SupportKind.FIXED,fixed_side='bottom',label='A').support((6,0),SupportKind.PIN,label='B').udl((.6,4),(5.4,4),direction=(0,-1),height=.9,label='q').moment((5,5.7),label='M'),
    }

def test_visual_gallery_generates_five_figures(tmp_path):
    options=RenderOptions(width=7,dpi=180,background='white')
    for name,d in _cases().items():
        style=PRINT_STYLE if name=='portal' else COLORBLIND_STYLE; fig=render_matplotlib(d,style=style,options=options); png=tmp_path/f'{name}.png'; svg=tmp_path/f'{name}.svg'; fig.savefig(png,dpi=options.dpi,transparent=False); render_svg(d,style=style,options=options).save(svg); assert png.stat().st_size>1000; assert svg.read_text().count('data-kind')>=1
