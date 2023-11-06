import botocore
from PIL import Image
from urllib.request import urlopen

from App_creators.utils import check_bank_card, check_price, get_image_from_s3
import unittest


class CheckBankCardTestCase(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(True, check_bank_card('4100118428035885'))

    def test_random_type(self):
        self.assertRaises(TypeError, check_bank_card, [1, 2, 3])

    def test_random_text(self):
        self.assertEqual(False, check_bank_card('ИВРИВРИВРИВРИВРИВРИВ'))

    def test_short(self):
        self.assertEqual(False, check_bank_card('123123123'))

    def test_float(self):
        self.assertEqual(False, check_bank_card('4100118428035885.5'))

    def test_with_spaces(self):
        self.assertEqual(False, check_bank_card('1234 1234 1234 1234'))


class CheckPriceTestCase(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(True, check_price(12312321))

    def test_free(self):
        self.assertEqual(True, check_price('free'))

    def test_random_type(self):
        self.assertRaises(TypeError, check_price, [(1, 2), (3, 4)])

    def test_negative(self):
        self.assertEqual(False, check_price(-1))

    def test_border(self):
        self.assertEqual(True, check_price('2'))


class GetImageFromS3TestCase(unittest.TestCase):
    def test_normal(self):
        url = 'https://storage.yandexcloud.net/mybacket/logos/test.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=YCAJEU7cWXGnpUYu3yJ3YFLM1%2F20231106%2Fru-central1%2Fs3%2Faws4_request&X-Amz-Date=20231106T103332Z&X-Amz-Expires=2592000&X-Amz-Signature=5AEDE4B5DA458317D5A8D701681FE7A173238EBCE16D111F1203AD50715A7897&X-Amz-SignedHeaders=host'
        expected = Image.open(urlopen(url))
        self.assertEqual(expected, get_image_from_s3('mybacket', 'logos/test.jpg'))

    def test_unexpected_backet(self):
        self.assertRaises(botocore.exceptions.ClientError, get_image_from_s3, 'my_backet', 'logos/test.jpg')

    def test_unexpected_path(self):
        self.assertRaises(botocore.exceptions.ClientError, get_image_from_s3, 'mybacket', 'logo/IVR.jpg')

    def test_unexpected_types(self):
        self.assertRaises(TypeError, get_image_from_s3, 1, 2)


if __name__ == '__main__':
    unittest.main()
