# SteamVR debugging tool

import sys 
import csv 
import json

import viz
import vizfx
import vizmat
import vizact
import vizinfo
import viztask
import vizshape

import steamvr

viz.setMultiSample(8)
viz.go()

WRIST_ID = 0 # ID of the tracker that represents the wrist
REF_ID = 1 	 # ID of tracker that is used as the reference

PART_ID = viz.input('Participant ID')

# Global coordinate visualization
grid = vizshape.addGrid((100, 100), color=[0.4, 0.4, 0.4])
main_axes = vizshape.addAxes(pos=(0,0,0), scale=(0.5, 0.5, 0.5))
ground_plane = vizshape.addPlane((100,100), color=[0.3, 0.3, 0.3], alpha=0.5)

# Lighting
headlight = viz.MainView.getHeadLight()
headlight.disable()
main_light = vizfx.addDirectionalLight(euler=(0,90,0), color=viz.WHITE)
origin_light = vizfx.addPointLight(color=viz.WHITE, pos=(0,0,0))

# UI
txt = 'Hotkeys:\nSpace - Save offset sample\nQ - Quit\n\n'
ui = vizinfo.InfoPanel(txt, icon=True, align=viz.ALIGN_RIGHT_TOP, title='Hand Offset Calibration')
ui.addSeparator()
ui_wrist = viz.addTextbox()
ui_wrist.setLength(0.5)
ui_wrist.message(str(WRIST_ID))
ui_ref = viz.addTextbox()
ui_ref.setLength(0.5)
ui_ref.message(str(REF_ID))
ui.addLabelItem('Wrist tracker ID:', ui_wrist)
ui.addLabelItem('Reference tracker ID:', ui_ref)
ui_submit = ui.addItem(viz.addButtonLabel('Update IDs'),align=viz.ALIGN_RIGHT_CENTER)
ui.renderToEye(viz.RIGHT_EYE)

points = []
devices = {}

def updateIDs():
	""" Button callback to allow setting tracker IDs """
	id_wrist_new = int(ui_wrist.getMessage())
	id_ref_new = int(ui_ref.getMessage())
	if id_wrist_new == id_ref_new:
		print('Error: Tracker IDs cannot be identical!')
		return -1		
	if id_wrist_new not in trackers.keys():
		print('Error: No tracker with ID {:d}!'.format(id_wrist_new))
		return -1
	if id_ref_new not in trackers.keys():
		print('Error: No tracker with ID {:d}!'.format(id_ref_new))
		return -1
	WRIST_ID = id_wrist_new
	REF_ID = id_ref_new
	print('IDs updated: wrist ({:d}), reference ({:d})'.format(WRIST_ID, REF_ID))
vizact.onbuttondown(ui_submit, updateIDs)


def storeOffset():
	""" Save position data of both trackers to later calculate offset """  
	this_sample = {}
	for id in trackers.keys():
		pos = trackers[id]['model'].getPosition(viz.ABS_GLOBAL)
		this_sample[id] = pos
	
	# Make a child object, position in abolute coords and read out wrist-relative position
	ref_rel = viz.addGroup(parent=trackers[WRIST_ID]['model'])
	ref_rel.setPosition(trackers[REF_ID]['model'].getPosition(viz.ABS_GLOBAL), viz.ABS_GLOBAL)
	this_sample['offset'] = ref_rel.getPosition(viz.REL_PARENT)

	points.append(this_sample)
	s = 'Saved: '
	for id in this_sample.keys():
		s += '{:s}: ({:.3f}, {:.3f}, {:.3f}) '.format(str(id), this_sample[id][0], 
													  this_sample[id][1], this_sample[id][2])
	print(s)
	

def saveCalibration(filename='wrist_offset'):
	""" Save list of stored points """
	fn = filename + '_' + str(PART_ID) + '.json'
	
	avg = [[], [], []]
	for sample in points:
		avg[0].append(sample['offset'][0])
		avg[1].append(sample['offset'][1])
		avg[2].append(sample['offset'][2])
	for ix, coord in enumerate(avg):
		avg[ix] = sum(coord) / len(coord)
	print('* Mean relative offset: ({:.3f}, {:.3f}, {:.3f})'.format(*avg))
	data = {'samples': points, 'average_offset': avg}

	with open(fn, 'w') as jf:
		json.dump(data, jf)
	print('Calibration data saved: {:s}.'.format(fn))

	# Make a cursor sphere to visualize offset
	index = vizshape.addSphere(0.01, parent=trackers[WRIST_ID]['model'])
	index.setPosition(avg, mode=viz.REL_PARENT)


# Headset
hmd = steamvr.HMD()
if not hmd.getSensor():
	sys.exit('Vive not detected')
hmd.setMonoMirror(True)
navigationNode = viz.addGroup()
viewLink = viz.link(navigationNode, viz.MainView)
viewLink.preMultLinkable(hmd.getSensor())

# Lighthouses
lighthouses = {}
for lidx, lighthouse in enumerate(steamvr.getCameraList()):
	
	lighthouse.model = lighthouse.addModel(parent=navigationNode)
	if not lighthouse.model:
		lighthouse.model = viz.addGroup(parent=navigationNode)
		
	lighthouse.model.disable(viz.INTERSECTION)
	viz.link(lighthouse, lighthouse.model)
	
	l_text = viz.addText3D(str(lidx), scale=(0.05, 0.05, 0.05), color=viz.YELLOW,
						   parent=lighthouse.model, pos=(0.1, 0, 0))
	l_text.setEuler(180, 0, 0)
	
	lighthouses[lidx] = {'model': lighthouse.model,
						 'text': l_text}
	print('Found Lighthouse: {:d}'.format(lidx))


# Controllers
controllers = {}
for cidx, controller in enumerate(steamvr.getControllerList()):
	
	controller.model = controller.addModel(parent=navigationNode)
	if not controller.model:
		controller.model = viz.addGroup(parent=navigationNode)
	controller.model.disable(viz.INTERSECTION)
	viz.link(controller, controller.model)
	
	c_axes = vizshape.addAxes(scale=(0.1, 0.1, 0.1))
	viz.link(controller, c_axes)
	c_text = viz.addText3D(str(cidx), scale=(0.05, 0.05, 0.05), 
						   parent=controller.model, pos=(-0.05, 0, 0))
						   
	vizact.onsensordown(controller, steamvr.BUTTON_TRIGGER, storeOffset)
	controllers[cidx] = {'model': controller.model,
						 'axes': c_axes,
						 'text': c_text}
	
	print('Found Controller: {:d}'.format(cidx))
	

# Trackers
trackers = {}
for tidx, tracker in enumerate(steamvr.getTrackerList()):
	
	tracker.model = tracker.addModel(parent=navigationNode)
	if not tracker.model:
		tracker.model = viz.addGroup(parent=navigationNode)
	tracker.model.disable(viz.INTERSECTION)
	viz.link(tracker, tracker.model)

	t_axes = vizshape.addAxes(scale=(0.1, 0.1, 0.1))
	viz.link(tracker, t_axes)

	t_text = viz.addText3D(str(tidx), scale=(0.05, 0.05, 0.05), color=viz.BLUE,
						   parent=tracker.model, pos=(-0.1, 0, 0))

	trackers[tidx] = {'model': tracker.model,
					  'axes': t_axes,
					  'text': t_text}
	print('Found Vive tracker: {:d}'.format(tidx))



def Main():
	pass

vizact.onkeydown(' ', storeOffset)
vizact.onkeydown('s', saveCalibration)
vizact.onkeydown('q', viz.quit)
viztask.schedule(Main)