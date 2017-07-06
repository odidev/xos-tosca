import unittest
from mock import patch, MagicMock
from tosca.parser import TOSCA_Parser
from grpc_client.resources import RESOURCES

class FakeObj:
    new = None
    filter = None

class FakeModel:
    save = None
    id = 1

class FakeGuiExt:
    objects = FakeObj

class FakeSite:
    objects = FakeObj

class FakeUser:
    objects = FakeObj

mock_resources = {
    'XOSGuiExtension': FakeGuiExt,
    'Site': FakeSite,
    'User': FakeUser
}

class TOSCA_Parser_E2E(unittest.TestCase):

    @patch.dict(RESOURCES, mock_resources, clear=True)
    @patch.object(FakeGuiExt.objects, 'filter', MagicMock(return_value=[FakeModel]))
    @patch.object(FakeModel, 'save')
    def test_basic_creation(self, mock_save):
        """
        [TOSCA_Parser] Should save models defined in a TOSCA recipe
        """
        recipe = """
tosca_definitions_version: tosca_simple_yaml_1_0

description: Persist xos-sample-gui-extension

imports:
   - custom_types/xosguiextension.yaml

topology_template:
  node_templates:

    # UI Extension
    test:
      type: tosca.nodes.XOSGuiExtension
      properties:
        name: test
        files: /spa/extensions/test/vendor.js, /spa/extensions/test/app.js
"""

        parser = TOSCA_Parser(recipe)

        parser.execute()

        # checking that the model has been saved
        mock_save.assert_called()

        self.assertIsNotNone(parser.templates_by_model_name['test'])
        self.assertEqual(parser.ordered_models_name, ['test'])

        # check that the model was saved with the expected values
        saved_model = parser.saved_model_by_name['test']
        self.assertEqual(saved_model.name, 'test')
        self.assertEqual(saved_model.files, '/spa/extensions/test/vendor.js, /spa/extensions/test/app.js')

    @patch.dict(RESOURCES, mock_resources, clear=True)
    @patch.object(FakeSite.objects, 'filter', MagicMock(return_value=[FakeModel]))
    @patch.object(FakeUser.objects, 'filter', MagicMock(return_value=[FakeModel]))
    @patch.object(FakeModel, 'save')
    def test_related_models_creation(self, mock_save):
        """
        [TOSCA_Parser] Should save related models defined in a TOSCA recipe
        """

        recipe = """
tosca_definitions_version: tosca_simple_yaml_1_0

description: Create a new site with one user

imports:
   - custom_types/user.yaml
   - custom_types/site.yaml

topology_template:
  node_templates:

    # Site
    site_onlab:
      type: tosca.nodes.Site
      properties:
        name: Open Networking Lab
        site_url: http://onlab.us/
        hosts_nodes: True

    # User
    user_test:
      type: tosca.nodes.User
      properties:
        username: test@opencord.org
        email: test@opencord.org
        password: mypwd
        firstname: User
        lastname: Test
        is_admin: True
      requirements:
        - site:
            node: site_onlab
            relationship: tosca.relationships.BelongsToOne
"""

        parser = TOSCA_Parser(recipe)

        parser.execute()

        self.assertEqual(mock_save.call_count, 2)

        self.assertIsNotNone(parser.templates_by_model_name['site_onlab'])
        self.assertIsNotNone(parser.templates_by_model_name['user_test'])
        self.assertEqual(parser.ordered_models_name, ['site_onlab', 'user_test'])

        # check that the model was saved with the expected values
        saved_site = parser.saved_model_by_name['site_onlab']
        self.assertEqual(saved_site.name, 'Open Networking Lab')

        saved_user = parser.saved_model_by_name['user_test']
        self.assertEqual(saved_user.firstname, 'User')
        self.assertEqual(saved_user.site_id, 1)