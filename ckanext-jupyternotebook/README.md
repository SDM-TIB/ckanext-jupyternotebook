# ckanext-jupyternotebook Plugin

This plugin integrates JupyterHub with CKAN, allowing users to execute and temporarily edit interactive Jupyter notebooks within the CKAN environment. The plugin makes data exploration and analysis more accessible and integrated.

### Features

- Integration of Jupyter Notebooks within CKAN
- Temporary notebook editing and execution
- Utilize DockerSpawner to create isolated Docker containers for each user, ensuring a secure and personalized computational environment.
- Guest user access without login
- Admin-configurable maximum number of concurrent guest users

### How it works

1. Users access Jupyter notebooks through the CKAN interface.
2. Each user is provided with a temporary, isolated Docker container.
3. Users can edit notebook cells and install libraries during their session.
4. After a predefined timeout, all changes are automatically reverted.
5. Guest users can access notebooks without logging in, subject to availability.

### Architecture

The extension consists of two main components:

1. **CKAN Extension (ckanext-jupyternotebook)**
   - Core CKAN plugin functionality
   - Views and templates for notebook interaction
   - Controllers for handling notebook operations

2. **JupyterHub Component (jupyterhub)**
   - Runs as a separate Docker container
   - Manages notebook instances
   - Provides API endpoints for user management
   
## Installation

As usual for CKAN extensions, you can install `ckanext-jupyternotebook` as follows:

```bash
git clone git@github.com:SDM-TIB/ckanext-jupyternotebook.git
pip install -e ./ckanext-jupyternotebook
pip install -r ./ckanext-jupyternotebook/requirements.txt
```

### Configure Environment Variables

Configure the .env file with the following required variables::

- ``CKAN_JUPYTERNOTEBOOK_URL``: The base URL for JupyterHub access
- ``CKAN_JUPYTERHUB_BASE_URL``: The base path for JupyterHub
- ``CKAN_NETWORK``: Docker network name
- ``CKAN_STORAGE_NOTEBOOK``: Path to notebook storage
- ``CKAN_API_JUPYTERHUB``: JupyterHub API endpoint
- ``CKAN_JUPYTERHUB_TIMEOUT``: Session timeout in seconds
- ``CKAN_JUPYTERHUB_USER``: Maximum concurrent users
- ``CKAN_JUPYTERHUB_PERCENTAGE_CPU``: CPU allocation per container
- ``CKAN_JUPYTERHUB_MEMORY_LIMIT``: Memory limit per container

Example of customising the extension's behaviour using the following environment variables::

    # JupyterHub variables
    CKAN_JUPYTERNOTEBOOK_URL=https://your-domain/jupyter/
    CKAN_JUPYTERHUB_BASE_URL=/your-path/jupyter
    CKAN_NETWORK=your-docker-network
    CKAN_STORAGE_NOTEBOOK=/path/to/notebook/storage
    CKAN_API_JUPYTERHUB=http://jupyterhub:6000
    CKAN_JUPYTERHUB_TIMEOUT=1200
    CKAN_JUPYTERHUB_USER=100
    CKAN_JUPYTERHUB_PERCENTAGE_CPU=50
    CKAN_JUPYTERHUB_MEMORY_LIMIT=1G

## License

`ckanext-jupyternotebook` is licensed under GPL-3.0, see the [license file](LICENSE).