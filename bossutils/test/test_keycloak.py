# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
sys.path.append("../")

try:
    from bossutils.keycloak import KeyCloakClient, KeyCloakError
    prefix = 'bossutils.'
except:
    from keycloak import KeyCloakClient, KeyCloakError
    prefix = '.'

from types import MethodType
import json
import unittest
from unittest import mock

import hvac

REALM = 'REALM'
BASE = 'http://auth'
TOKEN = {'access_token': 'access_token', 'refresh_token': 'refresh_token'}

def mock_login(self):
    self.token = TOKEN
    self.client_id = 'client_id'
    self.login_realm = 'realm'

def mock_logout(self):
    self.token = None
    self.client_id = None
    self.login_realm = None

class MockResponse:
    def __init__(self, status, text):
        self.status_code = status
        self.text = text

    def json(self):
        return json.loads(self.text)

'''
# The patch decorator mocks hvac.Client and passes it as the second parameter
# to each test method.  Setting autospec true forces the signature of the
# mock's methods match that of hvac.Client.
@patch('hvac.Client', autospec = True)
class TestVaultClient(unittest.TestCase):
    def setUp(self):
        """ Create a dummy configuration. """
        self.cfg = { VAULT_SECTION :
            {
                VAULT_URL_KEY : 'https://foo.com',
                VAULT_TOKEN_KEY : 'open'
            }
        }

    def test_exception_if_cant_auth_to_vault(self, mockClient):
        instance = mockClient.return_value
        instance.is_authenticated.return_value = False
        with self.assertRaises(Exception):
            v = Vault(self.cfg)

    def test_logout_destroys_hvac_client(self, mockClient):
        v = Vault(self.cfg)
        v.logout()
        self.assertIsNone(v.client)

    def test_exception_if_read_dict_fails(self, mockClient):
        instance = mockClient.return_value
        instance.read.return_value = None
        v = Vault(self.cfg)
        with self.assertRaises(Exception):
            v.read_dict('secrets')

    def test_exception_if_read_fails(self, mockClient):
        instance = mockClient.return_value
        instance.read.return_value = None
        v = Vault(self.cfg)
        with self.assertRaises(Exception):
            v.read('secrets', 'super')

    def test_exception_if_key_dosent_exist(self, mockClient):
        instance = mockClient.return_value
        instance.read.return_value = { "data": {} }
        v = Vault(self.cfg)
        with self.assertRaises(Exception):
            v.read('secrets', 'super')

class TestKeyCloakError(unittest.TestCase):
    pass
'''

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.client = KeyCloakClient(REALM, BASE)

    @mock.patch(prefix + 'keycloak.Vault', autospec = True)
    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_login(self, mPost, mVault):
        """login makes post call with data from vault and creates token variable"""
        mPost.return_value = MockResponse(200, json.dumps(TOKEN))
        mVault.return_value.read = lambda p, k: k

        self.assertIsNone(self.client.token)

        self.client.login()

        self.assertEqual(self.client.token, TOKEN)

        # DP NOTE: since the post call contains information read from Vault
        #          I don't explicitly check for the calls to Vault, because
        #          if they didn't happen, they the post call assert will fail

        url = BASE + '/realms/realm/protocol/openid-connect/token'
        data = {'grant_type': 'password',
                'client_id': 'client_id',
                'username': 'username',
                'password': 'password' }
        call = mock.call(url, data = data, verify = True)
        self.assertEqual(mPost.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.Vault', autospec = True)
    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_failed_login(self, mPost, mVault):
        """on post response with error status, KeyCloakError is raised"""
        mPost.return_value = MockResponse(500, '[]')
        mVault.return_value.read = lambda p, k: k

        with self.assertRaises(KeyCloakError):
            self.client.login()

    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_logout(self, mPost):
        """logout makes post call with data used in login and clears variables"""
        mPost.return_value = MockResponse(200, '[]')

        self.client.login = MethodType(mock_login, self.client) # See comment in TestRequests.setUp()
        self.client.login()

        self.assertEqual(self.client.token, TOKEN)

        self.client.logout()

        self.assertIsNone(self.client.token)

        url = BASE + '/realms/realm/protocol/openid-connect/logout'
        data = {'refresh_token': 'refresh_token',
                'client_id': 'client_id' }
        call = mock.call(url, data = data, verify = True)
        self.assertEqual(mPost.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_failed_logout(self, mPost):
        """on post response with error status, KeyCloakError is raised"""
        mPost.return_value = MockResponse(500, '[]')

        self.client.login = MethodType(mock_login, self.client) # See comment in TestRequests.setUp()
        self.client.login()

        with self.assertRaises(KeyCloakError):
            self.client.logout()

    def test_with(self):
        """login and logout are called"""
        self.client.loginCalled = False
        self.client.logoutCalled = False

        def call_login(self):
            self.loginCalled = True

        def call_logout(self):
            self.logoutCalled = True

        self.client.login = MethodType(call_login, self.client)
        self.client.logout = MethodType(call_logout, self.client)

        with self.client as kc:
            pass

        self.assertTrue(self.client.loginCalled)
        self.assertTrue(self.client.logoutCalled)

    def test_failed_with(self):
        """if an exception during with then it is propogated correctly"""
        self.client.loginCalled = False
        self.client.logoutCalled = False

        def call_login(self):
            self.loginCalled = True

        def call_logout(self):
            self.logoutCalled = True

        self.client.login = MethodType(call_login, self.client)
        self.client.logout = MethodType(call_logout, self.client)

        with self.assertRaises(Exception):
            with self.client as kc:
                raise Exception()

        self.assertTrue(self.client.loginCalled)
        self.assertTrue(self.client.logoutCalled)

    def test_failed_with_login(self):
        """if login fails, logout is not called"""
        self.client.loginCalled = False
        self.client.logoutCalled = False

        def call_login(self):
            self.loginCalled = True
            raise Exception()

        def call_logout(self):
            self.logoutCalled = True

        self.client.login = MethodType(call_login, self.client)
        self.client.logout = MethodType(call_logout, self.client)

        with self.assertRaises(Exception):
            with self.client as kc:
                pass

        self.assertTrue(self.client.loginCalled)
        self.assertFalse(self.client.logoutCalled)

    def test_failed_with_logout(self):
        """if logout fails, no exception is generated"""
        self.client.loginCalled = False
        self.client.logoutCalled = False

        def call_login(self):
            self.loginCalled = True

        def call_logout(self):
            self.logoutCalled = True
            raise Exception()

        self.client.login = MethodType(call_login, self.client)
        self.client.logout = MethodType(call_logout, self.client)

        with self.client as kc:
            pass

        self.assertTrue(self.client.loginCalled)
        self.assertTrue(self.client.logoutCalled)

class TestRequests(unittest.TestCase):
    def setUp(self):
        self.client = KeyCloakClient(REALM, BASE)

        # Have to use MethodType to bind the mock method to the specific instance
        # of the KeyCloakClient instead of binding it to all instances of the
        # class
        # See http://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance
        self.client.login = MethodType(mock_login, self.client)
        self.client.logout = MethodType(mock_logout, self.client)

    # DP TODO: the test_(get/post/put/delete) test logic can be merged into a
    #          single unified method implementing most of the logic
    @mock.patch(prefix + 'keycloak.requests.get', autospec = True)
    def test_get(self, mGet):
        """Appropriate URL, headers, parameters are set"""
        mGet.return_value = MockResponse(200, '[]')
        suffix = 'test'

        with self.client as kc:
            response = kc._get(suffix, {'param': 'one'}, {'header': 'one'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        url = BASE + '/admin/realms/' + REALM + '/' + suffix
        params = {'param': 'one'}
        headers = {'header': 'one', 'Authorization': 'Bearer access_token'}
        call = mock.call(url, headers = headers, params = params, verify = True)
        self.assertEqual(mGet.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.requests.get', autospec = True)
    def test_failed_get(self, mGet):
        """on error response, KeyCloakError is raised"""
        mGet.return_value = MockResponse(500, '[]')

        with self.assertRaises(KeyCloakError):
            with self.client as kc:
                response = kc._get('test')

    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_post(self, mPost):
        """Appropriate URL, headers, parameters are set"""
        mPost.return_value = MockResponse(200, '[]')
        suffix = 'test'

        with self.client as kc:
            response = kc._post(suffix, {'data': 'one'}, {'header': 'one'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        url = BASE + '/admin/realms/' + REALM + '/' + suffix
        data = {'data': 'one'}
        headers = {'header': 'one',
                   'Authorization': 'Bearer access_token',
                   'Content-Type': 'application/json'}
        call = mock.call(url, headers = headers, data = data, verify = True)
        self.assertEqual(mPost.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.requests.post', autospec = True)
    def test_failed_post(self, mPost):
        """on error response, KeyCloakError is raised"""
        mPost.return_value = MockResponse(500, '[]')

        with self.assertRaises(KeyCloakError):
            with self.client as kc:
                response = kc._post('test')

    @mock.patch(prefix + 'keycloak.requests.put', autospec = True)
    def test_put(self, mPut):
        """Appropriate URL, headers, parameters are set"""
        mPut.return_value = MockResponse(200, '[]')
        suffix = 'test'

        with self.client as kc:
            response = kc._put(suffix, {'data': 'one'}, {'header': 'one'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        url = BASE + '/admin/realms/' + REALM + '/' + suffix
        data = {'data': 'one'}
        headers = {'header': 'one',
                   'Authorization': 'Bearer access_token',
                   'Content-Type': 'application/json'}
        call = mock.call(url, headers = headers, json = data, verify = True)
        self.assertEqual(mPut.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.requests.put', autospec = True)
    def test_failed_put(self, mPut):
        """on error response, KeyCloakError is raised"""
        mPut.return_value = MockResponse(500, '[]')

        with self.assertRaises(KeyCloakError):
            with self.client as kc:
                response = kc._put('test')

    @mock.patch(prefix + 'keycloak.requests.delete', autospec = True)
    def test_delete(self, mDelete):
        """Appropriate URL, headers, parameters are set"""
        mDelete.return_value = MockResponse(200, '[]')
        suffix = 'test'

        with self.client as kc:
            response = kc._delete(suffix, {'data': 'one'}, {'header': 'one'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        url = BASE + '/admin/realms/' + REALM + '/' + suffix
        data = {'data': 'one'}
        headers = {'header': 'one',
                   'Authorization': 'Bearer access_token',
                   'Content-Type': 'application/json'}
        call = mock.call(url, headers = headers, data = data, verify = True)
        self.assertEqual(mDelete.mock_calls, [call])

    @mock.patch(prefix + 'keycloak.requests.delete', autospec = True)
    def test_failed_delete(self, mDelete):
        """on error response, KeyCloakError is raised"""
        mDelete.return_value = MockResponse(500, '[]')

        with self.assertRaises(KeyCloakError):
            with self.client as kc:
                response = kc._delete('test')

class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = KeyCloakClient(REALM, BASE)

        # Have to use MethodType to bind the mock method to the specific instance
        # of the KeyCloakClient instead of binding it to all instances of the
        # class
        # See http://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance
        self.client.login = MethodType(mock_login, self.client)
        self.client.logout = MethodType(mock_logout, self.client)