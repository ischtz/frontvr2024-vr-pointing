"""
Mid-Air Object Pointing Study
Immo Schuetz, 2020
"""

import math
import glob
import json

import hand

import viz
import vizfx
import vizact
import vizcam
import vizmat
import viztask
import vizshape
import vizinput
import vizconnect
import vizproximity
import vizfx.postprocess

from vizfx.postprocess.color import ExposureEffect

import steamvr 

from vzgazetoolbox.experiment import *
from vzgazetoolbox.recorder import SampleRecorder
from vzgazetoolbox.data import VAL_TAR_CR5, VAL_TAR_C

DEBUG = False

# Hardware Setup
# -----------------------------------------------------------------------------


viz.setMultiSample(4)
#vizconnect.go('vizconnect/avatar.py')
viz.go()


# HMD setup
HAS_VR = False
try:
    hmd = steamvr.HMD()
    if not hmd.getSensor():
        sys.exit('Vive not detected')
    HAS_VR = True
    hmd.setMonoMirror(True)
except:
    print('SteamVR not running')


# Set up navigation and controllers
eyeTracker = None
if HAS_VR:        
    navigationNode = viz.addGroup()
    viewLink = viz.link(navigationNode, viz.MainView)
    viewLink.preMultLinkable(hmd.getSensor())
    navigationNode.setPosition(0, 0, -1.8)

    # Check for controller availability
    if not steamvr.getControllerList():
        raise RuntimeError('No controllers connected! Left controller must be on and connected for this study.')

    for controller in steamvr.getControllerList():
        controller.model = controller.addModel(parent=navigationNode)
        if not controller.model:
            controller.model = viz.addGroup(parent=navigationNode)
        controller.model.disable(viz.INTERSECTION)
        viz.link(controller, controller.model)

    for tracker in steamvr.getTrackerList():
        tracker.model = tracker.addModel(parent=navigationNode)
        if not tracker.model:
            tracker.model = viz.addGroup(parent=navigationNode)
        tracker.model.disable(viz.INTERSECTION)
        viz.link(tracker, tracker.model)
        tracker.model.visible(False)

    VivePro = viz.add('VivePro.dle')
    eyeTracker = VivePro.addEyeTracker()
    if not eyeTracker:
        sys.exit('Eye tracker not detected')

else:
    walkNav = vizcam.WalkNavigate()
    viz.MainWindow.stereo(viz.STEREO_LEFT)
    


# Function Definitions
# -----------------------------------------------------------------------------


def generateStartPositions(distance=1.5, radius=0.25, eyeheight=0):
    """ Generate starting position objects (shoes) """
    hyp = distance / math.sqrt(2)
    
    positions = {'E':  [distance, eyeheight, 0.0],
                 'W':  [-distance, eyeheight, 0.0],
                 'N':  [0.0, eyeheight, distance],
                 'S':  [0.0, eyeheight, -distance],
                 'SW': [-hyp, eyeheight, -hyp],
                 'NW': [-hyp, eyeheight, hyp],
                 'NE': [hyp, eyeheight, hyp],
                 'SE': [hyp, eyeheight, -hyp]}

    return positions


def loadObjectFolder(files):
    """ Load all object files from asset folder, return dict
    
    Args:
        files (str): file spec, e.g. 'objects/*.glb' 
    """
    obj = {}
    for of in glob.glob(files):
        key = os.path.splitext(os.path.split(of)[1])[0]
        obj[key] = vizfx.addChild(of)
        obj[key].visible(False)

    return obj


def showObject(obj_dict, key, position, scale, yaw=0, material=0):
    """ Show one object from a dict of nodes, hiding all others
    
    Args:
        obj_dict: Dict of node3d objects
        key (str): Key of object to be shown
    """
    hideAllObjects(obj_dict)
    obj_dict[key].setPosition(position)
    obj_dict[key].setScale([scale, scale, scale])
    obj_dict[key].setEuler([yaw, 0.0, 0.0])
    obj_dict[key].color(COLORS[material])
    obj_dict[key].visible(True)


def hideAllObjects(obj_dict):
    """ Hide all objects from a dict of nodes """
    for obj in obj_dict.keys():
        obj_dict[obj].visible(False)


def fadeExposure(effect, exposure=-10, duration=1.0):
    """ Gradually fade the post-processing exposure value to 
    <exposure>, to simulate a world fade in/out effect """
    ex_start = effect.getExposure()
    t_start = viz.tick()    
    t_end = t_start + duration
    t = viz.tick()
    while t < t_end:
        p = (t-t_start) / duration
        ex = vizmat.Interpolate(ex_start, exposure, p)
        effect.setExposure(ex)
        yield vizact.waittime(0.01)
        t = viz.tick()


def updateRaycast(node):
    """ Calculate Eye-Finger-Raycast and set cursor node """
    #controller = steamvr.getControllerList()[1]
    #finger_ori = controller.model.getPosition(viz.ABS_GLOBAL)
    finger_ori = finger_cursor.getPosition(viz.ABS_GLOBAL)
    gaze_ori = exp.recorder.getCurrentGazeMatrix().getPosition()
    
    efrc = vizmat.VectorToPoint(gaze_ori, finger_ori)
    ray_end = vizmat.MoveAlongVector(gaze_ori, efrc, 1000)
    info = viz.MainScene.intersect(gaze_ori, ray_end)
    if info.valid:
        node.setPosition(info.point)
        node.dirVector = vizmat.VectorToPoint(gaze_ori, info.point)


def updateRaycasts(nodeC, nodeL, nodeR):
    """ Calculate Eye-Finger-Raycast and set cursor node """
    #controller = steamvr.getControllerList()[1]
    #finger_ori = controller.model.getPosition(viz.ABS_GLOBAL)
    finger_ori = finger_cursor.getPosition(viz.ABS_GLOBAL)
    gaze_ori = exp.recorder.getCurrentGazeMatrix().getPosition()
    gazeL_ori = exp.recorder.getCurrentGazeMatrix(viz.LEFT_EYE).getPosition()
    gazeR_ori = exp.recorder.getCurrentGazeMatrix(viz.RIGHT_EYE).getPosition()
    
    # Common gaze
    efrc = vizmat.VectorToPoint(gaze_ori, finger_ori)
    ray_end = vizmat.MoveAlongVector(gaze_ori, efrc, 1000)
    info = viz.MainScene.intersect(gaze_ori, ray_end)
    if info.valid:
        nodeC.setPosition(info.point)
        nodeC.dirVector = vizmat.VectorToPoint(gaze_ori, info.point)

    # Left eye
    efrcL = vizmat.VectorToPoint(gazeL_ori, finger_ori)
    ray_end = vizmat.MoveAlongVector(gazeL_ori, efrc, 1000)
    info = viz.MainScene.intersect(gazeL_ori, ray_end)
    if info.valid:
        nodeL.setPosition(info.point)
        nodeL.dirVector = vizmat.VectorToPoint(gazeL_ori, info.point)
    
    # Right eye
    efrcR = vizmat.VectorToPoint(gazeR_ori, finger_ori)
    ray_end = vizmat.MoveAlongVector(gazeR_ori, efrc, 1000)
    info = viz.MainScene.intersect(gazeR_ori, ray_end)
    if info.valid:
        nodeR.setPosition(info.point)
        nodeR.dirVector = vizmat.VectorToPoint(gazeR_ori, info.point)

def wallText(msg, color=[1.0, 1.0, 1.0], scale=0.08):
    """ Display message text on the North wall until controller button press
    
    Args:
        msg (str): Message text
        color: RBG 3-tuple of color values
        scale (float): Text node scaling factor    
    """
    # Create 3D text object
    text = viz.addText3D(msg, scale=[scale, scale, scale], color=color)
    text.resolution(1.0)
    text.setThickness(0.1)
    text.alignment(viz.ALIGN_CENTER)
    text.disable(viz.LIGHTING)
    
    # Move text to North wall
    text.setPosition(0.0, 1.8, 1.99)
    
    # Wait for trigger button press
    event = yield viztask.waitSensorDown(None, steamvr.BUTTON_TRIGGER)
    text.remove()
    viztask.returnValue(event)



# Experiment Setup
# -----------------------------------------------------------------------------


# Initialize experiment parameters
exp = Experiment(name='VRpoint', debug=DEBUG, auto_save=False)

exp.config.fade_dur     = 0.6
exp.config.object_scale = 0.6
exp.config.cursor_size  = 0.025
exp.config.stand_dst 	= 1.5
exp.config.stand_radius = 0.25
exp.config.wrist_tracker= 0 # Tracker ID
exp.config.start_pos    = generateStartPositions(exp.config.stand_dst, radius=exp.config.stand_radius)
exp.config.start_ori    = {'S':  0.0, 'W':  90.0, 'N': 180.0, 'E': -90.0, 
                           'SW': 45.0, 'NW': 135.0,  'NE': -135.0, 'SE': -45.0}
if DEBUG:
    exp.config.ray_cursor   = True
    exp.config.gaze_cursor  = True
else:
    exp.config.ray_cursor   = False
    exp.config.gaze_cursor  = False

# Load main trials (will ask for file)
exp.addTrialsFromCSV(block=2, params={'type': 'obj'})

# Set up calibration trials 
calib_params = {'type': 'cal',
                'start_pos':'S',
                'feedback': exp.trials[0].params.feedback}
print('* Setting calibration feedback based on first trial: {:s}'.format(exp.trials[0].params.feedback))
exp.addTrials(9, block=1, params=calib_params, list_params={'tar': list(range(1, 10))})
exp.addTrials(9, block=1, params=calib_params, list_params={'tar': list(range(1, 10))})

# Randomize (also sorts by block)
exp.randomizeTrials()
print(exp.trials)

# Gaze and hand recording
exp.addSampleRecorder(eye_tracker=eyeTracker, cursor=True)
exp.recorder._cursor.setScale(0.5, 0.5, 0.5)
exp.recorder._cursor.alpha(0.6)
exp.recorder.showGazeCursor(exp.config.gaze_cursor)

# Add button and object state to samples file
exp.recorder.setCustomVar('button', 0)
exp.recorder.setCustomVar('object_visible', 0)


# Fixation positions, presented opposite starting position
fix_pos = {'E':  [-2.0, 1.8, 0.0],
           'W':  [2.0, 1.8, 0.0],
           'N':  [0.0, 1.8, -2.0],
           'S':  [0.0, 1.8, 2.0],
           'SW': [2.0, 1.8, 2.0],
           'NW': [2.0, 1.8, -2.0],
           'NE': [-2.0, 1.8, -2.0],
           'SE': [-2.0, 1.8, 2.0]}

# Calibration positions, grid presented in N wall
cal_pos = {1:  [0.0, 1.8, 2.0],
           2:  [-1.0, 1.8, 2.0],
           3:  [-1.0, 2.8, 2.0],
           4:  [0.0, 2.8, 2.0],
           5:  [1.0, 2.8, 2.0],
           6:  [1.0, 1.8, 2.0],
           7:  [1.0, 0.8, 2.0],
           8:  [0.0, 0.8, 2.0],
           9:  [-1.0, 0.8, 2.0]}

# From colorbrewer package, Set1
COLORS = [[0.5, 0.5, 0.5],
          [0.8941, 0.102 , 0.1098],
          [0.2157, 0.4941, 0.7216],
          [0.302 , 0.6863, 0.2902],
          [0.5961, 0.3059, 0.6392],
          [1.    , 0.498 , 0.    ],
          [1.    , 1.    , 0.2   ],
          [0.651 , 0.3373, 0.1569],
          [0.9686, 0.5059, 0.749 ],
          [0.6   , 0.6   , 0.6   ]]

exp.config.fix_pos = fix_pos
exp.config.cal_pos = cal_pos
exp.config.colors = COLORS


# Scene Setup
# -----------------------------------------------------------------------------

# Load dict of target objects
allobj = loadObjectFolder('assets/objects/*.glb')

# Visual scene elements
#sky = vizfx.addChild('sky_day.osgb')
room = vizfx.addChild('assets/TableRoom.glb')
table = vizfx.addChild('assets/MarbleColumn.glb')
table.setPosition(0.0, -1.0, 0.0) # Note: MarbleColumn has centered origin, 2m height
table.visible(False)

# Lighting
viz.MainView.getHeadLight().disable()
sun = viz.addLight() 
sun.setEuler(0, 90, 0) 
fader = ExposureEffect()
vizfx.postprocess.addEffect(fader)

# Feedback: Wrist Tracker + Offset
left_controller = steamvr.getControllerList()[0].model
left_controller.visible(False)
#right_controller = steamvr.getControllerList()[1].model
#right_controller.visible(False)
wrist_tracker = steamvr.getTrackerList()[exp.config.wrist_tracker]
wrist_pos = viz.addGroup(parent=navigationNode)
wrist_pos.disable(viz.INTERSECTION)
viz.link(wrist_tracker, wrist_pos)

exp.recorder.addTrackedNode(wrist_pos, 'wrist')

## Feedback: Hand
#hand = viz.addGroup()
handR = hand.HandModel(file='glove.cfg')
handR.setParent(wrist_pos)
handR.disable(viz.INTERSECTION)
handR.setGesture(hand.GESTURE_INDEX_FINGER, closeThumb=True)
handR.setEuler([90, -110, 90])
handR.setPosition([0, 0.1, 0], viz.REL_PARENT)
glove_index = handR.getBone('END index')

# Feedback: Cursor
finger_cursor = vizshape.addSphere(exp.config.cursor_size / 2.0, 
                                   color=viz.BLUE, parent=wrist_pos)
finger_cursor.alpha(1.0)
finger_cursor.disable(viz.INTERSECTION)
finger_cursor.visible(False)

exp.recorder.addTrackedNode(finger_cursor, 'index')
exp.recorder.addTrackedNode(glove_index, 'glove_index')

# Raycast node and cursor
efrc = viz.addGroup()
efrc.dirVector = [0, 0, 0]
efrc_cursor = vizshape.addSphere(exp.config.cursor_size, color=viz.GREEN, parent=efrc)
efrc_cursor.alpha(0.6)
efrc.disable(viz.INTERSECTION) # don't raycast onto cursor itself!
efrc_cursor.disable(viz.INTERSECTION)
efrc_cursor.visible(exp.config.ray_cursor)

# Monocular raycasts
efrcL = viz.addGroup() # left eye
efrcL.dirVector = [0, 0, 0]
efrcL.disable(viz.INTERSECTION)
efrcR = viz.addGroup() # right eye
efrcR.dirVector = [0, 0, 0]
efrcR.disable(viz.INTERSECTION)

#vizact.onupdate(0, updateRaycast, efrc)
vizact.onupdate(0, updateRaycasts, efrc, efrcL, efrcR)
exp.recorder.addTrackedNode(efrc, 'efrc')
exp.recorder.addTrackedNode(efrcL, 'efrcL')
exp.recorder.addTrackedNode(efrcR, 'efrcR')

# Fixation target
fix = vizshape.addSphere(exp.config.cursor_size, color=viz.RED, alpha=0.9)
fix.emissive(viz.RED)
fix.disable(viz.INTERSECTION)
fix.visible(False)

# Calibration target
cal = vizshape.addSphere(exp.config.cursor_size, color=viz.GREEN, alpha=0.9)
cal.emissive(viz.GREEN)
cal.disable(viz.INTERSECTION)
cal.visible(False)

# Occluders
occ_left = vizshape.addPlane([0.5, 2.0], color=viz.BLACK, axis=vizshape.AXIS_Z)
occ_left.setPosition(-0.25, 1.0, -0.4)
occ_left.setEuler(180, 0, 0)
occ_left.disable(viz.INTERSECTION)
occ_right = vizshape.addPlane([0.5, 2.0], color=viz.BLACK, axis=vizshape.AXIS_Z)
occ_right.setPosition(0.25, 1.0, -0.4)
occ_right.setEuler(180, 0, 0)
occ_right.disable(viz.INTERSECTION)

occ_left.visible(False)
occ_right.visible(False)


# Experiment Task
# -----------------------------------------------------------------------------

def Main():

    # Request participant info
    yield exp.requestParticipantData()
    
    # Read offset calibration
    wrist_offset = [0, 0, 0]
    try:
        cal_json = 'wrist_offset_{:d}.json'.format(int(exp.participant.id))
        with open(cal_json, 'r') as jf:
            wrist_cal = json.load(jf)
            print(wrist_cal)
            exp.config.wrist_cal = wrist_cal
            wrist_offset = wrist_cal['average_offset']
    except:
        print('!! Warning: no wrist tracker calibration file found for this participant!')
    exp.config.wrist_offset = wrist_offset
    finger_cursor.setPosition(exp.config.wrist_offset, mode=viz.REL_PARENT)

    # Set up controller button logging
    vizact.onsensordown(controller, steamvr.BUTTON_TRIGGER, exp.recorder.setCustomVar, 'button', 1)
    vizact.onsensorup(controller, steamvr.BUTTON_TRIGGER, exp.recorder.setCustomVar, 'button', 0)
    
    # Initial start position: S, facing N wall
    print(exp.config)
    if HAS_VR:
        navigationNode.setPosition(exp.config.start_pos['S'])
        navigationNode.setEuler(exp.config.start_ori['S'], 0, 0, viz.ABS_GLOBAL)
        
    else:
        viz.MainView.setPosition(exp.config.start_pos['S'])
        viz.MainView.setEuler(exp.config.start_ori['S'], 0, 0, viz.ABS_GLOBAL)
    
    # Welcome message
    yield wallText('Willkommen zu unserer Zeige-Studie!\n\nZunächst müssen wir den Eyetracker kalibrieren.\nDrücke die Controller-Taste zum Starten und folge den Hinweisen.')
    yield exp.recorder.calibrateEyeTracker()

    yield wallText('Bitte schaue nun noch einmal auf jeden schwarzen Punkt, bis das Ziel grün wird.\nDrücke die Controller-Taste zum Starten.')
    val = yield exp.recorder.validateEyeTracker(targets=VAL_TAR_CR5)
    print(val)

    yield wallText('Nun kalibrieren wir noch deine Zeigebewegung.\nBitte schaue und zeige jeweils auf den grünen Punkt\nund drücke die linke Controller-Taste!')
    
    # Main Trial Loop
    cal_done = False
    while not exp.done:

        exp.startNextTrial()
        
        # Move participant to starting location
        if HAS_VR:
            navigationNode.setPosition(exp.config.start_pos[exp.currentTrial.params.start_pos])
            navigationNode.setEuler(exp.config.start_ori[exp.currentTrial.params.start_pos], 0, 0, viz.ABS_GLOBAL)
            
        else:
            viz.MainView.setPosition(exp.config.start_pos[exp.currentTrial.params.start_pos])
            viz.MainView.setEuler(exp.config.start_ori[exp.currentTrial.params.start_pos], 0, 0, viz.ABS_GLOBAL)
        
        # Set up visible objects
        hideAllObjects(allobj)
        if exp.currentTrial.params.type == 'cal':
            table.visible(False)
            cal.setPosition(cal_pos[exp.currentTrial.params.tar])
            cal.visible(True)
            exp.currentTrial.results.tar_x = cal_pos[exp.currentTrial.params.tar][0]
            exp.currentTrial.results.tar_y = cal_pos[exp.currentTrial.params.tar][1]

        elif exp.currentTrial.params.type == 'obj':
            if not cal_done:
                cal_done = True
                yield wallText('Jetzt geht es los. Fixiere jeweils zuerst den roten Punkt.\nWenn das Objekt erscheint, zeige darauf und drücke die linke Taste.')
                
            table.setPosition(0.0, exp.currentTrial.params.table_height - 1.0, 0.0)
            table.visible(False)            
            fix.setPosition(fix_pos[exp.currentTrial.params.start_pos])
            fix.visible(True)

        # Select the correct feedback
        if exp.currentTrial.params.feedback == 'hand':
            handR.visible(True)
            finger_cursor.visible(False)

        elif exp.currentTrial.params.feedback == 'cursor':
            handR.visible(False)
            finger_cursor.visible(True)

        elif exp.currentTrial.params.feedback == 'none':
            handR.visible(False)
            finger_cursor.visible(False)

        # World fade in
        if exp.currentTrial.params.type == 'obj':
            yield fadeExposure(fader, 0, exp.config.fade_dur)
        
        # Calibration trial: wait for button press only            
        if exp.currentTrial.params.type == 'cal':
            exp.currentTrial.results.t_fix_on = -1.0
            exp.currentTrial.results.t_fixated = -1.0

        # Pointing trial: wait for fixation, then show object
        elif exp.currentTrial.params.type == 'obj':
            exp.currentTrial.results.t_fix_on = viz.tick()
            yield exp.recorder.waitGazeNearTarget(fix.getPosition(), tolerance=1.5)
            exp.currentTrial.results.t_fixated = viz.tick()
            yield viztask.waitTime(0.5)
            
            # Set occluder based on trial file
            if exp.currentTrial.params.occluded == 'left':
                occ_left.visible(True)
                occ_right.visible(False)
            elif exp.currentTrial.params.occluded == 'right':
                occ_left.visible(False)
                occ_right.visible(True)
            else:
                occ_left.visible(False)
                occ_right.visible(False)

            # Show table and obejct together
            fix.visible(False)
            table.visible(True)
            showObject(allobj, exp.currentTrial.params.object, 
                       position=[0.0, exp.currentTrial.params.table_height, 0.0], 
                       scale=exp.config.object_scale,
                       yaw=exp.currentTrial.params.obj_angle,
                       material=exp.currentTrial.params.obj_material)
            exp.recorder.custom_vars.object_visible = 1
        
        # Wait until button press to confirm pointing
        if HAS_VR:            
            hit = yield viztask.waitSensorDown(None, steamvr.BUTTON_TRIGGER)
            exp.currentTrial.results.t_confirm = viz.tick()
            exp.currentTrial.results.button = hit.button
        else:
            hit = yield viztask.waitKeyDown(' ')
            exp.currentTrial.results.t_confirm = hit.time
            exp.currentTrial.results.button = 'spacebar'

        # Save position and vector data for this trial
        # Combined EFRC
        ray_end = efrc.getPosition()
        ray_vec = efrc.dirVector
        exp.currentTrial.results.efrc_x = ray_end[0]
        exp.currentTrial.results.efrc_y = ray_end[1]
        exp.currentTrial.results.efrc_z = ray_end[2]
        exp.currentTrial.results.efrc_dir_x = ray_vec[0]
        exp.currentTrial.results.efrc_dir_y = ray_vec[1]
        exp.currentTrial.results.efrc_dir_z = ray_vec[2]

        # Left eye EFRC
        ray_endL = efrcL.getPosition()
        ray_vecL = efrcL.dirVector
        exp.currentTrial.results.efrcL_x = ray_endL[0]
        exp.currentTrial.results.efrcL_y = ray_endL[1]
        exp.currentTrial.results.efrcL_z = ray_endL[2]
        exp.currentTrial.results.efrcL_dir_x = ray_vecL[0]
        exp.currentTrial.results.efrcL_dir_y = ray_vecL[1]
        exp.currentTrial.results.efrcL_dir_z = ray_vecL[2]

        # Right eye EFRC
        ray_endR = efrcR.getPosition()
        ray_vecR = efrcR.dirVector
        exp.currentTrial.results.efrcR_x = ray_endR[0]
        exp.currentTrial.results.efrcR_y = ray_endR[1]
        exp.currentTrial.results.efrcR_z = ray_endR[2]
        exp.currentTrial.results.efrcR_dir_x = ray_vecR[0]
        exp.currentTrial.results.efrcR_dir_y = ray_vecR[1]
        exp.currentTrial.results.efrcR_dir_z = ray_vecR[2]

        # Gaze
        gaze_end = exp.recorder.getCurrentGazePoint()
        gaze_vec = exp.recorder.getCurrentGazeMatrix().getForward()
        exp.currentTrial.results.gaze_x = gaze_end[0]
        exp.currentTrial.results.gaze_y = gaze_end[1]
        exp.currentTrial.results.gaze_z = gaze_end[2]
        exp.currentTrial.results.gaze_dir_x = gaze_vec[0]
        exp.currentTrial.results.gaze_dir_y = gaze_vec[1]
        exp.currentTrial.results.gaze_dir_z = gaze_vec[2]

        # Hand cursor and hand model bone
        hc = finger_cursor.getPosition(viz.ABS_GLOBAL)
        gc = glove_index.getPosition(viz.ABS_GLOBAL)
        exp.currentTrial.results.index_x = hc[0]
        exp.currentTrial.results.index_y = hc[1]
        exp.currentTrial.results.index_z = hc[2]
        exp.currentTrial.results.glove_x = gc[0]
        exp.currentTrial.results.glove_y = gc[1]
        exp.currentTrial.results.glove_z = gc[2]

        # Participant position re: floor
        pp = viz.MainView.getPosition(viz.ABS_GLOBAL)
        exp.currentTrial.results.standing_x = pp[0]
        exp.currentTrial.results.standing_z = pp[2]

        # Hide object and table, reset occluders
        occ_left.visible(False)
        occ_right.visible(False)
        cal.visible(False)
        table.visible(False)
        hideAllObjects(allobj)
        exp.recorder.custom_vars.object_visible = 0

        yield viztask.waitTime(0.25)
        exp.endCurrentTrial()
                
        # World fade out
        if exp.currentTrial.params.type == 'obj':
            yield fadeExposure(fader, -6, exp.config.fade_dur)
            
    
    exp.saveTrialData(rec_data='single')
    exp.saveExperimentData(exp.output_file_name + '_all.json')
    viz.quit()


viztask.schedule(Main)