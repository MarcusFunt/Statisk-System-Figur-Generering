"""Resolve semantic diagrams into a backend-neutral hierarchical scene."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from math import cos, hypot, pi, sin
from typing import TypeAlias

from .geometry import Point, Vector, add, arrow_head, interpolate, length, mul, normal, rotate, spring_points, unit
from .model import (
    AngleDimension,
    ArcMember,
    Beam,
    CoordinateAxes,
    Diagram,
    Dimension,
    Displacement,
    DistributedLoad,
    Hinge,
    Leader,
    Link,
    Moment,
    PointLoad,
    Reaction,
    SectionMarker,
    Spring,
    Support,
    SupportKind,
)
from .model import (
    Text as SemanticText,
)
from .options import RenderOptions
from .style import ElementStyle, Style
from .text_metrics import measure_text


@dataclass(frozen=True)
class Bounds:
    x0: float; x1: float; y0: float; y1: float
    @property
    def width(self) -> float: return max(self.x1-self.x0, 1e-12)
    @property
    def height(self) -> float: return max(self.y1-self.y0, 1e-12)
    def union(self, other: Bounds) -> Bounds:
        return Bounds(min(self.x0,other.x0),max(self.x1,other.x1),min(self.y0,other.y0),max(self.y1,other.y1))
    def padded(self, amount: float, vertical_ratio: float=1.0) -> Bounds:
        return Bounds(self.x0-amount,self.x1+amount,self.y0-amount*vertical_ratio,self.y1+amount*vertical_ratio)
    def intersects(self, other: Bounds, padding: float=0.0) -> bool:
        return not (self.x1+padding < other.x0 or other.x1+padding < self.x0 or self.y1+padding < other.y0 or other.y1+padding < self.y0)
    def overlap_area(self, other: Bounds) -> float:
        dx=max(0.0,min(self.x1,other.x1)-max(self.x0,other.x0)); dy=max(0.0,min(self.y1,other.y1)-max(self.y0,other.y0)); return dx*dy


def _bounds_points(points: Iterable[Point]) -> Bounds:
    pts=list(points); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return Bounds(min(xs),max(xs),min(ys),max(ys))


@dataclass(frozen=True)
class Paint:
    color: str
    width: float
    dash: tuple[float,...] | None = None
    fill: str | None = None
    opacity: float = 1.0


@dataclass(frozen=True)
class Line:
    start: Point; end: Point; paint: Paint
    def bounds(self) -> Bounds: return _bounds_points((self.start,self.end))

@dataclass(frozen=True)
class Polyline:
    points: tuple[Point,...]; paint: Paint
    def bounds(self) -> Bounds: return _bounds_points(self.points)

@dataclass(frozen=True)
class Polygon:
    points: tuple[Point,...]; paint: Paint
    def bounds(self) -> Bounds: return _bounds_points(self.points)

@dataclass(frozen=True)
class Circle:
    center: Point; radius: float; paint: Paint
    def bounds(self) -> Bounds: return Bounds(self.center[0]-self.radius,self.center[0]+self.radius,self.center[1]-self.radius,self.center[1]+self.radius)

@dataclass(frozen=True)
class Text:
    point: Point; value: str; color: str; size: float; font_family: str; align: str; valign: str; line_spacing: float; bounds_box: Bounds; opacity: float=1.0
    def bounds(self) -> Bounds: return self.bounds_box

Command: TypeAlias = Line | Polyline | Polygon | Circle | Text


@dataclass
class ElementGroup:
    element_kind: str
    element_id: int
    z_index: int
    insertion_index: int
    css_class: str | None = None
    commands: list[Command] = field(default_factory=list)
    def add(self, command: Command) -> None: self.commands.append(command)
    def bounds(self) -> Bounds | None:
        out=None
        for c in self.commands: out=c.bounds() if out is None else out.union(c.bounds())
        return out


@dataclass
class Scene:
    groups: list[ElementGroup] = field(default_factory=list)
    bounds: Bounds | None = None
    scale: float = 0.1
    @property
    def commands(self) -> list[Command]: return [c for g in self.groups for c in g.commands]
    def occupied(self) -> list[Bounds]: return [c.bounds() for c in self.commands if not isinstance(c,Text)]
    def recalculate_bounds(self) -> None:
        out=None
        for g in self.groups:
            gb=g.bounds()
            if gb is not None: out=gb if out is None else out.union(gb)
        self.bounds=out


@dataclass
class LabelSpec:
    group: ElementGroup; value: str; base: Point; default_offset: Vector; position: str; explicit_offset: Vector | None; color: str; opacity: float=1.0


def _visual_scale(diagram: Diagram, options: RenderOptions) -> float:
    if diagram.symbol_scale is not None: return diagram.symbol_scale
    x0,x1,y0,y1=diagram.extent(); xspan=max(x1-x0,1.0); yspan=max(y1-y0,1.0)
    aspect=xspan/yspan
    width=options.width; height=options.height
    if width is None: width=height*aspect  # type: ignore[operator]
    if height is None: height=width/aspect
    world_per_in=max(xspan/width,yspan/height)
    return world_per_in*0.20


def _paint(style: Style, override: ElementStyle | None, *, color: str, width: float, dash: tuple[float,...] | None=None, fill: str | None=None) -> Paint:
    if override:
        color=override.color or color; width=override.line_width or width; dash=override.dash if override.dash is not None else dash; fill=override.fill if override.fill is not None else fill; opacity=1.0 if override.opacity is None else override.opacity
    else: opacity=1.0
    return Paint(color,width,dash,fill,opacity)


def _text_bounds(point: Point, value: str, scale: float, style: Style, align: str, valign: str, multiplier: float=1.0) -> Bounds:
    metrics=measure_text(value,style.font_family,style.text_size*multiplier,style.line_spacing)
    world_per_point=scale*0.068/style.text_size
    width=metrics.width_points*world_per_point; height=metrics.height_points*world_per_point
    x0=point[0]-{"left":0.0,"center":width/2,"right":width}[align]
    y0=point[1]-{"top":height,"center":height/2,"bottom":0.0}[valign]
    return Bounds(x0,x0+width,y0,y0+height)


def _text_command(point: Point,value: str,*,color: str,style: Style,scale: float,align: str="center",valign: str="bottom",multiplier: float=1.0,opacity: float=1.0) -> Text:
    return Text(point,value,color,style.text_size*multiplier,style.font_family,align,valign,style.line_spacing,_text_bounds(point,value,scale,style,align,valign,multiplier),opacity)


def _arrow(group: ElementGroup,start: Point,vector: Vector,*,paint: Paint,preferred_head: float) -> None:
    arrow_length=length(vector); end=add(start,vector); group.add(Line(start,end,paint))
    head=min(preferred_head,arrow_length*0.38)
    if head <= 0: return
    left,right=arrow_head(end,vector,head); group.add(Polygon((end,left,right),Paint(paint.color,max(paint.width*0.7,0.1),fill=paint.color,opacity=paint.opacity)))


def _ground(group: ElementGroup,center: Point,tangent: Vector,down: Vector,width: float,style: Style,override: ElementStyle | None) -> None:
    p=_paint(style,override,color=style.ground,width=1.2)
    group.add(Line(add(center,mul(tangent,-width/2)),add(center,mul(tangent,width/2)),p))
    hp=_paint(style,override,color=style.ground,width=0.9)
    for ratio in (-0.38,-0.13,0.13,0.38):
        base=add(center,mul(tangent,width*ratio)); group.add(Line(base,add(add(base,mul(tangent,-width*0.10)),mul(down,width*0.14)),hp))


def _support(group: ElementGroup,s: Support,scale: float,style: Style,background: str | None) -> tuple[Point,Vector]:
    tangent=rotate((1,0),s.angle); down=rotate((0,-1),s.angle); height,width=scale*1.55,scale*1.75
    ink=_paint(style,s.style,color=style.ink,width=1.5)
    if s.kind is SupportKind.FIXED:
        base={"left":(-1.0,0.0),"right":(1.0,0.0),"top":(0.0,1.0),"bottom":(0.0,-1.0)}[s.fixed_side]
        direction=rotate(base,s.angle); cross=normal(direction); end=add(s.point,mul(direction,scale*0.2)); half=scale*1.15
        group.add(Line(add(end,mul(cross,-half)),add(end,mul(cross,half)),_paint(style,s.style,color=style.ink,width=style.beam_width+0.9)))
        hatch=_paint(style,s.style,color=style.ground,width=1.0)
        for marker in (-0.85,-0.45,-0.05,0.35,0.75):
            root=add(end,mul(cross,scale*marker)); group.add(Line(root,add(add(root,mul(cross,scale*0.22)),mul(direction,scale*0.30)),hatch))
        return s.point,direction
    if s.kind is SupportKind.SPRING:
        end=add(s.point,mul(down,height*1.35)); group.add(Polyline(tuple(spring_points(s.point,down,height*1.35,width*0.22)),_paint(style,s.style,color=style.ink,width=1.3))); _ground(group,end,tangent,down,width*1.25,style,s.style); return s.point,down
    if s.kind in {SupportKind.GUIDED,SupportKind.SLIDER}:
        center=add(s.point,mul(down,height*0.35)); box_w,box_h=width*0.8,scale*0.52
        corners=(add(add(center,mul(tangent,-box_w/2)),mul(down,-box_h/2)),add(add(center,mul(tangent,box_w/2)),mul(down,-box_h/2)),add(add(center,mul(tangent,box_w/2)),mul(down,box_h/2)),add(add(center,mul(tangent,-box_w/2)),mul(down,box_h/2)))
        group.add(Polygon(corners,Paint(ink.color,ink.width,fill=background,opacity=ink.opacity)))
        rail=add(center,mul(down,box_h)); _ground(group,rail,tangent,down,width,style,s.style)
        if s.kind is SupportKind.GUIDED:
            for sign in (-0.32,0.32): group.add(Circle(add(center,mul(tangent,box_w*sign)),scale*0.13,Paint(ink.color,1.0,fill=background,opacity=ink.opacity)))
        return s.point,down
    left=add(add(s.point,mul(down,height)),mul(tangent,-width/2)); right=add(add(s.point,mul(down,height)),mul(tangent,width/2)); group.add(Polygon((s.point,right,left),Paint(ink.color,ink.width,fill=s.style.fill if s.style and s.style.fill is not None else None,opacity=ink.opacity)))
    ground=add(s.point,mul(down,height))
    if s.kind is SupportKind.ROLLER:
        radius=scale*0.28
        for sign in (-0.28,0.28): group.add(Circle(add(add(ground,mul(tangent,width*sign)),mul(down,radius)),radius,Paint(ink.color,1.25,fill=background,opacity=ink.opacity)))
        _ground(group,add(ground,mul(down,radius*2)),tangent,down,width*1.35,style,s.style)
    else: _ground(group,ground,tangent,down,width*1.25,style,s.style)
    return s.point,down


def _clip_segment(start: Point,end: Point,circles: list[tuple[Point,float]]) -> list[tuple[Point,Point]]:
    # subtract circle-interior parameter intervals from a segment
    dx,dy=end[0]-start[0],end[1]-start[1]; seg2=dx*dx+dy*dy
    if seg2==0:return []
    intervals: list[tuple[float,float]]=[]
    for (cx,cy),r in circles:
        fx,fy=start[0]-cx,start[1]-cy; a=seg2; b=2*(fx*dx+fy*dy); c=fx*fx+fy*fy-r*r; disc=b*b-4*a*c
        if disc<=0: continue
        root=disc**0.5; t0=max(0.0,(-b-root)/(2*a)); t1=min(1.0,(-b+root)/(2*a))
        if t0<t1: intervals.append((t0,t1))
    if not intervals:return [(start,end)]
    intervals.sort(); merged: list[tuple[float, float]]=[]
    for lo,hi in intervals:
        if merged and lo<=merged[-1][1]: merged[-1]=(merged[-1][0],max(merged[-1][1],hi))
        else: merged.append((lo,hi))
    keep=[]; cursor=0.0
    for lo,hi in merged:
        if lo>cursor: keep.append((cursor,lo))
        cursor=max(cursor,hi)
    if cursor<1: keep.append((cursor,1.0))
    return [((start[0]+dx*a,start[1]+dy*a),(start[0]+dx*b,start[1]+dy*b)) for a,b in keep if b-a>1e-9]


def _kind_name(e: object) -> str:
    return {
        Beam:"beam",ArcMember:"arc-member",Support:"support",Hinge:"hinge",PointLoad:"point-load",DistributedLoad:"distributed-load",Moment:"moment",Reaction:"reaction",Dimension:"dimension",AngleDimension:"angle-dimension",SemanticText:"text",Spring:"spring",Link:"link",CoordinateAxes:"axes",SectionMarker:"section-marker",Leader:"leader",Displacement:"displacement"
    }[type(e)]


def _anchor_offset(position: str,scale: float) -> Vector:
    d=scale*0.8; return {"above":(0,d),"below":(0,-d),"left":(-d,0),"right":(d,0),"center":(0,0)}[position]


def _label_candidates(spec: LabelSpec,scale: float,style: Style) -> list[tuple[Point,str,Bounds,float]]:
    if spec.explicit_offset is not None: raw=[(add(spec.base,spec.explicit_offset),"bottom",0.0)]
    elif spec.position!="auto":
        valign="center" if spec.position in {"left","right","center"} else ("bottom" if spec.position=="above" else "top")
        raw=[(add(spec.base,_anchor_offset(spec.position,scale)),valign,0.0)]
    else:
        raw=[(add(spec.base,spec.default_offset),"bottom",0.0),(add(spec.base,_anchor_offset("above",scale)),"bottom",0.15),(add(spec.base,_anchor_offset("right",scale)),"center",0.25),(add(spec.base,_anchor_offset("left",scale)),"center",0.25),(add(spec.base,_anchor_offset("below",scale)),"top",0.35),(add(spec.base,(scale*.95,scale*.95)),"center",0.45),(add(spec.base,(-scale*.95,scale*.95)),"center",0.45),(add(spec.base,(scale*.95,-scale*.95)),"center",0.55),(add(spec.base,(-scale*.95,-scale*.95)),"center",0.55)]
    return [(p,v,_text_bounds(p,spec.value,scale,style,"center",v),pref) for p,v,pref in raw]


def _place_labels(scene: Scene,specs: list[LabelSpec],style: Style,options: RenderOptions) -> None:
    if not specs:return
    static=scene.occupied(); candidate_sets=[_label_candidates(s,scene.scale,style) for s in specs]
    selected=[0]*len(specs)
    if options.avoid_label_collisions:
        def score(i: int,j: int,current: list[int]) -> float:
            _,_,box,pref=candidate_sets[i][j]; symbol=sum(box.overlap_area(b)>0 for b in static); label_overlap=0
            for k,choice in enumerate(current):
                if k==i: continue
                if box.intersects(candidate_sets[k][choice][2],scene.scale*.05): label_overlap+=1
            return 100*symbol+50*label_overlap+10*pref
        for _ in range(6):
            changed=False
            for i,cands in enumerate(candidate_sets):
                best=min(range(len(cands)),key=lambda j:(score(i,j,selected),j))
                if best!=selected[i]: selected[i]=best; changed=True
            if not changed: break
    for spec,cands,choice in zip(specs,candidate_sets,selected):
        p,v,_,_=cands[choice]; spec.group.add(_text_command(p,spec.value,color=spec.color,style=style,scale=scene.scale,valign=v,opacity=spec.opacity))


def layout_scene(diagram: Diagram, *, style: Style, options: RenderOptions) -> Scene:
    scale=_visual_scale(diagram,options); scene=Scene(scale=scale); labels: list[LabelSpec]=[]
    # stable per-kind semantic IDs based on insertion order, independent of z order
    counts: dict[str,int]={}; identity: dict[int,tuple[str,int,int]]={}
    for insertion,e in enumerate(diagram.elements):
        kind=_kind_name(e); idx=counts.get(kind,0); counts[kind]=idx+1; identity[id(e)]=(kind,idx,insertion)
    hinge_circles=[(e.point,(e.radius or scale*.32)*1.08) for e in diagram.elements if isinstance(e,Hinge)]
    groups: dict[int,ElementGroup]={}
    for e in sorted(diagram.elements,key=lambda x:(x.z_index,identity[id(x)][2])):
        kind,idx,insertion=identity[id(e)]; g=ElementGroup(kind,idx,e.z_index,insertion,getattr(e,"css_class",None)); groups[id(e)]=g; scene.groups.append(g)
        override=getattr(e,"style",None)
        if isinstance(e,Beam):
            paint=_paint(style,override,color=style.ink,width=style.beam_width if e.kind=="beam" else style.bar_width,dash=style.beam_dash)
            for a,b in _clip_segment(e.start,e.end,hinge_circles): g.add(Line(a,b,paint))
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.start,e.end,.5),mul(normal((e.end[0]-e.start[0],e.end[1]-e.start[1])),scale*style.label_scale),e.label_position,e.label_offset,paint.color,paint.opacity))
        elif isinstance(e,ArcMember):
            angles=[e.start_angle+(e.end_angle-e.start_angle)*i/32 for i in range(33)]; pts=tuple((e.center[0]+e.radius*cos(a*pi/180),e.center[1]+e.radius*sin(a*pi/180)) for a in angles); paint=_paint(style,override,color=style.ink,width=style.beam_width if e.kind=="beam" else style.bar_width,dash=style.beam_dash); g.add(Polyline(pts,paint))
            if e.label: labels.append(LabelSpec(g,e.label,pts[len(pts)//2],(0,scale*.6),"auto",None,paint.color,paint.opacity))
        elif isinstance(e,Support):
            base,direction=_support(g,e,scale,style,options.background)
            if e.label: labels.append(LabelSpec(g,e.label,base,mul(direction,scale*3.2),e.label_position,e.label_offset,(override.color if override and override.color else style.ink),1.0 if not override or override.opacity is None else override.opacity))
        elif isinstance(e,Hinge):
            radius=e.radius or scale*.32; p=_paint(style,override,color=style.ink,width=1.35,fill=options.background); g.add(Circle(e.point,radius,p))
            if e.label: labels.append(LabelSpec(g,e.label,e.point,(scale*.55,scale*.55),e.label_position,e.label_offset,p.color,p.opacity))
        elif isinstance(e,DistributedLoad):
            direction=unit(e.direction); base_length=hypot(e.end[0]-e.start[0],e.end[1]-e.start[1]); count=e.count or max(2,min(25,round(base_length/(scale*style.distributed_load_spacing))+1)); color=(override.color if override and override.color else (e.color or style.load)); paint=_paint(style,override,color=color,width=style.force_width,dash=style.load_dash)
            h0=e.start_height if e.start_height is not None else (e.offset or scale*3.0); h1=e.end_height if e.end_height is not None else (e.offset or scale*3.0); top_a=add(e.start,mul(direction,-h0)); top_b=add(e.end,mul(direction,-h1)); g.add(Line(top_a,top_b,_paint(style,override,color=color,width=1.0,dash=style.load_dash)))
            for i in range(count):
                f=i/(count-1); base=interpolate(e.start,e.end,f); h=h0+(h1-h0)*f
                if h>1e-12: _arrow(g,add(base,mul(direction,-h)),mul(direction,h),paint=paint,preferred_head=scale*style.arrow_head_scale*.92)
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(top_a,top_b,.5),mul(normal(direction),scale*.45),e.label_position,e.label_offset,color,paint.opacity))
        elif isinstance(e,PointLoad):
            color=(override.color if override and override.color else (e.color or style.load)); paint=_paint(style,override,color=color,width=style.force_width); _arrow(g,e.point,e.vector,paint=paint,preferred_head=scale*style.arrow_head_scale)
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.point,add(e.point,e.vector),.53),mul(normal(e.vector),scale*.48),e.label_position,e.label_offset,color,paint.opacity))
        elif isinstance(e,Reaction):
            color=(override.color if override and override.color else (e.color or style.reaction)); paint=_paint(style,override,color=color,width=style.force_width); _arrow(g,e.point,e.vector,paint=paint,preferred_head=scale*style.arrow_head_scale)
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.point,add(e.point,e.vector),.53),mul(normal(e.vector),scale*.48),e.label_position,e.label_offset,color,paint.opacity))
        elif isinstance(e,Moment):
            radius=e.radius or scale*1.05; color=(override.color if override and override.color else (e.color or style.load)); paint=_paint(style,override,color=color,width=style.force_width); start_a,end_a=((315,35) if e.clockwise else (35,315)); angles=[start_a+(end_a-start_a)*i/24 for i in range(25)]; pts=tuple((e.point[0]+radius*cos(a*pi/180),e.point[1]+radius*sin(a*pi/180)) for a in angles); g.add(Polyline(pts,paint)); theta=end_a*pi/180; direction=(sin(theta),-cos(theta)) if e.clockwise else (-sin(theta),cos(theta)); _arrow(g,add(pts[-1],mul(direction,-scale*.55)),mul(direction,scale*.55),paint=paint,preferred_head=scale*style.arrow_head_scale*.92)
            if e.label: labels.append(LabelSpec(g,e.label,e.point,(radius+scale*.45,radius*.35),e.label_position,e.label_offset,color,paint.opacity))
        elif isinstance(e,Dimension):
            nv=normal((e.end[0]-e.start[0],e.end[1]-e.start[1])); start=add(e.start,mul(nv,e.offset)); end=add(e.end,mul(nv,e.offset)); paint=_paint(style,override,color=style.dimension,width=1.0,dash=style.dimension_dash); g.add(Line(start,end,paint))
            sign=1 if e.offset>=0 else -1
            if e.extension_lines and abs(e.offset)>1e-12:
                for original,dimpt in ((e.start,start),(e.end,end)):
                    a=add(original,mul(nv,e.extension_gap*sign)); b=add(dimpt,mul(nv,e.extension_overrun*sign)); g.add(Line(a,b,paint))
            tick=scale*.22
            for point in (start,end):
                if e.endpoint_style=="tick": g.add(Line(add(point,mul(nv,-tick)),add(point,mul(nv,tick)),paint))
                elif e.endpoint_style=="slash":
                    d=unit((e.end[0]-e.start[0],e.end[1]-e.start[1])); sl=unit((d[0]+nv[0],d[1]+nv[1])); g.add(Line(add(point,mul(sl,-tick)),add(point,mul(sl,tick)),paint))
                elif e.endpoint_style=="dot": g.add(Circle(point,tick*.45,Paint(paint.color,paint.width,fill=paint.color,opacity=paint.opacity)))
            if e.endpoint_style=="arrow":
                d=(end[0]-start[0],end[1]-start[1]); _arrow(g,add(start,mul(unit(d),scale*.5)),mul(unit(d),-scale*.5),paint=paint,preferred_head=scale*.16); _arrow(g,add(end,mul(unit(d),-scale*.5)),mul(unit(d),scale*.5),paint=paint,preferred_head=scale*.16)
            labels.append(LabelSpec(g,e.label,interpolate(start,end,.5),mul(nv,scale*.38),e.label_position,e.label_offset,paint.color,paint.opacity))
        elif isinstance(e,AngleDimension):
            start_angle,end_angle=e.start_angle,e.end_angle
            if e.clockwise and end_angle>start_angle: end_angle-=360
            if not e.clockwise and end_angle<start_angle: end_angle+=360
            angles=[start_angle+(end_angle-start_angle)*i/28 for i in range(29)]; pts=tuple((e.center[0]+e.radius*cos(a*pi/180),e.center[1]+e.radius*sin(a*pi/180)) for a in angles); paint=_paint(style,override,color=style.dimension,width=1.0,dash=style.dimension_dash); g.add(Polyline(pts,paint)); mid=(start_angle+end_angle)/2; labels.append(LabelSpec(g,e.label,(e.center[0]+(e.radius+scale*.35)*cos(mid*pi/180),e.center[1]+(e.radius+scale*.35)*sin(mid*pi/180)),(0,0),"center",None,paint.color,paint.opacity))
        elif isinstance(e,SemanticText):
            p=_paint(style,override,color=style.ink,width=1.0); g.add(_text_command(e.point,e.value,color=p.color,style=style,scale=scale,align=e.align,valign=e.valign,opacity=p.opacity))
        elif isinstance(e,Spring):
            v=(e.end[0]-e.start[0],e.end[1]-e.start[1]); p=_paint(style,override,color=style.ink,width=1.3); g.add(Polyline(tuple(spring_points(e.start,v,length(v),scale*.32)),p));
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.start,e.end,.5),mul(normal(v),scale*.55),"auto",None,p.color,p.opacity))
        elif isinstance(e,Link):
            v=(e.end[0]-e.start[0],e.end[1]-e.start[1]); p=_paint(style,override,color=style.ink,width=style.bar_width); g.add(Line(e.start,e.end,p)); r=scale*.18; g.add(Circle(e.start,r,Paint(p.color,1.1,fill=options.background,opacity=p.opacity))); g.add(Circle(e.end,r,Paint(p.color,1.1,fill=options.background,opacity=p.opacity)))
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.start,e.end,.5),mul(normal(v),scale*.5),"auto",None,p.color,p.opacity))
        elif isinstance(e,CoordinateAxes):
            p=_paint(style,override,color=style.dimension,width=1.0); _arrow(g,e.origin,e.x_vector,paint=p,preferred_head=scale*.22); _arrow(g,e.origin,e.y_vector,paint=p,preferred_head=scale*.22); x_end=add(e.origin,e.x_vector); y_end=add(e.origin,e.y_vector); g.add(_text_command(add(x_end,mul(unit(e.x_vector),scale*.18)),e.x_label,color=p.color,style=style,scale=scale,valign="center",opacity=p.opacity)); g.add(_text_command(add(y_end,mul(unit(e.y_vector),scale*.18)),e.y_label,color=p.color,style=style,scale=scale,opacity=p.opacity))
        elif isinstance(e,SectionMarker):
            d=unit(e.direction); n=normal(d); p=_paint(style,override,color=style.dimension,width=1.2); a=add(e.point,mul(n,-scale*.8)); b=add(e.point,mul(n,scale*.8)); g.add(Line(a,b,p)); _arrow(g,add(a,mul(d,-scale*.35)),mul(d,scale*.35),paint=p,preferred_head=scale*.14); _arrow(g,add(b,mul(d,-scale*.35)),mul(d,scale*.35),paint=p,preferred_head=scale*.14)
            if e.label: labels.append(LabelSpec(g,e.label,e.point,mul(d,scale*.6),"auto",None,p.color,p.opacity))
        elif isinstance(e,Leader):
            p=_paint(style,override,color=style.dimension,width=1.0); v=(e.target[0]-e.text_point[0],e.target[1]-e.text_point[1]); _arrow(g,e.text_point,v,paint=p,preferred_head=scale*.18); g.add(_text_command(e.text_point,e.text,color=p.color,style=style,scale=scale,align="left",valign="bottom",opacity=p.opacity))
        elif isinstance(e,Displacement):
            p=_paint(style,override,color=style.reaction,width=style.force_width); _arrow(g,e.point,e.vector,paint=p,preferred_head=scale*style.arrow_head_scale); end=add(e.point,e.vector); n=normal(e.vector); g.add(Line(add(end,mul(n,-scale*.22)),add(end,mul(n,scale*.22)),p))
            if e.label: labels.append(LabelSpec(g,e.label,interpolate(e.point,end,.55),mul(n,scale*.45),"auto",None,p.color,p.opacity))
    scene.recalculate_bounds(); _place_labels(scene,labels,style,options); scene.recalculate_bounds()
    content=scene.bounds or Bounds(-1,1,-1,1)
    if diagram.title:
        g=ElementGroup("title",0,10_000,len(scene.groups),None); point=((content.x0+content.x1)/2,content.y1+scale*1.05); g.add(_text_command(point,diagram.title,color=style.ink,style=style,scale=scale,multiplier=1.25)); scene.groups.append(g); scene.recalculate_bounds(); content=scene.bounds or content
    margin=max(scale*options.padding,scale*.75); scene.bounds=content.padded(margin,1.15)
    scene.groups.sort(key=lambda g:(g.z_index,g.insertion_index))
    return scene


def figure_size(bounds: Bounds,options: RenderOptions) -> tuple[float,float]:
    aspect=bounds.width/bounds.height
    if options.width is not None and options.height is not None:return options.width,options.height
    if options.width is not None:return options.width,options.width/aspect
    assert options.height is not None
    return options.height*aspect,options.height
