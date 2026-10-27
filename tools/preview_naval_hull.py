#!/usr/bin/env python3
"""Render actual exported waterjet geometry and the separate hydrostatic envelope.

The close-up clips existing triangles at a plane. It does not add a fictional
cut cap or alter any source shape. Photos carry the full visible-mesh revision.
"""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'australis-2030'),str(ROOT/'tools'),str(ROOT)]
from build_current_game_preview import load_current_mesh
from generate_source_models import Mesh
from build import COLORS
from render_current_views import _render
import build_3d_viewer as viewer
from audit_naval_hull import read_groups,PACKAGE

RELEASE='Australis-v0.8.2'


def clip_triangles(triangles,zmax=-145.):
    """Clip real triangle polygons to the aft halfspace, without capping it."""
    result=[]
    for name,tri,mat in triangles:
        polygon=list(np.asarray(tri,float));clipped=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            ina,inb=a[2]<=zmax,b[2]<=zmax
            if ina:clipped.append(a)
            if ina!=inb:
                t=(zmax-a[2])/(b[2]-a[2]);clipped.append(a+(b-a)*t)
        for j in range(1,len(clipped)-1):
            triangle=np.asarray([clipped[0],clipped[j],clipped[j+1]])
            if np.linalg.norm(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]))>1e-9:
                result.append((name,triangle,mat))
    assert result,'No stern triangles survived cropping'
    return result


def lines_plan(groups,data,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    v,_=groups['HydrostaticEnvelope'];zs=sorted(set(round(float(z),5) for z in v[:,2]))
    bg='#101e2a';fg='#dce9ec';line='#7ad0df';muted='#9bb4c0'
    plt.rcParams.update({'font.family':'DejaVu Sans','text.color':fg,'axes.labelcolor':muted,'xtick.color':muted,'ytick.color':muted,'axes.edgecolor':'#46616d'})
    fig,axes=plt.subplots(3,1,figsize=(17,10),facecolor=bg,gridspec_kw={'height_ratios':[1.2,1,1.2]})
    for ax in axes:ax.set_facecolor(bg);ax.grid(alpha=.14,color=muted)
    profile,plan,body=axes
    yy=[];bb=[]
    for z in zs:
        section=v[np.abs(v[:,2]-z)<.0001];yy.append(section[:,1].min());bb.append(section[:,0].max())
    profile.fill_between(zs,yy,0,color='#254a5d');profile.plot(zs,yy,color=line,lw=2);profile.axhline(0,color='#dce9ec',lw=1)
    from waterjet_geometry import JET_CENTRES,OUTLET_BORE
    x,y,z=JET_CENTRES[0]
    profile.add_patch(plt.Circle((z,y),OUTLET_BORE/2,fill=False,color='#dfb77c',lw=1.5))
    profile.set(xlim=(-190,186),ylim=(-13,2),ylabel='Height relative to WL (m)',title='SIDE PROFILE · broader, fuller stern · nozzle bore in gold')
    profile.set_aspect('equal',adjustable='box')
    plan.fill_between(zs,-np.asarray(bb),bb,color='#254a5d');plan.plot(zs,bb,color=line,lw=2);plan.plot(zs,-np.asarray(bb),color=line,lw=2);plan.axhline(0,color='#b2cbd2',lw=.8,ls='--')
    for x,y,z in JET_CENTRES:plan.plot([z-2,z+1],[x,x],color='#dfb77c',lw=2)
    plan.set(xlim=(-190,186),ylim=(-23,23),ylabel='Transverse X (m)',title='WATERLINE PLAN · mirrored centreline · eight provisional jet axes in gold')
    plan.set_aspect('equal',adjustable='box')
    selected=[min(zs,key=lambda z:abs(z-target)) for target in (-181.3,-165,-145,-80,0,80,125,155,175)]
    for z in selected:
        section=v[np.abs(v[:,2]-z)<.0001]
        # Reference export preserves one ordered 50-vertex ring per station.
        assert len(section)==50,('Unexpected envelope section',z,len(section))
        outline=np.vstack([section,section[:1]])
        color=plt.cm.viridis((z+181.3)/362.6)
        body.plot(outline[:,0],outline[:,1],color=color,lw=1.7,label=f'Z {z:+.0f} m')
    body.axvline(0,color='#b2cbd2',lw=.8,ls='--');body.axhline(0,color='#b2cbd2',lw=.8)
    body.set(xlim=(-23,23),ylim=(-12.5,1),xlabel='Transverse X (m)',ylabel='Height relative to WL (m)',title='BODY SECTIONS · full stern sections provide initial waterjet packaging space')
    body.set_aspect('equal',adjustable='box');body.legend(loc='center left',bbox_to_anchor=(1.01,.5),fontsize=8,frameon=False,labelcolor=fg)
    fig.suptitle('AUSTRALIS v0.8.2  /  WATERJET HULL ENVELOPE',x=.065,ha='left',fontsize=22,fontweight='bold')
    fig.text(.065,.925,'Separate closed reference envelope · 41 m maximum waterline beam · 11.5 m maximum draft · intake ducts omitted from this lines sheet',fontsize=11,color=muted)
    fig.text(.065,.024,'Experimental game geometry. Envelope volume is not net buoyancy; loading, duct deductions, power, full stability and seakeeping remain unresolved.',fontsize=10,color=muted)
    fig.subplots_adjust(left=.08,right=.83,top=.88,bottom=.085,hspace=.8)
    fig.savefig(out/f'{RELEASE}-Hull-Lines.png',dpi=160,facecolor=bg);plt.close(fig)


def main():
    out=ROOT.parent/'finished';out.mkdir(exist_ok=True)
    native,obj,ini=load_current_mesh();mesh=Mesh()
    for name,v,faces,material in native.parts:
        if name=='UnderwaterHull' or name.startswith('Waterjet'):
            mesh.parts.append((name,v,faces,material))
        elif name in ('Surface_Dark','Surface_Underwater'):
            chosen=[f for f in faces if all(v[j][1]<-.0001 for j in f)]
            used=sorted({j for f in chosen for j in f})
            if not used:continue
            lookup={j:i for i,j in enumerate(used)}
            mesh.parts.append((name,v[used],[[lookup[j] for j in f] for f in chosen],material))
    assert not any(n.startswith(('Propeller','Rudder')) for n,*_ in mesh.parts)
    revision=viewer.model_revision(mesh,COLORS);triangles=list(mesh.triangles());photos=[]
    aft=clip_triangles(triangles)
    for key,title,az,el,selected in (
        ('stern-detail','Eight-jet stern detail',-65,-20,aft),
        ('underbody','Full submerged hull and waterjet arrangement',-115,-28,triangles),
        ('stern-aft','Stern outlets viewed from astern',-90,-8,aft),
    ):
        path=out/f'{RELEASE}-{key}.png'
        caption='v0.8.2 experimental · 8 waterjets · 4 outer steering / reversing concepts · 4 fixed boosters'
        footer='Actual exported mesh · detail views crop the aft hull · native game approximation; real propulsion performance unvalidated'
        _render(selected,COLORS,title,az,el,revision,path,caption=caption,footer=footer,light_direction=(.25,-.4,-.88),exposure=1.8)
        photos.append(dict(id=key,title=title,path=path,caption='Actual exported model. Stern detail views clip existing aft geometry for visibility.'))
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Australis 2030','Australis · waterjet hull').replace('v0.8.2 WATERJET PROTOTYPE','v0.8.2 WATERJET PROTOTYPE')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('CATOBAR · 370 m · 82 m main deck · 99 aircraft · 5,300 embarked targets','362.6 m waterline · 41 m maximum beam · 11.5 m maximum draft')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Two bow + one port-waist catapult. Four lifts and three helipads. Aircraft support: fixed-wing carrier aircraft, VTOL/STOL and helicopters.','Broad symmetric stern with eight open intake ducts and jet outlets. Four outer steering units and four fixed boosters. Upper hull and flight deck are omitted from this view.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('</style>','#deploy,#laserStatus,#deployCIWS,#ciwsStatus,#moveLifts{display:none} </style>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Lifts start at hangar level. Manual six-second movement preview.','Rotate below the stern to inspect intake mouths, ducts and nozzles.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Deployment demonstration only. The viewer does not fire weapons.','Static viewer pose. In-game impeller/steering animation uses native propulsion and rudder proxies.')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('These views and the rotatable model use the same current mesh. Aircraft are selected in Sea Power; this model has no parked aircraft.','These views and the rotatable hull use the same exported mesh. Detail photos crop the stern; the 3D view contains the full submerged hull.')
    start=viewer.TEMPLATE.index('  <div class="footer muted">')
    end=viewer.TEMPLATE.index('</aside>',start)
    viewer.TEMPLATE=viewer.TEMPLATE[:start]+'  <div class="footer muted">Actual game-package geometry, not an in-game screenshot. Eight units are a provisional packaging study. No CFD, matched pump curves, real speed, full stability or seakeeping validation. The closed reference envelope used for preliminary hydrostatics is excluded from this visible mesh.</div>\n'+viewer.TEMPLATE[end:]
    viewer.TEMPLATE=viewer.TEMPLATE.replace('elevation = 34*Math.PI/180','elevation = -22*Math.PI/180').replace('elevation=34*Math.PI/180','elevation=-22*Math.PI/180').replace('color * light, 1.0','color * light * 1.5, 1.0')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('const target = [0, 19, 0];','const target = [0, -4, 0];')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('Math.max(-.14,Math.min(1.50,','Math.max(-1.50,Math.min(1.50,').replace('Math.max(230,Math.min(1100,','Math.max(60,Math.min(1100,')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('<button type="button" data-view="bow">Bow</button>','<button type="button" data-view="bow">Bow</button><button type="button" data-view="stern">Stern detail</button>')
    viewer.TEMPLATE=viewer.TEMPLATE.replace('const view = button.dataset.view;','const view = button.dataset.view; target[2]=0;')
    viewer.TEMPLATE=viewer.TEMPLATE.replace("if (view === 'bow') { azimuth=0; elevation=.25; distance=480; }", "if (view === 'bow') { azimuth=0; elevation=-.10; distance=480; } if (view === 'stern') { top=false; azimuth=Math.PI; elevation=-.30; distance=90; target[2]=-165; }")
    viewer.build_viewer(mesh,COLORS,out/f'{RELEASE}-Waterjets-3D.html',photos=photos)
    data=json.loads((PACKAGE/'naval-hull-hydrostatics.json').read_text())
    groups=read_groups(PACKAGE/'hydrostatics-envelope.obj');lines_plan(groups,data,out)
    print('[OK] Actual waterjet 3D viewer, cropped stern renders and separate envelope lines sheet')
if __name__=='__main__':main()
