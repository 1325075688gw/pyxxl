from .base import ExportDataABC


class Csv(ExportDataABC):
    def export(self):
        self.export_data.to_csv(self._file_name, index=False, encoding="utf-8")
