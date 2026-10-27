"""Controller tests with fake widgets; NOT graphical/Tk rendering validation."""
from pathlib import Path
import queue
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qr_viewer import PrivateViewer
from viewer_core import DisplayGate, Frame, Result
from test_viewer_core import PNG

class Widget:
    def __init__(self,events):self.events=events
    def configure(self,**kwargs):self.events.append(('configure',kwargs))
    def set(self,value):self.events.append(('message',value))
class Root:
    def __init__(self,events):self.events=events
    def after(self,*args):self.events.append(('after',args[0]))
    def destroy(self):self.events.append(('destroy',None))
    def focus_displayof(self):return None

def fixture():
    events=[]; viewer=PrivateViewer.__new__(PrivateViewer)
    viewer.root=Root(events);viewer.reader=None;viewer.gate=DisplayGate();viewer.results=queue.Queue(maxsize=1)
    viewer.enabled=True;viewer.busy=False;viewer.closed=False;viewer.photo=None;viewer.next_poll=100
    viewer.image=Widget(events);viewer.message=Widget(events);viewer.lease=Widget(events)
    return viewer,events

class ControllerTests(unittest.TestCase):
    def test_pause_focus_loss_and_close_clear_pixels(self):
        for operation in ['pause','_check_focus','close']:
            viewer,events=fixture();serial=viewer.gate.begin()
            viewer.gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2);viewer.photo=object()
            getattr(viewer,operation)()
            self.assertIsNone(viewer.photo);self.assertIsNone(viewer.gate.frame)
            self.assertFalse(viewer.enabled)
            self.assertIn(('configure',{'image':'','text':'QR oculto'}),events)
    def test_timer_clears_expired_image_without_network(self):
        viewer,events=fixture();serial=viewer.gate.begin()
        viewer.gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2);viewer.photo=object()
        with patch('qr_viewer.time.monotonic',return_value=10):viewer.tick()
        self.assertIsNone(viewer.photo);self.assertIn(('configure',{'image':'','text':'QR oculto'}),events)
    def test_poll_hides_first_and_starts_only_one_worker(self):
        viewer,events=fixture();viewer.next_poll=0
        class Thread:
            def __init__(self,**kwargs):events.append(('thread_create',None))
            def start(self):events.append(('thread_start',None))
        with patch('qr_viewer.time.monotonic',return_value=2),patch('qr_viewer.threading.Thread',Thread):
            viewer.tick();viewer.tick()
        self.assertEqual(events[0],('configure',{'image':'','text':'QR oculto'}))
        self.assertEqual(sum(event[0]=='thread_start' for event in events),1)
    def test_stale_completion_after_pause_cannot_redisplay(self):
        viewer,_=fixture();serial=viewer.gate.begin();viewer.pause();viewer.enabled=True
        viewer.results.put((serial,Result('qr_required',Frame(1,10,PNG,1))))
        with patch('qr_viewer.time.monotonic',return_value=2),patch.object(viewer,'_show') as show:
            viewer.tick();show.assert_not_called()
    def test_failed_refresh_clears_existing_photo(self):
        viewer,_=fixture();serial=viewer.gate.begin();viewer.photo=object()
        viewer.results.put((serial,Result('transport_unavailable')))
        with patch('qr_viewer.time.monotonic',return_value=2):viewer.tick()
        self.assertIsNone(viewer.photo);self.assertIsNone(viewer.gate.frame)
    def test_resume_keeps_old_image_hidden_until_new_result(self):
        viewer,events=fixture();serial=viewer.gate.begin();viewer.photo=object()
        viewer.pause();viewer.resume()
        self.assertTrue(viewer.enabled);self.assertIsNone(viewer.photo)
        self.assertGreater(viewer.gate.serial,serial);self.assertEqual(viewer.next_poll,0)
    def test_visible_local_lease_is_not_claimed_whatsapp_validity(self):
        viewer,events=fixture();serial=viewer.gate.begin()
        viewer.gate.accept(serial,Result('qr_required',Frame(3,2.5,PNG,1)),2);viewer.photo=object()
        with patch('qr_viewer.time.monotonic',return_value=2):viewer.tick()
        messages=[event[1] for event in events if event[0]=='message']
        self.assertTrue(any('0.50 s' in m and 'quadro 3' in m and 'Não é garantia' in m for m in messages))
    def test_image_decode_error_is_hidden_without_exception_details(self):
        viewer,events=fixture();serial=viewer.gate.begin()
        viewer.gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2)
        try:
            import tkinter
        except ImportError:
            self.skipTest('Tk unavailable; actual GUI remains unvalidated')
        with patch('tkinter.PhotoImage',side_effect=RuntimeError('DO_NOT_DISPLAY_RAW_DETAILS')):
            viewer._show(viewer.gate.frame)
        self.assertIsNone(viewer.photo);self.assertNotIn('DO_NOT_DISPLAY',str(events))

if __name__=='__main__':unittest.main()
