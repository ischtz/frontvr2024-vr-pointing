# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Experiment UI

import viz
import vizinfo
import vizdlg

from .experiment import Experiment, Trial


class ExperimentUI(object):

    def __init__(self, experiment):
        if type(experiment) != Experiment:
            raise ValueError('ExperimentUI requires a valid Experiment instance as first argument!')

        self._exp = experiment
        self._createUI()
        self.updateTrialList()


    def _createUI(self):
        """ Set up major UI elements """
        self._ui = vizdlg.TabPanel(align=viz.ALIGN_RIGHT_TOP, border=True)

        self._ui_trials = vizdlg.GridPanel(border=False)
        self._ui_trials_rows = []
        self._tp_trials = self._ui.addPanel('Trials', self._ui_trials)
        self._tp_trials.setCellPadding(0)
        self._ui.addItem(self._ui_trials)

        self._ui_config = vizdlg.GridPanel(border=False)
        self._ui_config_rows = []
        self._tp_config = self._ui.addPanel('Config', self._ui_config)

        viz.link(viz.RightTop, self._ui, offset=(-20,-20,0))


    def updateTrialList(self):
        """ Rebuilds list of trials in experiment UI """
        if len(self._ui_trials_rows) > 0:
            for row in self._ui_trials_rows:
                self._ui_trials.removeRow(row)
            self._ui_trials_rows = []
        
        header = self._ui_trials.addRow([viz.addText('Trial'),
                                         viz.addText('Status')])
        self._ui_trials_rows.append(header)

        for t in self._exp.trials:
            r = self._ui_trials.addRow([viz.addText(str(t.number)),
                                         viz.addText(t.status)])
            self._ui_trials_rows.append(r)


    def updateConfig(self):
        """ Rebuild list of config parameters """
        if len(self._ui_config_rows) > 0:
            for row in self._ui_config_rows:
                self._ui_config.removeRow(row)
            self._ui_config_rows = []

        for c in self._exp.config:
            label = viz.addText(str(c[0]))
            if type(c[1]) == bool:
                field = viz.addCheckbox()
                field.set(c[1])
            else:
                field = viz.addTextbox()
                field.message(str(c[1]))
            row = self._ui_config.addRow([label, field])
            self._ui_config_rows.append(row)


    def update(self):
        """ Update UI information """
        self.updateTrialList()
        self.updateConfig()