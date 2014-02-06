#!/usr/bin/python
# coding: utf-8

from shape.shape import Shape
from math import pi, tan, degrees
from utils import const

from PyQt4 import QtGui, QtCore

class ProximitySensor(Shape):
    """ ProximitySensor class represents a generic class for proximity sensors
    """

    def __init__(self, name_, parent_, location_, beamAngle_):
        """
        """
        super(ProximitySensor, self).__init__(name_, parent_)

        # Location on the parent object (in m)
        self.setPos(location_)

        # angle of the beam (in rad)
        self.setTheta(beamAngle_)

        # View angle (in rad)
        self.spread = pi/8

        # Minimum range (in m)
        self.minRange = 0.001

        # Maximum range (in m)
        self.maxRange = 0.12

        # Current range (in m)
        self.currRange = self.maxRange

        # Brush color
        self.brushColor = QtGui.QColor('red')
        self.brushColor.setAlpha(50)
        self.brush = QtGui.QBrush(self.brushColor)

        # Pen color
        self.penColor = QtGui.QColor('red')
        self.penColor.setAlpha(128)
        self.pen = QtGui.QPen(QtCore.Qt.NoPen)

    def show(self, show_):
        if show_:
            self.brush = QtGui.QBrush(self.brushColor)
        else:
            self.brush = QtGui.QBrush(QtCore.Qt.NoBrush)

        # Trigger an update of the view
        self.update()

    def getMaxBeamRange(self, ):
        return self.maxRange

    # Restart the sensor to its initial state
    def restart(self, ):
        """
        """
        self.needReduction = False
        self.currRange = self.maxRange

    # Check if current range > minrange
    def isMinRangeReached(self, ):
        return self.currRange <= self.minRange

    def isMaxRangeReached(self, ):
        return self.currRange >= self.maxRange

    # Get current beam range (in m)
    def getBeamRange(self, ):
        """
        """
        return self.currRange

    # Set current beam range (in m)
    def setBeamRange(self, range_):
        """
        """
        self.currRange = range_

    # Reduce beam range (in m)
    def reduceBeamRange(self, reduce_):
        """
        """
        self.currRange = self.currRange - reduce_

    # Increase beam range (in m)
    def increaseBeamRange(self, increase_):
        """
        """
        self.currRange = self.currRange + increase_

    # Return the left limit of the beam (in m)
    def getBeamLeftLimit(self, ):
        """
        """
        return QtCore.QPointF(self.currRange, -self.currRange * tan(self.spread/2))

    # Return the right limit of the beam (in m)
    def getBeamRightLimit(self, ):
        """
        """
        return QtCore.QPointF(self.currRange, self.currRange * tan(self.spread/2))

    # Return an estimate of the area painted by the item
    def boundingRect(self, ):
        """
        """
        rectX = 0
        rectY = -self.currRange * tan(self.spread/2)
        rectW = self.currRange
        rectH = 2 * self.currRange * tan(self.spread/2)

        return QtCore.QRectF(rectX, rectY, rectW, rectH)

    # Define the accurate shape of the item
    def shape(self, ):
        """
        """
        path = QtGui.QPainterPath()

        leftLimit = self.getBeamLeftLimit()
        leftLimit = QtCore.QPointF(leftLimit.x() , leftLimit.y())
        rightLimit = self.getBeamRightLimit()
        rightLimit = QtCore.QPointF(rightLimit.x() , rightLimit.y())

        path.addPolygon(QtGui.QPolygonF([QtCore.QPointF(0,0), leftLimit, rightLimit]))

        return path

    # Define how to paint the shape
    def paint(self, painter, option, widget):
        """
        """
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        leftLimit = self.getBeamLeftLimit()
        leftLimit = QtCore.QPointF(leftLimit.x() , leftLimit.y())

        rightLimit = self.getBeamRightLimit()
        rightLimit = QtCore.QPointF(rightLimit.x() , rightLimit.y())

        painter.drawPolygon(QtCore.QPointF(0,0), leftLimit, rightLimit)
