import logging
import os
from hashlib import sha256

import ckan.lib.helpers as h
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jupyternotebook.views as views
import requests
from ckan.common import config
from ckan.common import request
from ckanext.jupyternotebook.JNFile import JNFile

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)
ignore_empty = plugins.toolkit.get_validator('ignore_empty')

API_URL = os.getenv('CKAN_API_JUPYTERHUB')
API_KEY = os.getenv('JUPYTERHUB_API_TOKEN')

dict_user_session = dict()


def get_api_headers():
    """Get headers for API requests including optional API key"""
    headers = {}
    if API_KEY:
        headers['X-API-Key'] = API_KEY
    return headers


def get_data_from_api():
    """Get an available guest user from JupyterHub API"""
    try:
        response = requests.get(
            API_URL + '/get_user',
            headers=get_api_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            # Handle new JSON response format
            data = response.json()
            if data.get('success'):
                username = data.get('data', {}).get('username')
                log.info(f"Got free user: {username}")
                return username
            else:
                log.error(f"API returned error: {data.get('error')}")
                return None
        elif response.status_code == 503:
            # No users available
            log.warning('No free users available (503)')
            return None
        else:
            log.error(f'Failed to retrieve data from API: status {response.status_code}')
            return None
            
    except requests.exceptions.RequestException as e:
        log.error(f'Error calling get_user API: {e}')
        return None
    except Exception as e:
        log.error(f'Unexpected error: {e}')
        return None


def generate_session_id():
    # Retrieve IP address and user agent from the request object
    ip_address = request.environ.get('REMOTE_ADDR')
    user_agent = request.environ.get('HTTP_USER_AGENT')

    # Create a unique string based on IP address and user agent
    unique_string = f"{ip_address}-{user_agent}"

    # Hash the unique string to create a session ID
    session_id = sha256(unique_string.encode()).hexdigest()

    return session_id


def get_user_id(session_id):
    # Invert the session dictionary to map session IDs to user IDs
    session_to_user = {v: k for k, v in dict_user_session.items()}
    return session_to_user.get(session_id)


def remove_session_to_user(user):
    if user in dict_user_session:
        dict_user_session.pop(user)


def get_jupyterhub_env_variable(variable_name, default=''):
    """
    Retrieve a JupyterHub-related environment variable.

    :param variable_name: Name of the environment variable
    :param default: Default value if environment variable is not set
    :return: Value of the environment variable or default
    """
    return os.getenv(variable_name, default)


def copy_notebook_to_user(username, notebook_name):
    """Copy notebook to user's container via API"""
    try:
        # Changed from GET to POST with JSON body
        response = requests.post(
            API_URL + '/copy_notebook',
            headers={**get_api_headers(), 'Content-Type': 'application/json'},
            json={
                'username': username,
                'notebook_name': notebook_name
            },
            timeout=30
        )
        
        # Handle new JSON response format
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log.info(f"Successfully copied {notebook_name} to {username}")
                return True
            else:
                log.error(f"Failed to copy notebook: {data.get('error')}")
                return False
        else:
            log.error(f"API request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"Error calling copy_notebook API: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return False


class JupyternotebookPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)
    plugins.implements(plugins.IBlueprint, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    url_nb = os.getenv('CKAN_JUPYTERNOTEBOOK_URL')

    # IResourceView

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'jupyternotebook')
        toolkit.add_resource('static', 'jupyternotebook')

        if toolkit.check_ckan_version(min_version='2.10'):
            icon = 'magnifying-glass'
        else:
            icon = 'fa fa-file-code-o'

        toolkit.add_ckan_admin_tab(config_, 'jupyternotebook_admin.admin', 'JupyterHub', icon=icon)

        self.formats = ['ipynb']
        jn_filepath_default = "/var/lib/ckan/notebook"
        self.jn_filepath = config.get('ckan.jupyternotebooks_path', jn_filepath_default)

    def get_blueprint(self):
        return views.get_blueprints()

    def get_helpers(self):
        # Register the helper function here
        return {
            'get_jupyterhub_env_variable': get_jupyterhub_env_variable
        }

    def info(self):
        return {'name': 'jupyternotebook',
                'title': plugins.toolkit._('Jupyternotebook'),
                'icon': 'video-camera',
                'schema': {'jupyternotebook_url': [ignore_empty, str]},
                'iframed': False,
                'always_available': False,
                'default_title': plugins.toolkit._('Jupyternotebook'),
                }

    def can_view(self, data_dict):
        return (data_dict['resource'].get('format', '').lower()
                in self.formats)

    def view_template(self, context, data_dict):
        filename = data_dict['resource_view'].get('jupyternotebook_url') or data_dict['resource'].get('url')
        resource_id = data_dict['resource'].get('id')
        resource_date = data_dict['resource'].get('last_modified')
        url_type = data_dict['resource'].get('url_type')

        session_id = generate_session_id()
        log.info(f"Session ID: {session_id}")

        current_session = False
        if session_id in dict_user_session.values():
            user = get_user_id(session_id)
            current_session = True
        else:
            user = get_data_from_api()

            if user is None:
                toolkit.h.flash_notice(
                    toolkit._('Sorry, there is not more free JupyterHub user, wait few minutes please.')
                )
                data_dict['nb_file'] = "ERROR"
                data_dict['home_url'] = h.url_for('home')
                return 'jupyterhub_no_users.html'

            dict_user_session[user] = session_id
            log.debug(f"New user assigned: {user}")

        # Construct JupyterHub URL for this user
        jn_url = self.url_nb + "user/" + user + "/notebooks/"
        log.info(f"User sessions: {dict_user_session}")
        log.info(f"JupyterHub URL: {jn_url}")

        # Create JNFile object
        self.file = JNFile(filename, resource_id, resource_date, self.jn_filepath, jn_url, url_type)
        data_dict['nb_file'] = self.file

        if current_session:
            notebook_name = self.file.filename
            log.info(f"Copying notebook {notebook_name} to existing user {user}")
            
            success = copy_notebook_to_user(user, notebook_name)
            
            if not success:
                log.error(f"Failed to copy notebook {notebook_name} for user {user}")
                # Note: We don't fail the request, just log the error
                # The user might still be able to access previously copied notebooks

        return 'jupyternotebook_view.html'
