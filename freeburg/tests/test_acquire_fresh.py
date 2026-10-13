from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from freeburg.tools.acquire_fresh import acquire


class FakeResponse:
    status=200
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):return self.data[:n]


class FreshAcquisitionTests(unittest.TestCase):
    def test_reject_html(self):
        with TemporaryDirectory() as t:
            out=Path(t)/"fake.xls"
            with self.assertRaisesRegex(ValueError,"Expected XLS"):
                acquire("https://example.test/example.xls",out,"xls",
                        opener=lambda request,timeout:FakeResponse(b"<!DOCTYPE html><html></html>"))
            self.assertFalse(out.exists())

    def test_hash_manifest_metadata_and_no_overwrite(self):
        with TemporaryDirectory() as t:
            out=Path(t)/"h15.zip"
            data=bytes.fromhex("504b0304")+b"placeholder"
            got=acquire("https://example.test/archive.zip",out,"zip",
                        opener=lambda request,timeout:FakeResponse(data))
            self.assertEqual(got["bytes"],len(data))
            self.assertEqual(out.read_bytes(),data)
            self.assertEqual(len(got["sha256"]),64)
            with self.assertRaises(FileExistsError):
                acquire("https://example.test/archive.zip",out,"zip",
                        opener=lambda request,timeout:FakeResponse(data))


if __name__=="__main__":
    unittest.main()
