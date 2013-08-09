import random
import unittest
import mock
import tempfile
import io
import logging
import shutil

import nupay

class USBTokenReaderTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        #logging.basicConfig(level=logging.DEBUG)
        unused, self.mounts_path = tempfile.mkstemp()
        self.tmpdir = tempfile.mkdtemp()
        self.write_no_device()
        self.token_reader = nupay.USBTokenReader(mounts_path=self.mounts_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
 
    def write_no_device(self):
        with io.open(self.mounts_path, "wb") as f:
            f.write("/dev/sda2 /boot ext2 rw,relatime,errors=continue 0 0\n")
   
    def write_paths(self, paths):
        with io.open(self.mounts_path, "wb") as f:
            f.write("/dev/sda2 /boot ext2 rw,relatime,errors=continue 0 0\n")
            for path in paths:
                f.write("/dev/sda1 %s vfat rw,sync,nodev,noexec,noatime,nodiratime,fmask=0022,dmask=0022,codepage=cp437,iocharset=ascii,shortname=mixed,errors=remount-ro 0 0\n"%path)

    def test_no_device(self):
        self.assertRaises(nupay.NoTokensAvailableError, self.token_reader.read_tokens)
    
    def test_new_device(self):
        self.write_paths(["/mnt/foobar"])
        self.assertRaises(nupay.NoTokensAvailableError, self.token_reader.read_tokens)

    def test_new_device_with_bad_purse(self):
        self.write_paths([self.tmpdir])
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            purse.write("123\n")
            purse.write("124\n")
        self.assertRaises(nupay.NoTokensAvailableError, self.token_reader.read_tokens)
 
    def test_new_device_with_empty_purse(self):
        self.write_paths([self.tmpdir])
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            pass
        self.assertRaises(nupay.NoTokensAvailableError, self.token_reader.read_tokens)
        
    def test_new_device_with_purse_dup(self):
        self.write_paths([self.tmpdir])
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686\n")
            purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686\n")
 
        tokens = self.token_reader.read_tokens()
        self.assertEqual(1, len(tokens))
        self.assertEqual(tokens[0].hash, "db891851322ff6b04b993af03fda984f3356f64e34abaf73faf7919cae02c1f38c4cd172f6e71414cc25e7f2c331c2cdc4e176e604a2b16686eb7d528671b513")
 
    def test_new_device_with_purse(self):
        self.write_paths([self.tmpdir])
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686\n")
            purse.write("24fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686\n")
 
        tokens = self.token_reader.read_tokens()
        self.assertEqual(2, len(tokens))
    
    def test_device_removed(self):
        self.write_paths([self.tmpdir])
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686\n")
        self.token_reader.read_tokens()

        self.assertTrue(self.token_reader.medium_valid)
        self.write_paths([])
        self.assertFalse(self.token_reader.medium_valid)

    def test_large_purse_default(self):
        self.write_paths([self.tmpdir])
        t = 1375901686
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            for i in range(230):
                purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%%%d\n"%(t+i))
        tokens = self.token_reader.read_tokens()
        self.assertEqual(200, len(tokens))

    def test_large_purse_250(self):
        self.write_paths([self.tmpdir])
        t = 1375901686
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            for i in range(300):
                purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%%%d\n"%(t+i))
        tokens = self.token_reader.read_tokens(250)
        self.assertEqual(250, len(tokens))

    def test_huge_purse(self):
        self.write_paths([self.tmpdir])
        t = 1375901686
        with io.open(self.tmpdir+'/purse', "wb") as purse:
            for i in range(30000):
                purse.write("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%%%d\n"%(t+i))
        self.assertRaises(nupay.NoTokensAvailableError, self.token_reader.read_tokens)



if __name__ == '__main__':
    unittest.main()
