import QtQuick
import QtQuick.Controls

Item {
    id: root

    width: 1400
    height: 900

    property string activeTool: "SELECT"

    Rectangle {
        anchors.fill: parent
        color: "transparent"
    }

    Rectangle {
        x: 20
        y: 18
        width: parent.width - 40
        height: 62

        color: "#CC080C12"
        border.color: "#553A4A58"
        border.width: 1
        radius: 12

        Rectangle {
            x: 1
            y: 1
            width: parent.width - 2
            height: 2
            radius: 1
            color: "#55FF8A24"
        }

        Text {
            x: 20
            y: 10
            text: "AI3D STUDIO"
            color: "#FF8A24"
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            x: 21
            y: 37
            text: "3D DESIGN ENVIRONMENT"
            color: "#7C8B98"
            font.pixelSize: 9
            font.bold: true
        }

        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: 18
            y: 16
            width: 118
            height: 30

            color: "#182019"
            border.color: "#00D98B"
            border.width: 1
            radius: 7

            Text {
                anchors.centerIn: parent
                text: "●  SYSTEM ONLINE"
                color: "#00E89A"
                font.pixelSize: 9
                font.bold: true
            }
        }

        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: 145
            y: 16
            width: 92
            height: 30

            color: "#1D140D"
            border.color: "#FF8A24"
            border.width: 1
            radius: 7

            Text {
                anchors.centerIn: parent
                text: "AI READY"
                color: "#FF8A24"
                font.pixelSize: 9
                font.bold: true
            }
        }
    }

    Rectangle {
        id: toolsPanel

        x: 20
        y: 100
        width: 128
        height: 520

        color: "#C90A0F15"
        border.color: "#553A4A58"
        border.width: 1
        radius: 12

        Rectangle {
            x: 5
            y: 5
            width: parent.width
            height: parent.height
            color: "#30000000"
            radius: 12
            z: -1
        }

        Text {
            x: 16
            y: 16
            text: "TOOLS"
            color: "#FF8A24"
            font.pixelSize: 11
            font.bold: true
        }

        Rectangle {
            x: 16
            y: 40
            width: 96
            height: 1
            color: "#333A4A58"
        }

        Column {
            x: 14
            y: 55
            width: 100
            spacing: 8

            Repeater {
                model: [
                    "SELECT",
                    "MOVE",
                    "ROTATE",
                    "SCALE",
                    "SKETCH",
                    "CAD",
                    "AI"
                ]

                delegate: Rectangle {
                    width: 100
                    height: 43

                    color: root.activeTool === modelData
                           ? "#38FF8A24"
                           : "#22141A21"

                    border.color: root.activeTool === modelData
                                  ? "#FF8A24"
                                  : "#303A4A58"

                    border.width: 1
                    radius: 8

                    Behavior on color {
                        ColorAnimation {
                            duration: 120
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: modelData

                        color: root.activeTool === modelData
                               ? "#FFB15F"
                               : "#B7C2CC"

                        font.pixelSize: 10
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent

                        onClicked: {
                            root.activeTool = modelData
                            backend.setTool(modelData)
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: rightPanel

        anchors.right: parent.right
        anchors.rightMargin: 20
        y: 100
        width: 290
        height: 620

        color: "#C90A0F15"
        border.color: "#553A4A58"
        border.width: 1
        radius: 12

        Rectangle {
            x: 5
            y: 5
            width: parent.width
            height: parent.height
            color: "#30000000"
            radius: 12
            z: -1
        }

        Rectangle {
            x: 10
            y: 10
            width: parent.width - 20
            height: 190

            color: "#B80C1118"
            border.color: "#383A4A58"
            border.width: 1
            radius: 9

            Text {
                x: 14
                y: 13
                text: "SCENE HIERARCHY"
                color: "#FF8A24"
                font.pixelSize: 10
                font.bold: true
            }

            Rectangle {
                x: 14
                y: 35
                width: parent.width - 28
                height: 1
                color: "#303A4A58"
            }

            Text {
                x: 14
                y: 54
                text: "Scene"
                color: "#FFFFFF"
                font.pixelSize: 11
            }

            Text {
                x: 27
                y: 84
                text: "No QML hierarchy data"
                color: "#667583"
                font.pixelSize: 10
            }
        }

        Rectangle {
            x: 10
            y: 212
            width: parent.width - 20
            height: 155

            color: "#B80C1118"
            border.color: "#383A4A58"
            border.width: 1
            radius: 9

            Text {
                x: 14
                y: 13
                text: "PROPERTIES"
                color: "#FF8A24"
                font.pixelSize: 10
                font.bold: true
            }

            Rectangle {
                x: 14
                y: 35
                width: parent.width - 28
                height: 1
                color: "#303A4A58"
            }

            Text {
                x: 14
                y: 53
                text: "POSITION"
                color: "#697987"
                font.pixelSize: 8
            }

            Text {
                x: 14
                y: 70
                text: "0.00     0.00     0.00"
                color: "#D7DEE5"
                font.pixelSize: 9
            }

            Text {
                x: 14
                y: 94
                text: "ROTATION"
                color: "#697987"
                font.pixelSize: 8
            }

            Text {
                x: 14
                y: 111
                text: "0.00     0.00     0.00"
                color: "#D7DEE5"
                font.pixelSize: 9
            }

            Text {
                x: 14
                y: 135
                text: "SCALE"
                color: "#697987"
                font.pixelSize: 8
            }

            Text {
                x: 14
                y: 152
                text: "1.00     1.00     1.00"
                color: "#D7DEE5"
                font.pixelSize: 9
            }
        }

        Rectangle {
            id: webcamPanel

            x: 10
            y: 380
            width: parent.width - 20
            height: parent.height - 390

            color: "#D5020407"
            border.color: "#66FF8A24"
            border.width: 1
            radius: 9
            clip: true

            Text {
                z: 2

                x: 14
                y: 12

                text: "HAND TRACKING"
                color: "#FF8A24"
                font.pixelSize: 10
                font.bold: true
            }

            Text {
                z: 2

                x: 14
                y: 30

                text: "CAMERA"
                color: "#647380"
                font.pixelSize: 8
                font.bold: true
            }

            Rectangle {
                anchors.fill: parent
                anchors.margins: 2

                color: "transparent"
                border.color: "#223A4A58"
                border.width: 1
                radius: 7
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 48
                height: 1

                color: "#333A4A58"
            }

            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 15

                text: "OPENGL CAMERA"
                color: "#53616D"
                font.pixelSize: 9
                font.bold: true
            }

            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 34

                text: "HAND TRACKING ACTIVE"
                color: "#00D98B"
                font.pixelSize: 8
            }

            Rectangle {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 10
                anchors.bottomMargin: 10

                width: 82
                height: 24

                color: "#CC07100C"
                border.color: "#00D98B"
                border.width: 1
                radius: 6

                Text {
                    anchors.centerIn: parent
                    text: "● LIVE"
                    color: "#00E89A"
                    font.pixelSize: 9
                    font.bold: true
                }
            }
        }
    }

    Rectangle {
        id: commandPanel

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 170
        anchors.rightMargin: 340
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 22

        height: 62

        color: "#D0080D13"
        border.color: "#553A4A58"
        border.width: 1
        radius: 12

        Rectangle {
            x: 1
            y: 1
            width: 4
            height: parent.height - 2

            color: "#FF8A24"
            radius: 2
        }

        Text {
            x: 20
            y: 10

            text: "AI COMMAND"
            color: "#FF8A24"
            font.pixelSize: 9
            font.bold: true
        }

        Text {
            x: 20
            y: 32

            text: "> Ready for command..."
            color: "#748391"
            font.pixelSize: 10
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 22
            y: 12

            text: "TOOL  " + root.activeTool
            color: "#D9E1E7"
            font.pixelSize: 9
            font.bold: true
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 22
            y: 34

            text: "HAND TRACKING  ●"
            color: "#00D98B"
            font.pixelSize: 9
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.leftMargin: 20
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 12

        width: 128
        height: 2

        color: "#66FF8A24"
    }

    Rectangle {
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 12

        width: 290
        height: 2

        color: "#66FF8A24"
    }
}