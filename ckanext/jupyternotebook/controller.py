import logging
import os

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import requests
from ckan.common import request
from ckan.plugins import toolkit
from ckanext.jupyternotebook import plugin

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 'ckanext.jupyternotebook.timeout'
DEFAULT_MAX_USER = 'ckanext.jupyternotebook.max_user'
DEFAULT_CPU_PERCENTAGE = 'ckanext.jupyternotebook.cpu'
DEFAULT_MEMORY_LIMIT = 'ckanext.jupyternotebook.memory'
API_URL = os.getenv('CKAN_API_JUPYTERHUB')
API_KEY = os.getenv('JUPYTERHUB_API_TOKEN')


def get_api_headers():
    """Get headers for API requests including optional API key"""
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['X-API-Key'] = API_KEY
    return headers


def restart_jupyterhub():
    """Restart JupyterHub service via API"""
    try:
        response = requests.post(
            API_URL + '/restart_jupyterhub',
            headers=get_api_headers(),
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log.info("JupyterHub restart successful")
                return True
            else:
                log.error(f"JupyterHub restart failed: {data.get('error')}")
                return False
        else:
            log.error(f"API request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"Error calling restart API: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return False


def update_env_variable(key, value):
    """Update environment variable"""
    try:
        os.environ[key] = str(value)
        return True
    except Exception as e:
        log.error(f"Error updating environment variable {key}: {str(e)}")
        return False


def update_jupyterhub_env_variables(updates):
    """Update environment variables in JupyterHub container via API"""
    try:
        response = requests.post(
            API_URL + '/update_env',
            headers=get_api_headers(),
            json=updates,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log.info(f"Updated variables: {data.get('data', {}).get('updated', [])}")
                return True
            else:
                log.error(f"Failed to update variables: {data.get('error')}")
                return False
        else:
            log.error(f"API request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"Error calling update_env API: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return False


class JupyterHubController:

    def __init__(self):
        pass

    @staticmethod
    def get_jupyterhub_env_variable(variable_name, default=''):
        """
        Retrieve a JupyterHub-related environment variable.

        :param variable_name: Name of the environment variable
        :param default: Default value if environment variable is not set
        :return: Value of the environment variable or default
        """
        return os.getenv(variable_name, default)


    @staticmethod
    def validate_inputs(timeout, max_user, cpu, memory):
        """Validate all input values with specific ranges and requirements"""
        try:
            # Convert and validate timeout
            timeout = int(timeout)
            if timeout < 5:
                raise ValueError("Timeout must be at least 5 seconds")

            # Convert and validate max_user
            max_user = int(max_user)
            if max_user <= 0:
                raise ValueError("Maximum users must be greater than 0")

            # Convert and validate CPU
            cpu = int(cpu)
            if cpu < 1 or cpu > 100:
                raise ValueError("CPU percentage must be between 1 and 100")

            # Validate memory format and value
            if not memory.endswith(('M', 'G')):
                raise ValueError("Memory must end with M or G")

            # Extract numeric value from memory string
            memory_value = int(memory[:-1])
            if memory_value <= 0:
                raise ValueError("Memory value must be greater than 0")

            # Return validated values
            return timeout, max_user, cpu, memory

        except ValueError as e:
            raise ValueError(str(e))

    def admin(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
            'auth_user_obj': toolkit.c.userobj
        }
        try:
            logic.check_access('sysadmin', context, {})
        except logic.NotAuthorized:
            base.abort(403, toolkit._('Need to be system administrator to administer.'))

        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'default_setup':
                # Get form values
                timeout = request.form.get(DEFAULT_TIMEOUT, '')
                max_user = request.form.get(DEFAULT_MAX_USER, '')
                cpu = request.form.get(DEFAULT_CPU_PERCENTAGE, '')
                memory = request.form.get(DEFAULT_MEMORY_LIMIT, '').strip()

                try:
                    # Validate all inputs
                    timeout, max_user, cpu, memory = self.validate_inputs(
                        timeout, max_user, cpu, memory
                    )

                    # Update environment variables
                    updates = {
                        'CKAN_JUPYTERHUB_TIMEOUT': str(timeout),
                        'CKAN_JUPYTERHUB_USER': str(max_user),
                        'CKAN_JUPYTERHUB_PERCENTAGE_CPU': str(cpu),
                        'CKAN_JUPYTERHUB_MEMORY_LIMIT': memory
                    }

                    local_success = True
                    for key, value in updates.items():
                        if not update_env_variable(key, value):
                            local_success = False
                            break

                    # Update environment variables in JupyterHub container
                    remote_success = update_jupyterhub_env_variables(updates)


                    # if success and restart_jupyterhub():
                    #     toolkit.h.flash_success(
                    #         toolkit._('JupyterHub settings have been updated and service restarted.'))
                    if local_success and remote_success:
                        plugin.dict_user_session = dict()
                        toolkit.h.flash_success(toolkit._('JupyterHub settings have been updated.'))
                    elif local_success and not remote_success:
                        toolkit.h.flash_error(toolkit._('Local settings updated but failed to update JupyterHub container.'))
                    else:
                        toolkit.h.flash_error(toolkit._('Error updating JupyterHub settings.'))

                except ValueError as e:
                    toolkit.h.flash_error(f"Invalid input: {str(e)}")

        # Get current values for display
        extra_vars = {
            'timeout': self.get_jupyterhub_env_variable('CKAN_JUPYTERHUB_TIMEOUT'),
            'max_user': self.get_jupyterhub_env_variable('CKAN_JUPYTERHUB_USER'),
            'cpu': self.get_jupyterhub_env_variable('CKAN_JUPYTERHUB_PERCENTAGE_CPU'),
            'memory': self.get_jupyterhub_env_variable('CKAN_JUPYTERHUB_MEMORY_LIMIT')
        }

        return toolkit.render('admin_jupyter.html', extra_vars=extra_vars)
