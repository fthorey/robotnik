#!/usr/bin/python
# coding: utf-8

from PyQt4 import QtGui, QtCore
from math import degrees
from common import const

class Shape(QtGui.QGraphicsItem):
    """ Shape class is the basic class for all objects in the simulator
    """

    def __init__(self, name_, parent=None):
        """
        """
        # Call parent constructor
        super(Shape, self).__init__(parent)

        # Name of the shape
        self.name = name_

        # Angle of the shape in its own referential (in rad)
        self.theta = 0

        # Main color of the shape
        self.color = QtGui.QColor(0, 0, 0)

    # Get the position of the shape in the world referential
    # -> In charge of converting position from pixel to m
    def pos(self, ):
        """
        """
        pos = super(Shape, self).scenePos()
        return QtCore.QPointF(pos.x()*const.pix2m, pos.y()*const.pix2m)

    # Set the position of the shape in the world referential
    # -> In charge of converting position from m to pixel
    def setPos(self, pos_):
        """
        """
        super(Shape, self).setPos(QtCore.QPointF(pos_.x()*const.m2pix, pos_.y()*const.m2pix))

    # Return the name of the shape
    def getName(self, ):
        """
        """
        return self.name

    # Return the current theta angle (in rad)
    def getTheta(self, ):
        """
        """
        return self.theta

    # Set the position of the shape (in rad)
    def setTheta(self, theta_):
        """
        """
        self.theta = theta_
        self.setRotation(degrees(self.theta))

    # Return an estimate of the area painted by the item
    def boundingRect(self, ):
        """
        """
        return QtCore.QRectF(-50, -50, 100, 100)

    # Define the accurate shape of the item
    def shape(self, ):
        """
        """
        path = QtGui.QPainterPath()
        path.addRect(-50, -50, 100, 100);
        return path;

    # Define how to paint the shape
    def paint(self, painter, option, widget):
        """
        """
        painter.setBrush(self.color);
        painter.drawRect(-50, -50, 100, 100)
