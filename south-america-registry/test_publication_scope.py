"""Regression tests for the explicitly limited publication scope."""
import unittest
from build import PUBLISHED_SCOPE, PENDING, SCOPE
from query import select


class PublicationScope(unittest.TestCase):
    def test_fourteen_of_sixteen(self):
        self.assertEqual(len(SCOPE),16)
        self.assertEqual(len(PUBLISHED_SCOPE),14)
        self.assertEqual(PENDING,{'AR','PY'})
        self.assertFalse(PUBLISHED_SCOPE.intersection(PENDING))
        self.assertEqual(PUBLISHED_SCOPE | PENDING,SCOPE)

    def test_pending_queries_rejected(self):
        for cc in sorted(PENDING):
            with self.subTest(country=cc):
                with self.assertRaisesRegex(ValueError,'not included'):
                    list(select(cc))


if __name__=='__main__':unittest.main()
