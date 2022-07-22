from .base import ExportDataABC


class Xlsx(ExportDataABC):
    def export(self):
        self.export_data.to_excel(self._file_name, index=False, encoding="utf-8")
