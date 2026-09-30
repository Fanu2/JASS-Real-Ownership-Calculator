import csv
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,
    QLineEdit,QPushButton,QTableWidget,QTableWidgetItem,QFileDialog,
    QMessageBox,QLabel,QSpinBox,QGroupBox,QHeaderView,QComboBox,QCheckBox,
    QTabWidget
)
from .jamabandi_parser import parse_html
from .land_math import area_to_sar,fraction_value,parse_area,format_kms,fraction_text

OWNER_HEADERS=["Owner Name","Recorded Fraction","Recorded Share","Sold / Deducted","Real Ownership","Real Fraction"]
LEDGER_HEADERS=["Khatoni","Cultivator / Buyer","Fraction","Khasra No.","Area","Deduct","Owner to Deduct From"]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JASS Real Ownership Calculator v2.0.0")
        self.resize(1450,850)
        self.owners=[]
        self._build()

    def _build(self):
        root=QWidget(); self.setCentralWidget(root); lay=QVBoxLayout(root)
        meta=QGroupBox("Jamabandi / Calculation Inputs")
        f=QFormLayout(meta)
        self.khewat=QLineEdit()
        self.village=QLineEdit()
        self.kanal=QSpinBox(); self.kanal.setRange(0,10000000)
        self.marla=QSpinBox(); self.marla.setRange(0,19)
        f.addRow("Khewat Number:",self.khewat)
        f.addRow("Village:",self.village)
        f.addRow("Total Area — Kanal:",self.kanal)
        f.addRow("Total Area — Marla:",self.marla)
        lay.addWidget(meta)

        b=QHBoxLayout()
        for txt,fn in [
            ("Import Jamabandi HTML",self.import_html),
            ("Calculate Real Ownership",self.calculate),
            ("Auto-Match Names",self.auto_match),
            ("Copy Result",self.copy_result),
            ("Export Result CSV",self.export_csv),
            ("Clear",self.clear_all)]:
            q=QPushButton(txt); q.clicked.connect(fn); b.addWidget(q)
        lay.addLayout(b)
        self.status=QLabel("Import the real Jamabandi HTML. The program separates recorded ownership from specific-number / Khana Kasht deductions.")
        lay.addWidget(self.status)

        tabs=QTabWidget()
        ownerw=QWidget(); ol=QVBoxLayout(ownerw)
        self.owner_table=QTableWidget(0,len(OWNER_HEADERS))
        self.owner_table.setHorizontalHeaderLabels(OWNER_HEADERS)
        self.owner_table.setAlternatingRowColors(True)
        self.owner_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.owner_table.horizontalHeader().setStretchLastSection(True)
        ol.addWidget(self.owner_table)
        tabs.addTab(ownerw,"Real Ownership")

        ledw=QWidget(); ll=QVBoxLayout(ledw)
        info=QLabel("Review the extracted Khana Kasht / specific-number entries. Only rows marked Deduct are subtracted. If the seller-owner cannot be established from the record, leave the owner blank rather than guessing.")
        info.setWordWrap(True); ll.addWidget(info)
        self.ledger=QTableWidget(0,len(LEDGER_HEADERS))
        self.ledger.setHorizontalHeaderLabels(LEDGER_HEADERS)
        self.ledger.setAlternatingRowColors(True)
        self.ledger.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ledger.horizontalHeader().setStretchLastSection(True)
        ll.addWidget(self.ledger)
        tabs.addTab(ledw,"Khana Kasht / Specific Numbers")
        lay.addWidget(tabs)

    def import_html(self):
        path,_=QFileDialog.getOpenFileName(self,"Open Jamabandi HTML","","HTML Files (*.htm *.html);;All Files (*)")
        if not path:return
        try:
            data=parse_html(path)
            self.village.setText(data.get("village",""))
            self.owners=data["owners"]
            self.owner_table.setRowCount(0)
            for o in self.owners:
                r=self.owner_table.rowCount(); self.owner_table.insertRow(r)
                self._set(self.owner_table,r,0,o["name"])
                self._set(self.owner_table,r,1,o["fraction"])
                self._set(self.owner_table,r,2,"")
                self._set(self.owner_table,r,3,"0-0-0")
                self._set(self.owner_table,r,4,"")
                self._set(self.owner_table,r,5,"")
            self.ledger.setRowCount(0)
            for x in data["cultivators"]:
                # Only useful entries: name/fraction/area/khasra.
                if not any((x["text"],x["fraction"],x["khasra"],x["area"])): continue
                r=self.ledger.rowCount(); self.ledger.insertRow(r)
                self._set(self.ledger,r,0,x["khatauni"])
                self._set(self.ledger,r,1,x["text"])
                self._set(self.ledger,r,2,x["fraction"])
                self._set(self.ledger,r,3,x["khasra"])
                self._set(self.ledger,r,4,x["area"])
                cb=QCheckBox()
                cb.setChecked(bool(x["deduct"]))
                self.ledger.setCellWidget(r,5,cb)
                combo=QComboBox(); combo.addItem("")
                combo.addItems([o["name"] for o in self.owners])
                self.ledger.setCellWidget(r,6,combo)
            self.status.setText(f"Imported {len(self.owners)} recorded owner-share entries and {self.ledger.rowCount()} cultivation entries. No seller linkage is guessed.")
        except Exception as e:
            QMessageBox.critical(self,"Import Error",str(e))

    def auto_match(self):
        # Exact normalized name matching only. No fuzzy seller inference.
        names={self.norm(o["name"]):i for i,o in enumerate(self.owners)}
        for r in range(self.ledger.rowCount()):
            combo=self.ledger.cellWidget(r,6)
            txt=self._text(self.ledger,r,1)
            key=self.norm(txt)
            if key in names:
                combo.setCurrentIndex(names[key]+1)
        self.status.setText("Exact-name matches applied only. No fuzzy seller inference was used.")

    def calculate(self):
        total=area_to_sar(self.kanal.value(),self.marla.value())
        if total<=0:
            QMessageBox.warning(self,"Total Area","Enter total area in Kanal and Marla.")
            return
        deductions=[0]*self.owner_table.rowCount()
        unassigned=0
        for r in range(self.ledger.rowCount()):
            cb=self.ledger.cellWidget(r,5)
            if not cb or not cb.isChecked(): continue
            amount=parse_area(self._text(self.ledger,r,4))
            if amount is None:
                frac=fraction_value(self._text(self.ledger,r,2))
                if frac is not None: amount=total*frac
            if amount is None: continue
            combo=self.ledger.cellWidget(r,6)
            idx=combo.currentIndex()-1 if combo else -1
            if 0<=idx<len(deductions):
                deductions[idx]+=amount
            else:
                unassigned+=amount
        for r,o in enumerate(self.owners):
            rec=fraction_value(o["fraction"])
            rec_area=total*rec if rec is not None else None
            sold=deductions[r]
            real=(rec_area-sold) if rec_area is not None else None
            self._set(self.owner_table,r,2,format_kms(rec_area))
            self._set(self.owner_table,r,3,format_kms(sold))
            self._set(self.owner_table,r,4,format_kms(real))
            self._set(self.owner_table,r,5,fraction_text(real,total))
        msg=f"Calculated. Assigned deductions: {format_kms(sum(deductions))}."
        if unassigned:
            msg+=f" Unassigned deductions: {format_kms(unassigned)} — these were NOT subtracted from any owner."
        self.status.setText(msg)
        if unassigned:
            QMessageBox.warning(self,"Unassigned Specific-Number Area",
                "Some selected Khana Kasht deductions have no seller-owner assignment. They were deliberately not subtracted from any owner. Assign the seller in the second tab and calculate again.")

    def copy_result(self):
        lines=["\t".join(OWNER_HEADERS)]
        for r in range(self.owner_table.rowCount()):
            lines.append("\t".join(self._text(self.owner_table,r,c) for c in range(len(OWNER_HEADERS))))
        QApplication.clipboard().setText("\n".join(lines))
        self.status.setText("Real-ownership result copied.")

    def export_csv(self):
        path,_=QFileDialog.getSaveFileName(self,"Export Result","real_ownership.csv","CSV Files (*.csv)")
        if not path:return
        with open(path,"w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f)
            w.writerow(["Khewat Number",self.khewat.text()])
            w.writerow(["Village",self.village.text()])
            w.writerow(["Total Area Kanal",self.kanal.value(),"Total Area Marla",self.marla.value()])
            w.writerow([])
            w.writerow(OWNER_HEADERS)
            for r in range(self.owner_table.rowCount()):
                w.writerow([self._text(self.owner_table,r,c) for c in range(len(OWNER_HEADERS))])
            w.writerow([])
            w.writerow(LEDGER_HEADERS[:-1])
            for r in range(self.ledger.rowCount()):
                deduct=self.ledger.cellWidget(r,5)
                combo=self.ledger.cellWidget(r,6)
                w.writerow([self._text(self.ledger,r,c) for c in range(5)]+[
                    "YES" if deduct and deduct.isChecked() else "NO",
                    combo.currentText() if combo else ""])
        self.status.setText(f"Exported {Path(path).name}")

    def clear_all(self):
        self.owner_table.setRowCount(0); self.ledger.setRowCount(0)
        self.owners=[]; self.status.setText("Cleared.")

    @staticmethod
    def norm(s):
        return re.sub(r'\s+',' ',str(s).replace(" ","").lower())

    @staticmethod
    def _text(table,r,c):
        item=table.item(r,c)
        return item.text().strip() if item else ""

    @staticmethod
    def _set(table,r,c,v):
        table.setItem(r,c,QTableWidgetItem(str(v)))

def run():
    app=QApplication([])
    w=MainWindow(); w.show()
    app.exec()
