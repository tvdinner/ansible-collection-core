import sys
import unittest

from ansible_collections.tvdinner.core.plugins.module_utils.common import (
    calculate_diff,
    connection_argument_spec,
    normalize_dict_subset,
    normalize_list,
)


class FakeModule(object):
    _diff = True


class TestCommon(unittest.TestCase):

    def test_connection_argument_spec(self):
        spec = connection_argument_spec('gitea_url', 'gitea_token')
        self.assertTrue(spec['gitea_url']['required'])
        self.assertTrue(spec['gitea_token']['no_log'])
        self.assertTrue(spec['validate_certs']['default'])
        self.assertEqual(spec['timeout']['default'], 30)

    def test_normalize_list(self):
        self.assertEqual(normalize_list(['b', 'a', 'b']), ['a', 'b'])
        self.assertEqual(normalize_list(None), [])

    def test_normalize_dict_subset(self):
        source = {'name': 'x', 'created': '2026', 'id': 5}
        self.assertEqual(
            normalize_dict_subset(source, ['name']), {'name': 'x'})
        self.assertEqual(normalize_dict_subset(None, ['name']), {})

    def test_calculate_diff_unchanged(self):
        result = calculate_diff({'a': 1}, {'a': 1}, FakeModule())
        self.assertFalse(result['changed'])

    def test_calculate_diff_changed(self):
        result = calculate_diff({'a': 1}, {'a': 2}, FakeModule())
        self.assertTrue(result['changed'])
        self.assertEqual(result['diff']['before'], {'a': 1})
        self.assertEqual(result['diff']['after'], {'a': 2})

    def test_calculate_diff_create(self):
        result = calculate_diff(None, {'a': 1}, FakeModule())
        self.assertTrue(result['changed'])

    def test_calculate_diff_delete(self):
        result = calculate_diff({'a': 1}, None, FakeModule())
        self.assertTrue(result['changed'])


if __name__ == '__main__':
    unittest.main()
