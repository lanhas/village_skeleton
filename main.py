import sys
from PyQt5.QtWidgets import QApplication
from controller import AxisTrans
from PyQt5.QtGui import QIcon, QPixmap

if __name__ == "__main__":
    app = QApplication(sys.argv)
    axistrans = AxisTrans()
    axistrans.setWindowTitle('村落骨架提取')
    icon = QIcon()
    icon.addPixmap(QPixmap('function/axis_trans/resource/glass.png'))
    axistrans.setWindowIcon(icon)
    axistrans.show()
    sys.exit(app.exec_())