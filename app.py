import logging
import config
import docker
import sys
import os

from flask import Flask
from blueprint import aptb
from globus_action_provider_tools.flask.helpers import assign_json_provider

def create_app():
    app = Flask(__name__)
    assign_json_provider(app)
    app.logger.setLevel(logging.DEBUG)
    app.config.from_object(config)
    app.register_blueprint(aptb)

    # Check if docker image is available
    docker_client = docker.from_env()
    image_name = "computation_image:latest"
    image_list = [img.tags[0] for img in docker_client.images.list() if img.tags]
    if image_name not in image_list:
        # If image is not avaliable, try to build it
        try: 
            resource_dir = os.path.dirname(os.path.abspath(__file__))
            resource_dir = os.path.join(resource_dir, "method_resources/computation_docker")
            docker_client.images.build(path=resource_dir, tag=image_name)
        except Exception as e:
            print(f"An error occurred: {e}. Your additional comment goes here.")
            sys.exit(1)
    else:
        print(f"Docker image found: {image_name}")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8080)