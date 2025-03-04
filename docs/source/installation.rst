Installation
============

This guide will help you install and set up Qorzen on your system.

Prerequisites
------------

Before installing Qorzen, you'll need:

* Python 3.12 or higher
* pip for dependency management
* PostgreSQL (optional, for database storage)

Installing with pip
------------------

If you prefer using pip instead of Poetry:

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/qorzen/qorzen.git
       cd qorzen

2. Create and activate a virtual environment:

   .. code-block:: bash

       python -m venv venv
       source venv/bin/activate  # On Windows, use: venv\Scripts\activate

3. Install dependencies:

   .. code-block:: bash

       pip install -r requirements.txt

4. Create a configuration file:

   .. code-block:: bash

       cp config.yaml.example config.yaml
       # Edit config.yaml with your preferred settings

5. Run the application:

   .. code-block:: bash

       python -m qorzen

Docker Installation
-----------------

Qorzen can also be run using Docker:

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/qorzen/qorzen.git
       cd qorzen

2. Build and start the Docker containers:

   .. code-block:: bash

       docker-compose up -d

3. Access the UI at http://localhost:8000/ and the API at http://localhost:8000/api

Next Steps
---------

After installation, you should:

1. Configure the application by editing the `config.yaml` file
2. Set up a proper database for production use
3. Create an admin user with a secure password
4. Install any plugins you need

See the :doc:`configuration` and :doc:`usage` guides for more details.