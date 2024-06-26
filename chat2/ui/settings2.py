# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SettingsWindow2(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(495, 313)
        MainWindow.setStyleSheet("*{  \n"
"    font-family:微软雅黑;\n"
"    font-size:20px;\n"
"    color: #1d649c;\n"
"}\n"
"QPushButton{\n"
"    border:1px solid #1d649c;\n"
"}\n"
"QPushButton:hover{\n"
"    color: rgb(85, 255, 255);\n"
"}\n"
"")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_ip = QtWidgets.QLabel(self.centralwidget)
        self.label_ip.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_ip.setObjectName("label_ip")
        self.horizontalLayout.addWidget(self.label_ip)
        self.lineEdit_ip = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_ip.setObjectName("lineEdit_ip")
        self.horizontalLayout.addWidget(self.lineEdit_ip)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 8)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_port = QtWidgets.QLabel(self.centralwidget)
        self.label_port.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_port.setObjectName("label_port")
        self.horizontalLayout_2.addWidget(self.label_port)
        self.lineEdit_port = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_port.setObjectName("lineEdit_port")
        self.horizontalLayout_2.addWidget(self.lineEdit_port)
        self.horizontalLayout_2.setStretch(0, 2)
        self.horizontalLayout_2.setStretch(1, 8)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_name = QtWidgets.QLabel(self.centralwidget)
        self.label_name.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_name.setObjectName("label_name")
        self.horizontalLayout_3.addWidget(self.label_name)
        self.lineEdit_name = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_name.setObjectName("lineEdit_name")
        self.horizontalLayout_3.addWidget(self.lineEdit_name)
        self.horizontalLayout_3.setStretch(0, 2)
        self.horizontalLayout_3.setStretch(1, 8)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_yes = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_yes.setObjectName("pushButton_yes")
        self.horizontalLayout_4.addWidget(self.pushButton_yes)
        self.pushButton_no = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_no.setObjectName("pushButton_no")
        self.horizontalLayout_4.addWidget(self.pushButton_no)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 495, 33))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "设置"))
        self.label_ip.setText(_translate("MainWindow", "IP地址："))
        self.label_port.setText(_translate("MainWindow", "端口号："))
        self.label_name.setText(_translate("MainWindow", "昵称："))
        self.pushButton_yes.setText(_translate("MainWindow", "确定"))
        self.pushButton_no.setText(_translate("MainWindow", "取消"))
