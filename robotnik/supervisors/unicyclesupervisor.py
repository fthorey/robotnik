#!/usr/bin/python
# coding: utf-8

from math import degrees, sqrt, cos, sin, pi, log1p, tan, atan2
from robots.robot import Robot
from controllers.gotogoal import GoToGoal
from controllers.avoidobstacle import AvoidObstacle
from controllers.followwall import FollowWall
from controllers.hold import Hold
from supervisors.supervisor import Supervisor
import numpy as np
import json

from PyQt4 import QtCore, QtGui

class UnicycleSupervisor(Supervisor):
    """ UnicycleSupervisor is a class that provides a way to control a Woggle robot.
    The UnicycleSupervisor does not move the robot directly. Instead, the supervisor
    selects a controller to do the work and uses the controller outputs
    to generate the robot inputs.
    """

    def __init__(self, robotInfo_, infoFile_):
        # Call parent constructor
        super(UnicycleSupervisor, self,).__init__(infoFile_);

        # Keep track of the position of the robot
        self._info["pos"] = robotInfo_["pos"]

        # Keep track of the old encoders values
        self._info["encoders"] = {}
        self._info["encoders"]["old_leftTicks"] = robotInfo_["encoders"]["leftTicks"]
        self._info["encoders"]["old_rightTicks"] = robotInfo_["encoders"]["rightTicks"]

        # Keep track of the wheels geometry values
        self._info["wheels"] = robotInfo_["wheels"].copy()

        # Keep track of the sensors informations
        self._info["sensors"] = robotInfo_["sensors"].copy()
        self._info["sensors"]["dist"] = self.getIRDistance(robotInfo_)
        self._info["sensors"]["toCenter"] = robotInfo_["sensors"]["ir"]["toCenter"]

        # Follow wall important information
        self._info["direction"] = "left"

        # Distance from center of robot to extremity of a sensor beam
        self._distMax = self._info["sensors"]["toCenter"] + robotInfo_["sensors"]["ir"]["rmax"]
        self._bestDistance = None

        # Create:
        # - a go-to-goal controller
        # - an avoid-obstacle controller
        # - a follow-wall controller
        # - a hold controller
        self._gtg = self.createController('gotogoal.GoToGoal', self._info)
        self._avd = self.createController('avoidobstacle.AvoidObstacle', self._info)
        self._hld = self.createController('hold.Hold', None)
        self._fow = self.createController('followwall.FollowWall', self._info)

        # Set GoToGoal transition functions
        self.addController(self._gtg,
                           (self.atGoal, self._hld),
                           (self.atWall, self._fow))
        # Set AvoidObstacle transition functions
        self.addController(self._avd,
                           (self.atGoal, self._hld),
                           (self.safe, self._fow))
        # Set Hold transition functions
        self.addController(self._hld,
                           (lambda: not self.atGoal(), self._gtg))
        # Set FollowWall transition functions
        self.addController(self._fow,
                           (self.atGoal, self._hld),
                           (self.unsafe, self._avd),
                           (self.wallCleared, self._gtg))

        # Set current controller to GoToGoal
        self._current = self._gtg

    def wallCleared(self, ):
        """Check if the robot should stop following the wall.
        """
        # Did we make progress?
        if self._toGoal >= self._bestDistance:
            return False

        # Are we far enough from the wall,
        # so that we don't switch back immediately
        if self.isAtWall():
            return False

        # Check if we have a clear shot to the goal
        theta_gtg = self._gtg.getHeadingAngle(self.info())
        dtheta = self._fow.getHeadingAngle(self.info()) - theta_gtg

        if self.info()["direction"] == 'right':
            dtheta = -dtheta

        return sin(dtheta) >= 0 and cos(dtheta) >= 0

    def safe(self, ):
        """Check if the surrounding is safe (i.e. no obstacle too close).
        """
        wallFar = self._distMin > self._distMax*0.6
        # Check which way to go
        if wallFar:
            self.atWall()
        return wallFar

    def unsafe(self, ):
        """Check if the surrounding is unsage (i.e. obstacle too close).
        """
        return self._distMin < self._distMax * 0.5

    def atGoal(self):
        """Check if the distance to goal is small.
        """
        return self._toGoal < self.info()["wheels"]["baseLength"]/2

    def isAtWall(self):
        """Check if the distance to obstacle is small.
        """
        # Detect a wall when it is at 80% of the distance
        # from the center of the robot
        return self._toWall < (self._distMax * 0.8)

    def atWall(self, ):
        """Check if the distance to wall is small and decide a direction.
        """
        wall_close = self.isAtWall()

        # Find the closest detected point
        if wall_close:
            dmin = self._distMax
            angle = 0
            for i, d in enumerate(self.info()["sensors"]["ir"]["dist"]):
                if d < dmin:
                    dmin = d
                    angle = self.info()["sensors"]["ir"]["insts"][i].angle()

            # Take the direction that follow the wall
            # on the right side
            if angle >= 0:
                self.info()["direction"] = 'left'
            else:
                self.info()["direction"] = 'right'

        # Save the closest we've been to the goal
        if self._bestDistance is None:
            self._bestDistance = self._toGoal

        if self._toGoal < self._bestDistance:
            self._bestDistance = self._toGoal

        return wall_close

    def getIRDistance(self, robotInfo_):
        """Converts the IR distance readings into a distance in meters.
        """
        # Get the current parameters of the sensor
        readings = robotInfo_["sensors"]["ir"]["readings"]
        rmin = robotInfo_["sensors"]["ir"]["rmin"]
        rmax = robotInfo_["sensors"]["ir"]["rmax"]

        #   Conver the readings to a distance (in m)
        dists = [max( min( (log1p(3960) - log1p(r))/30 + rmin, rmax), rmin) for r in readings]
        return dists

    def processStateInfo(self, robotInfo_):
        """Process the current estimation of the robot state.
        """
        # Get the number of ticks on each wheel since last call
        dtl = robotInfo_["encoders"]["leftTicks"] - self.info()["encoders"]["old_leftTicks"]
        dtr = robotInfo_["encoders"]["rightTicks"] - self.info()["encoders"]["old_rightTicks"]

        # Save the wheel encoder ticks for the next estimate
        self.info()["encoders"]["old_leftTicks"] += dtl
        self.info()["encoders"]["old_rightTicks"] += dtr

        # Get old state estimation (in m and rad)
        x, y, theta = self.info()["pos"]

        # Get robot parameters (in m)
        R = robotInfo_["wheels"]["radius"]
        L = robotInfo_["wheels"]["baseLength"]
        m_per_tick = (2*pi*R) / robotInfo_["encoders"]["ticksPerRev"]

        # distance travelled by left wheel
        dl = dtl*m_per_tick
        # distance travelled by right wheel
        dr = dtr*m_per_tick

        theta_dt = -(dr-dl)/L
        theta_mid = theta + theta_dt/2
        dst = (dr+dl)/2
        x_dt = dst*cos(theta_mid)
        y_dt = dst*sin(theta_mid)

        theta_new = theta + theta_dt
        x_new = x + x_dt
        y_new = y + y_dt

        # Process the state estimation
        self.info()["pos"] = (x_new, y_new, theta_new)

        # Process the sensors readings
        self.info()["sensors"]["ir"]["dist"] = self.getIRDistance(robotInfo_)

        # Smallest reading translated into distance from center of robot
        vectors = np.array([s.mapToParent(d, 0) for s, d in zip(self.info()["sensors"]["ir"]["insts"],
                                                                self.info()["sensors"]["ir"]["dist"])])
        self._distMin = min((sqrt(a[0]**2 + a[1]**2) for a in vectors))

        # Update goal
        self.info()["goal"] = self._planner.getGoal()

        # Distance to the goal
        self._toGoal = sqrt((x_new - self.info()["goal"]["x"])**2 +
                            (y_new - self.info()["goal"]["y"])**2)

        # Distance to the closest obstacle
        self._toWall = self.info()["sensors"]["toCenter"] + min(self.info()["sensors"]["ir"]["dist"])

    def drawHeading(self, painter, option=None, widget=None):
        """Draw the heading direction.
        """
        def drawArrow(painter, color, x1, y1, x2, y2, angle=0.5, ratio=0.1):
            """Draw an arrow.
            """
            # Save state
            painter.save()
            # Rotate and scale
            painter.rotate(degrees(atan2(y2-y1,x2-x1)))
            factor = sqrt((x1-x2)**2 + (y1-y2)**2)
            painter.scale(factor, factor)
            # Draw the arrow
            line = QtCore.QLineF(0, 0, 1, 0)
            xe = 1 - ratio
            ye = tan(angle) * ratio
            line1 = QtCore.QLineF(1, 0, xe, ye)
            line2 = QtCore.QLineF(1, 0, xe, -ye)
            painter.setPen(QtCore.Qt.SolidLine)
            painter.setPen(QtGui.QColor(color))
            painter.drawLine(line)
            painter.drawLine(line1)
            painter.drawLine(line2)
            # Restore state
            painter.restore()

        arrow_l = self.info()["wheels"]["baseLength"] * 2

        # # Draw Robot direction
        # drawArrow(painter, "green", 0, 0, arrow_l, 0)

        # Draw GoToGoal direction
        if self.currentController() is self._gtg:
            gtg_angle = self._gtg.getHeadingAngle(self.info())
            drawArrow(painter, "blue", 0, 0, arrow_l, 0)

        # Draw AvoidObstacle direction
        elif self.currentController() is self._avd:
            avd_angle = self._avd.getHeadingAngle(self.info())
            drawArrow(painter, "red", 0, 0, arrow_l, 0)

        # Draw FollowWall direction
        elif self.currentController() is self._fow:
            along_wall = self._fow._along_wall_vector
            to_wall = self._fow._to_wall_vector

            if to_wall is not None:
                to_angle = degrees(atan2(to_wall[1], to_wall[0]))
                drawArrow(painter, "green", 0, 0, to_wall[0], to_wall[1])
            if along_wall is not None:
                along_angle = degrees(atan2(along_wall[1], along_wall[0]))
                painter.translate(to_wall[0], to_wall[1])
                drawArrow(painter, "purple", 0, 0, along_wall[0], along_wall[1])