import hashlib
from pathlib import Path
import tempfile
import unittest
from materialize import restore

class Reconstruction(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.data=b'original\x00bytes\xff';(self.root/'part.bin').write_bytes(self.data)
        self.entry={'path':'countries/MX/source.gz','bytes':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest(),'parts':[{'path':'part.bin','bytes':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}]}
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
        self.assertEqual(p.read_bytes(),b'different')
    def test_part_path_traversal(self):
        self.entry['parts'][0]['path']='../part.bin'
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_part_symlink(self):
        (self.root/'alias.bin').symlink_to(self.root/'part.bin')
        self.entry['parts'][0]['path']='alias.bin'
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_wrong_full_hash_leaves_no_output(self):
        self.entry['sha256']='0'*64
        with self.assertRaises(ValueError):restore(self.root,self.entry)
        self.assertFalse((self.root/self.entry['path']).exists())
        self.assertEqual(list((self.root/'countries/MX').iterdir()),[])
    def test_wrong_total_size(self):
        self.entry['bytes']+=1
        with self.assertRaises(ValueError):restore(self.root,self.entry)
    def test_oversized_part(self):
        data=b'x'*(512*1024+1);(self.root/'part.bin').write_bytes(data)
        self.entry['parts'][0].update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        self.entry.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        with self.assertRaises(ValueError):restore(self.root,self.entry)
if __name__=='__main__':unittest.main()
