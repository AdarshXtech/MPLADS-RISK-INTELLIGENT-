"""Small synthetic XML fixtures test read-only export inspection boundaries."""

from zipfile import ZipFile

import pytest

from backend.inspect_exports import read_static_xlsx, run


def workbook(tmp_path, body):
    path = tmp_path / "synthetic.xlsx"
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", body)
    return path


def test_sparse_static_cells(tmp_path):
    path = workbook(
        tmp_path,
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="3"><c r="A3"><v>1</v></c><c r="C3" t="inlineStr"><is><t>Synthetic</t></is></c></row></sheetData></worksheet>',
    )
    assert read_static_xlsx(path) == [(3, ["1", "", "Synthetic"])]


@pytest.mark.parametrize(
    "cell", ['<c r="A1"><f>1+1</f><v>2</v></c>', '<c r="A1" t="s"><v>0</v></c>']
)
def test_formula_and_shared_string_refused(tmp_path, cell):
    path = workbook(
        tmp_path,
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1">'
        + cell
        + "</row></sheetData></worksheet>",
    )
    with pytest.raises(ValueError, match="static"):
        read_static_xlsx(path)


def test_xml_entities_refused(tmp_path):
    path = workbook(
        tmp_path, '<!DOCTYPE test [<!ENTITY content "unsafe">]><worksheet/>'
    )
    with pytest.raises(ValueError, match="DTD"):
        read_static_xlsx(path)


def test_inspection_does_not_write_into_raw(tmp_path):
    with pytest.raises(ValueError, match="raw directory"):
        run(tmp_path, tmp_path / "processed", tmp_path / "dictionary.md")
