import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

pytestmark = pytest.mark.unit

from kicad_api.ipc_backend import IPCBackend  # noqa: E402


def _install_fake_document_type(monkeypatch):
    kipy_mod = types.ModuleType("kipy")
    proto_mod = types.ModuleType("kipy.proto")
    common_mod = types.ModuleType("kipy.proto.common")
    types_mod = types.ModuleType("kipy.proto.common.types")
    types_mod.DocumentType = types.SimpleNamespace(DOCTYPE_PCB=3)

    monkeypatch.setitem(sys.modules, "kipy", kipy_mod)
    monkeypatch.setitem(sys.modules, "kipy.proto", proto_mod)
    monkeypatch.setitem(sys.modules, "kipy.proto.common", common_mod)
    monkeypatch.setitem(sys.modules, "kipy.proto.common.types", types_mod)


def _pcb_doc(project_path="/workspace/fellow/tag/hardware"):
    return types.SimpleNamespace(
        board_filename="fellow.kicad_pcb",
        project=types.SimpleNamespace(name="fellow", path=project_path),
    )


def _connected_backend(kicad):
    backend = IPCBackend()
    backend._connected = True
    backend._kicad = kicad
    return backend


def test_get_open_board_path_uses_kicad10_typed_document_query(monkeypatch):
    _install_fake_document_type(monkeypatch)
    doc = _pcb_doc()

    class FakeKiCad:
        def ping(self):
            return None

        def get_open_documents(self, doc_type):
            assert doc_type == 3
            return [doc]

    backend = _connected_backend(FakeKiCad())

    assert backend.get_open_board_path() == "/workspace/fellow/tag/hardware/fellow.kicad_pcb"


def test_get_open_documents_falls_back_to_legacy_untyped_query(monkeypatch):
    _install_fake_document_type(monkeypatch)
    doc = _pcb_doc()

    class FakeKiCad:
        def get_open_documents(self, *args):
            if args:
                raise TypeError("get_open_documents() takes 1 positional argument")
            return [doc]

    backend = _connected_backend(FakeKiCad())

    assert backend._get_open_documents("DOCTYPE_PCB") == [doc]


def test_open_project_matches_kicad10_project_from_pcb_document(monkeypatch):
    _install_fake_document_type(monkeypatch)
    doc = _pcb_doc()

    class FakeKiCad:
        def ping(self):
            return None

        def get_open_documents(self, doc_type):
            assert doc_type == 3
            return [doc]

    backend = _connected_backend(FakeKiCad())

    result = backend.open_project(Path("/workspace/fellow/tag/hardware/fellow.kicad_pro"))

    assert result["success"] is True
    assert result["path"] == "/workspace/fellow/tag/hardware/fellow.kicad_pro"
