
=============
ckanext-jupyternotebook
=============

This plugin integrates JupyterHub with CKAN, allowing users to execute and temporarily edit interactive Jupyter notebooks within the CKAN environment. The plugin makes data exploration and analysis more accessible and integrated.

**Features**

- Seamless integration of Jupyter Notebooks within CKAN
- Temporary notebook editing and execution
- Utilize DockerSpawner to create isolated Docker containers for each user, ensuring a secure and personalized computational environment.
- Guest user access without login
- Admin-configurable maximum number of concurrent guest users

**How it works**

1. Users access Jupyter notebooks through the CKAN interface.
2. Each user is provided with a temporary, isolated Docker container.
3. Users can edit notebook cells and install libraries during their session.
4. After a predefined timeout, all changes are automatically reverted.
5. Guest users can access notebooks without logging in, subject to availability.

Architecture
------------
The extension consists of two main components:

1. **CKAN Extension (CKAN_JupyterHub)**
   - Core CKAN plugin functionality
   - Views and templates for notebook interaction
   - Controllers for handling notebook operations

2. **JupyterHub Component (jupyterhub)**
   - Runs as a separate Docker container
   - Manages notebook instances
   - Provides API endpoints for user management

------------
Requirements
------------
- CKAN 2.1 or later
- Python 3.6 or later
- Docker
- JupyterHub


1. Installation
----------------

a. Clone the repository::

    git clone https://github.com/SDM-TIB/CKAN_JupyterHub.git

b. Install the extension package::

    pip install CKAN_JupyterHub/ckanext-jupyternotebook

c. Add the plugin to your CKAN configuration file (typically at ``/etc/ckan/default/ckan.ini``)::

    ckan.plugins = ... jupyternotebook

2. Configure Environment Variables
-----------------------------------

Configure the .env file with the following required variables::

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

3. Set Up JupyterHub
--------------------

a. Build the JupyterHub service::

    cd ../jupyterhub
    # Build the Docker image and tag it as 'jupyterhub-service'
    docker build -t jupyterhub-service .

b. Start the JupyterHub service::

    # Run a container from the image
    docker run -d \
      --name jupyterhub \              # Name of the running container
      --network your-docker-network \   # Connect to your Docker network
      --env-file ../.env \             # Load environment variables
      -p 8000:8000 \                   # Map JupyterHub port
      -p 6000:6000 \                   # Map API port
      jupyterhub-service               # Name of the image to use


3. Restart CKAN
----------------
::

    sudo service apache2 reload

---------------
Config settings
---------------

The extension's behavior can be customized through the following environment variables:

- ``CKAN_JUPYTERNOTEBOOK_URL``: The base URL for JupyterHub access
- ``CKAN_JUPYTERHUB_BASE_URL``: The base path for JupyterHub
- ``CKAN_NETWORK``: Docker network name
- ``CKAN_STORAGE_NOTEBOOK``: Path to notebook storage
- ``CKAN_API_JUPYTERHUB``: JupyterHub API endpoint
- ``CKAN_JUPYTERHUB_TIMEOUT``: Session timeout in seconds
- ``CKAN_JUPYTERHUB_USER``: Maximum concurrent users
- ``CKAN_JUPYTERHUB_PERCENTAGE_CPU``: CPU allocation per container
- ``CKAN_JUPYTERHUB_MEMORY_LIMIT``: Memory limit per container


----------------------
Developer installation
----------------------
To install ckanext-jupyternotebook for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/SDM-TIB/CKAN_JupyterHub.git
    cd CKAN_JupyterHub/ckanext-jupyternotebook
    python setup.py develop
    pip install -r dev-requirements.txt


-----
Tests
-----

To run the tests, do::

    pytest --ckan-ini=test.ini

To run the tests and produce a coverage report, first make sure you have
``pytest-cov`` installed in your virtualenv (``pip install pytest-cov``) then run::

    pytest --ckan-ini=test.ini  --cov=ckanext.jupyternotebook


License
-------

ckanext-CKAN_JupyterHub is licensed under GPL-3.0.