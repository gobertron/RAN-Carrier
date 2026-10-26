#!/usr/bin/env python3
"""Validate real native fleet files and their bindings with stdlib only."""
from pathlib import Path
import configparser,re,math,json
from internal_fit import validate_arrangement
UNIT=217/3.161967
IDS=['ran_cvn_australis_2030','ran_cvn_southern_cross_2030','ran_cvn_federation_2030','ran_cvn_commonwealth_2030']
def ini(p):
    c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(p,encoding='utf-8-sig');return c
def vec(s):return tuple(float(x) for x in s.split(','))
def validate(package,stock=None):
    package=Path(package)
    for ship_id in IDS:
        c=ini(package/'vessels'/f'{ship_id}.ini');deck=c['FlightDeck']
        assert c['General']['NumberOfDCTeams']=='5'
        for family,count in (('Elevator',4),('LaunchPoint',6),('RecoveryPoint',4),('DeckZone',15)):
            assert int(deck[f'NumberOf{family}s'])==count
            assert all(f'{family}{i}' in c for i in range(1,count+1))
            assert f'{family}{count+1}' not in c
        assert len([s for s in c.sections() if s.startswith('TaxiPath')])==int(deck['NumberOfTaxiPaths'])
        assert deck['LandingWhileLaunching']=='True' and deck['LaunchDelay']=='1'
        for e in (1,2):assert set(map(int,c[f'Elevator{e}']['AssociatedLaunchPoints'].split(',')))=={1,2,3}
        assert c['Elevator3']['AssociatedLaunchPoints']=='4' and c['Elevator4']['AssociatedLaunchPoints']=='6,5'
        for i in range(1,7):
            allowed=c[f'LaunchPoint{i}']['AllowedType'];assert ('Helicopter' in allowed)==(i>=4)
            assert c[f'LaunchPoint{i}']['SupportsVeryLarge']=='True'
        for i in range(2,5):
            assert not set(c[f'RecoveryPoint{i}'].get('BlocksRecoveryPoints','').split(',')) & {'2','3','4'}
        assert c['RecoveryPoint2']['Position']==c['LaunchPoint6']['Position']
        assert c['RecoveryPoint3']['Position']==c['LaunchPoint4']['Position']
        assert c['RecoveryPoint4']['Position']==c['LaunchPoint5']['Position']
        for i in range(1,int(deck['NumberOfTaxiPaths'])+1):
            path=c[f'TaxiPath{i}'];assert path['From'] in c and path['To'] in c
            assert all(all(math.isfinite(v) for v in vec(s)) for s in path['Waypoints'].split('|'))
        assert c['Animations']['AnimationFile_1']=='ran_australis_lifts'
        anim=ini(package/'animations/ran_australis_lifts.ini')
        for i in range(1,5):
            el=c[f'Elevator{i}'];assert el['Mesh']==f'LiftPlatform{i}'
            assert el['StartsLowered']=='True'
            for direction in ('Up','Down'):
                key=el[f'Move{direction}Animation'];seq=anim[key]['Sequence1']
                assert anim[key]['Sequence1_Model']==el['Mesh']
                ys=[float(anim[seq][f'Step{j}'].split('|')[1].split(',')[1])*UNIT for j in (1,2)]
                assert abs(abs(ys[1]-ys[0])-10.202)<1e-5
        obj=package/c['Models']['ResourcesFolder']/c['Models']['ResourcesRoot']
        groups=set(re.findall(r'^o (.+)$',obj.read_text(),re.M))
        registered=list(c['Submodels'].values());assert len(registered)==len(set(registered))
        assert set(registered)==groups-{'Hull','coll_hull_main'}|{'Flag1'},(ship_id,'missing submodels',groups-set(registered))
        for name in groups-{'Hull','coll_hull_main'}:
            assert c[name]['Mesh']==name
            if 'Parent' in c[name]:assert c[name]['Parent'] in c
            material=ini(obj.parent/c[name]['Material'])
            for tex in material['Textures'].values():assert (package/tex).is_file(),tex
        # The VLS parent supplies the actual forward axis. Test transformed axes,
        # rather than trusting only the per-container angle.
        for i in range(1,5):
            root=c[f'PVLS_{i}_LaunchBase'];assert root['Rotation']=='-90,0,0'
            angle=math.radians(vec(root['Rotation'])[0]);forward=(0,-math.sin(angle),math.cos(angle))
            assert math.dist(forward,(0,1,0))<1e-8
        ciws=[c[s] for s in c.sections() if re.fullmatch(r'WeaponSystem\d+',s) and c[s].get('Type')=='CIWS']
        assert len(ciws)==5
        assert c['Magazine_CIWS']['Ammunition1_Count']=='20000'
        assert sum(int(c[f'Magazine_PVLS_{i}']['Ammunition1_Count']) for i in (1,3))==40
        assert all(c[f'Magazine_PVLS_{i}']['Ammunition1']=='usn_rim-66e' for i in (1,3))
        assert c['Foam']['SternFoamTexture'] and c['RudderSystem1']['Mount']=='WaterjetSteering1'
        assert c['PropulsionSystems']['NumberOfPropulsionSystems']=='8'
        assert c['RudderSystems']['NumberOfRudderSystems']=='4'
        for i in range(1,9):
            assert c[f'PropulsionSystem{i}']['Mount']==f'WaterjetImpeller{i}'
        for j,i in enumerate((1,2,7,8),1):
            assert c[f'RudderSystem{j}']['Mount']==f'WaterjetSteering{i}'
        assert c['Physics']['MaxForwardVelocity']=='30' and c['MainPowerSystem']['HorsePower']=='280000'
        telegraph=vec(c['Physics']['TelegraphVelocities'])
        # Native loader indexes the seven knots entries by telegraph + 1.
        assert telegraph==(-7.,0.,6.,12.,20.,30.,30.),(ship_id,'incorrect aviation/emergency speed ladder')
        assert telegraph[3+1]==20 and telegraph[4+1]==30 and max(telegraph)==30
        if stock is not None:check_stock(c,package,Path(stock))
    result=validate_arrangement(package)
    lighting=json.loads((package/'lift-lighting.json').read_text())
    assert lighting['deck_level_m']==22.002 and lighting['lower_level_m']==11.8
    assert lighting['off_depth_m']==.10 and lighting['full_depth_m']==.60
    assert len(lighting['groups'])==4 and lighting['daytime_operation']
    positions=ini(package/'vessels/ran_cvn_australis_2030.ini')
    for i,group in enumerate(lighting['groups'],1):
        assert group['id']==i and group['model']==f'LiftPlatform{i}'
        cx,_,cz=(a*UNIT for a in vec(positions[group['model']]['Position']))
        assert len(group['fixtures'])==8
        for lamp in group['fixtures']:
            x,y,z=lamp['position'];pitch,yaw,roll=lamp['rotation_degrees']
            assert y in (15.,19.) and pitch-lamp['spot_angle']/2>=5
            assert lamp['range']==7 and lamp['intensity']==.65
            if lamp['wall']=='outer':assert x-cx>=11.13
            else:assert abs(z-cz)>=13.13
    motions=json.loads((package/'enclosed-deck.json').read_text())['motions']
    assert len(motions)==81
    for m in motions:
        if m['axis']=='y' and m['name'].startswith(('CIWS','Mk46','ESSM','RAM','SRBOC')):
            roof=44 if m['name']=='CIWS_4_Lift' else 37.84 if m['name']=='CIWS_5_Lift' else 22
            assert abs(m['position'][1]+m['travel']-roof-.08)<1e-6,m
    assert (package/'RAN.Australis.DeckController.dll').read_bytes()[:2]==b'MZ'
    print('[OK] Four ships; five teams; lift/animation, route and role bindings; all 80 vertical axes; internal fit')
    return result
def check_stock(c,package,stock):
    for family,file in (('SensorSystem','sensors.ini'),('WeaponSystem','weapons.ini')):
        local=ini(package/'systems'/file);catalog=ini(stock/'systems'/file)
        if not catalog.sections():raise ValueError('Missing stock catalogue: '+file)
        for i in range(1,int(c[family+'s']['NumberOf'+family+'s'])+1):
            s=c[f'{family}{i}']
            if s['Type']!='Visual' and s['SystemName'] not in set(local.sections())|set(catalog.sections()):raise ValueError('Missing stock system '+s['SystemName'])
    for s in c.sections():
        for key,value in c[s].items():
            if re.fullmatch(r'Ammunition\d*|Countermeasure',key) and not (stock/'ammunition'/f'{value}.ini').is_file():raise ValueError('Missing stock round '+value)
    if not (stock/'vessels/usn_cvn_nimitz.ini').is_file():raise ValueError('Stock Nimitz definition not found')
if __name__=='__main__':validate(Path(__file__).resolve().parents[1]/'game-mod/RAN-Carrier-Australis-2030')
