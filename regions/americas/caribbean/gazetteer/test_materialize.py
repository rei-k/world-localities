import hashlib
from pathlib import Path
import tempfile
import unittest
from materialize import restore

class Reconstruction(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.data=b'original\x00bytes\xff';(self.root/'part.bin').write_bytes(self.data)
        self.entry={'path':'countries/DO/source.gz','bytes':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest(),'parts':[{'path':'part.bin','bytes':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}]}
    def tearDown(self):self.temp.cleanup()
    def test_roundtrip_idempotent(self):
        p=restore(self.root,self.entry);self.assertEqual(p.read_bytes(),self.data);self.assertEqual(restore(self.root,self.entry),p)
    def test_corrupt_part(self):
        (self.root/'part.bin').write_bytes(b'x')
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_no_traversal(self):
        self.entry['path']='../outside'
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_no_symlink(self):
        (self.root/'countries').symlink_to('/tmp')
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_no_overwrite(self):
        p=restore(self.root,self.entry);p.write_bytes(b'different')
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_absolute_path_rejected(self):
        self.entry['path']='/tmp/outside-caribbean'
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_part_traversal_rejected(self):
        self.entry['parts'][0]['path']='../part.bin'
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_full_hash_mismatch_leaves_no_target(self):
        self.entry['sha256']='0'*64
        with self.assertRaises(ValueError):restore(self.root,self.entry)
        self.assertFalse((self.root/self.entry['path']).exists())
    def test_part_hash_mismatch_same_size(self):
        (self.root/'part.bin').write_bytes(b'x'*len(self.data))
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_part_size_limit(self):
        self.entry['parts'][0]['bytes']=512*1024+1
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_duplicate_manifest_target_rejected(self):
        import json
        from materialize import manifest
        (self.root/'split_manifest.json').write_text(json.dumps({'files':[self.entry,self.entry]}))
        with self.assertRaises(ValueError):manifest(self.root)
    def test_manifest_symlink_rejected(self):
        from materialize import manifest
        (self.root/'split_manifest.json').symlink_to(self.root/'part.bin')
        with self.assertRaises(ValueError):manifest(self.root)
if __name__=='__main__':unittest.main()

