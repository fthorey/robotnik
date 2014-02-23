#!/usr/bin/python
# coding: utf-8

from utils.simobject import SimObject
from math import pi, tan, degrees, cos, sin, sqrt

from PyQt4 import QtGui, QtCore

class ProximitySensor(SimObject):
    """ The ProximitySensor class represents a generic class for proximity sensors
    """

    # Overall number of proximity sensors in the world
    count = 0

    def __init__(self, pos_):

        # Call parent constructor
        super(ProximitySensor, self).__init__('sharp' + str(self.count),
                                              QtCore.Qt.NoBrush,
                                              QtCore.Qt.NoPen)
        # Increment by 1 the number of proximity sensors in the world
        self.count = self.count + 1

        # Location on the parent object (in m)
        self.setPos(pos_[0])

        # angle of the beam (in rad)
        self.setAngle(pos_[1])

        # View angle (in rad)
        self._phi = pi/10

        # Minimum range (in m)
        self._rmin = 0.01

        # Maximum range (in m)
        self._rmax = 0.10

        # Maximum detection distance of the sensor (in m)
        self._maxDist = 65536

        # Current detection ditance of the sensor (in m)
        self._currDist = self._maxDist

        # The current cone of the sensor
        self._envelope = self.getCone(self._rmax)

        # Update current bounding rect
        self.__updateBoundingRect()

        # Update current shape
        self.__updateShape()

        # Brush colors
        self._brushColorNoCol = QtGui.QColor(0xFF5566)
        self._brushColorNoCol.setAlpha(70)
        self._brushColorCol = QtGui.QColor(0xFF5566)

        # Set brush
        self.setBrush(QtGui.QBrush(self._brushColorNoCol))

        # Pen color
        self.setPen(QtGui.QPen(QtCore.Qt.NoPen))

    def __updateBoundingRect(self, ):
        """Update the bounding rectangle of the sensor
        """
        xmin, ymin, xmax, ymax = self.getBounds()
        self._boundingRect = QtCore.QRectF(QtCore.QPointF(xmin, ymin), QtCore.QPointF(xmax, ymax))

    def __updateShape(self, ):
        """Update the shape of the sensor
        """
        points = [QtCore.QPointF(p[0], p[1]) for p in self._envelope]
        self._shape = QtGui.QPainterPath()
        self._shape.addPolygon(QtGui.QPolygonF(points))

    def isAtMaxRange(self, ):
        """Check if the sensor is at its maximum range or not
        """
        return self._currDist == self._maxDist

    def getCone(self, distance):
        """Get the envelope of the beam of the sensor
        """
        return [(self._rmin*cos(self._phi/2),self._rmin*sin(self._phi/2)),
                (distance*cos(self._phi/2),distance*sin(self._phi/2)),
                (distance,0),
                (distance*cos(self._phi/2),-distance*sin(self._phi/2)),
                (self._rmin*cos(self._phi/2),-self._rmin*sin(self._phi/2))]

    def show(self, show_):
        """Choose wether to draw the proximity sensor on screen or not
        """
        if show_:
            self._brush = QtGui.QBrush(self._brushColor)
        else:
            self._brush = QtGui.QBrush(QtCore.Qt.NoBrush)

        # Trigger an update of the view
        self.update()

    def restart(self, ):
        """Restart the sensor to its initial state
        """
        # Set the envelope to its maximum value
        self._envelope = self.getCone(self._rmax)
        # Change brush color
        self.setBrush(QtGui.QBrush(self._brushColorNoCol))

    def getEnvelope(self):
        """Return the envelope of the sensor
        """
        return self._envelope

    def boundingRect(self, ):
        """Return the bounding rectangle of the sensor
        """
        return self._boundingRect

    def shape(self, ):
        """Return the shape of the sensor
        """
        return self._shape

    def updateDistance(self, simObject = None):
        """updates all the distances from the reading
        """
        if simObject is None:
            # reset distance to max
            self._currDist = self._maxDist
            self._envelope = self.getCone(self._rmax)
            # change brush color
            self.setBrush(QtGui.QBrush(self._brushColorNoCol))
        else:
            distance2obj = self.getDistanceTo(simObject)
            if distance2obj:
                if self._currDist > distance2obj:
                    # Update current distance
                    self._currDist = distance2obj
                    # Update envelope
                    self._envelope = self.getCone(self._currDist)
                    # Change brush color
                    self.setBrush(QtGui.QBrush(self._brushColorCol))
        # Update bounding rect and shape
        self.__updateBoundingRect()
        self.__updateShape()

    def getDistanceTo(self, simObject):
        """Gets the distance to another simObject
        returns distance in meters or None if not in contact
        """
        pos = self.parentItem().mapToScene(self.pos())
        ox, oy = pos.x(), pos.y()
        minDist = None
        for px, py in self.getContactPoints(simObject):
            distance = sqrt((px-ox)*(px-ox)+(py-oy)*(py-oy))
            if minDist is not None:
                if distance < minDist:
                    minDist = distance
            else: minDist = distance
        return minDist

    # Define how to paint the shape
    def paint(self, painter, option, widget):
        """Paints the shape on screen
        """
        painter.setBrush(self.brush())
        painter.setPen(self.pen())

        points = [QtCore.QPointF(p[0], p[1]) for p in self._envelope]
        painter.drawPolygon(QtGui.QPolygonF(points))
