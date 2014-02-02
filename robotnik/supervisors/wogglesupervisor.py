#!/usr/bin/python
# coding: utf-8


from math import degrees, sqrt
from robots.robot import Robot
from controllers.controller import GoToGoal, Rotate
from utils import const
from supervisors.supervisor import Supervisor
from utils import const

from PyQt4 import QtCore

class WoggleSupervisor(Supervisor):
    """ WoggleSupervisor is a class that provides a way to control a Woggle robot
    """

    def __init__(self, robot_):
        """
        """
        # Call parent constructor
        super(WoggleSupervisor, self,).__init__(robot_);

    # Select and execute the current controller
    # The step duration is in seconds
    def execute(self, ):
        """
        """

        if self.isAtGoal() or self.robot.isStopped():
            self.robot.setWheelSpeeds(0, 0)
            return

        # Execute the controller to obtain parameters to apply to the robot
        v, w = self.controller.execute(self.stateEstimate, self.goal, const.stepDuration)

        # Convert speed (in m/s) and angular rotation (in rad/s) to
        # angular speed to apply to each robot wheels (in rad/s)
        vel_l, vel_r = self.robot.getDynamics().uni2Diff(v, w)

        # Apply current speed to wheels
        self.robot.setWheelSpeeds(vel_l, vel_r)

        # Update the estimate of the robot position
        self.updateOdometry()

    def updateOdometry(self, ):
        """
        """
        # For now, get exact robot position (in m) and angle (in rad)
        self.stateEstimate = [self.robot.pos(), self.robot.getTheta()]