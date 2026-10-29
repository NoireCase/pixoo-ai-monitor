from copy import deepcopy
import json
from types import SimpleNamespace
import threading
from unittest.mock import patch
import pytest
from health_check import read_snapshot,process_inventory
from runtime_health import RuntimeStatus,evaluate

NOW=10000
PROCESSES=[{'pid':12,'parent_pid':11},{'pid':11,'parent_pid':3}]

def snapshot():
    return {'schema_version':1,'pid':12,'process_birth':8000,'state':'running','heartbeat_at':NOW-1,
            'heartbeat_timeout_seconds':30,'refresh_seconds':120,'provider_timeout_seconds':75,
            'data_stale_seconds':360,'bluetooth_connected':True,'frame_result':'sent',
            'last_frame_check_at':NOW-1,'last_send_at':NOW-1,
            'providers':{p:{'status':'OK','last_attempt_at':NOW-2,'last_success_at':NOW-1,
                            'in_progress':False,'error_kind':None} for p in ('go','cx','ds')}}

def verdict(data=None,processes=None,birth=8000):
    return evaluate(snapshot() if data is None else data,PROCESSES if processes is None else processes,now=NOW,live_birth=birth)

def test_healthy_launcher_child_one_instance():
    assert verdict()['overall']=='HEALTHY'
    assert not any(c['level']=='UNHEALTHY' for c in verdict()['checks'])

def test_no_extra_send_needed_for_unchanged_frame():
    s=snapshot();s.update(frame_result='unchanged',last_send_at=1)
    assert verdict(s)['overall']=='HEALTHY'

@pytest.mark.parametrize('status',['ERROR','STALE','NOT_CONFIGURED','UNSUPPORTED','PENDING'])
def test_provider_failure_is_degraded(status):
    s=snapshot();s['providers']['go'].update(status=status,error_kind='HTTP 400')
    r=verdict(s)
    assert r['overall']=='DEGRADED'
    assert any(c['name']=='cx' and c['level']=='OK' for c in r['checks'])

def test_disconnected_socket():
    s=snapshot();s.update(bluetooth_connected=False,frame_result='waiting_reconnect')
    assert verdict(s)['overall']=='DEGRADED'

def test_no_successful_send():
    s=snapshot();s['last_send_at']=None
    assert verdict(s)['overall']=='DEGRADED'

def test_loop_stalled_even_if_process_exists():
    s=snapshot();s['heartbeat_at']=NOW-31
    assert verdict(s)['overall']=='UNHEALTHY'

def test_old_heartbeat_not_running():
    assert verdict(processes=[])['overall']=='UNHEALTHY'

def test_stopped():
    s=snapshot();s['state']='stopped'
    assert verdict(s)['overall']=='UNHEALTHY'

def test_pid_reused():
    assert verdict(birth=9000)['overall']=='UNHEALTHY'

def test_duplicates_two_groups():
    assert verdict(processes=PROCESSES+[{'pid':21,'parent_pid':3}])['overall']=='UNHEALTHY'

def test_permission_denied_and_identity_unknown():
    assert evaluate(snapshot(),None,now=NOW,live_birth=None)['overall']=='UNKNOWN'

def test_legacy_no_heartbeat():
    assert evaluate(None,PROCESSES,now=NOW)['overall']=='UNKNOWN'
    assert evaluate(None,[],now=NOW)['overall']=='UNHEALTHY'

def test_clock_change():
    s=snapshot();s['heartbeat_at']=NOW+60
    assert verdict(s)['overall']=='UNKNOWN'

@pytest.mark.parametrize('in_progress,age',[(True,76),(False,196)])
def test_refresh_thread_stalled(in_progress,age):
    s=snapshot();s['providers']['go'].update(last_attempt_at=NOW-age,in_progress=in_progress)
    assert verdict(s)['overall']=='DEGRADED'

def test_success_data_expired():
    s=snapshot();s['providers']['go']['last_success_at']=NOW-361
    assert verdict(s)['overall']=='DEGRADED'

def test_corrupt_and_missing_heartbeat(tmp_path):
    p=tmp_path/'status.json';assert read_snapshot(p)==(None,None)
    p.write_text('{bad');assert read_snapshot(p)[1]
    p.write_text(json.dumps({'schema_version':99}));assert read_snapshot(p)[1]
    s=snapshot();s['providers']['go']['last_attempt_at']=float('nan')
    p.write_text(json.dumps(s));assert read_snapshot(p)[1]

def test_heartbeat_schema_and_no_secrets(tmp_path):
    status=RuntimeStatus(tmp_path/'runtime-status.json',{'mac':'SECRET_DEVICE','display_style':'b3'})
    sample=snapshot()['providers']
    sample['go'].update(api_key='SECRET_KEY',remaining_percent=72,error_kind='sensitive response body')
    monitor=SimpleNamespace(guard=threading.Lock(),provider_health=sample,data={'balance':'SECRET_BALANCE'})
    status.write(monitor,frame_result='unchanged')
    raw=status.path.read_text()
    assert all(x not in raw for x in ['SECRET_DEVICE','SECRET_KEY','SECRET_BALANCE','remaining_percent','sensitive response body'])
    assert read_snapshot(status.path)[1] is None
    assert not status.path.with_suffix('.json.tmp').exists()
    status.write(monitor,state='stopped')
    assert json.loads(status.path.read_text())['state']=='stopped'

def test_inventory_filters_project_and_emits_only_ids():
    result=SimpleNamespace(returncode=0,stdout='[{"pid":12,"parent_pid":11}]')
    with patch('health_check.subprocess.run',return_value=result) as run:
        assert process_inventory()==[{'pid':12,'parent_pid':11}]
        command=run.call_args.args[0][-1]
        assert 'PIXOO_HEALTH_ROOT' in command and 'parent_pid' in command
        assert run.call_args.kwargs['timeout']==12

def test_inventory_failure_unknown():
    with patch('health_check.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
        assert process_inventory() is None
