import sys
import time

from PySide6.QtWidgets import QApplication

import app_placabase_gui as gui


def main():
    try:
        app = QApplication(sys.argv)
        w = gui.MainWindow()
        w.show()

        # ensure at least one row exists
        if w.centers_table.rowCount() == 0:
            w.add_row()

        # instrument PreviewWidget.paintEvent to print when called
        orig_paint = gui.PreviewWidget.paintEvent

        def new_paint(self, event):
            try:
                # locate main window ancestor similar to widget logic
                parent = self.parent()
                while parent is not None and not hasattr(parent, 'hcol_edit'):
                    parent = parent.parent()
                H = parent.hcol_edit.text() if parent and hasattr(parent, 'hcol_edit') else 'N/A'
                B = parent.bcol_edit.text() if parent and hasattr(parent, 'bcol_edit') else 'N/A'
                centers = []
                if parent and hasattr(parent, 'centers_table'):
                    for r in range(parent.centers_table.rowCount()):
                        itx = parent.centers_table.item(r, 0)
                        ity = parent.centers_table.item(r, 1)
                        centers.append((itx.text() if itx else '', ity.text() if ity else ''))
                print(f"Preview.paintEvent called: H={H}, B={B}, centers={centers}")
            except Exception as e:
                print(f"Error in instrumentation: {e}")
            orig_paint(self, event)

        gui.PreviewWidget.paintEvent = new_paint

        # initial repaint
        print("Initial repaint")
        w.preview.repaint()
        app.processEvents()
        time.sleep(0.2)

        # change H_col and B_col programmatically
        print("Changing H_col to 500 and B_col to 400")
        w.hcol_edit.setText("500")
        w.bcol_edit.setText("400")

        # update table first cell
        print("Updating centers table first row to (10,20)")
        w.centers_table.setItem(0, 0, gui.QTableWidgetItem('10'))
        w.centers_table.setItem(0, 1, gui.QTableWidgetItem('20'))

        # force repaint and process events
        w.preview.repaint()
        app.processEvents()
        time.sleep(0.2)

        print("Test complete - closing")
        w.close()
        app.quit()
    except Exception as e:
        print(f"Test failed with exception: {e}")


if __name__ == '__main__':
    main()
