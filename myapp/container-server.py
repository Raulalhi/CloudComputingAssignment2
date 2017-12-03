from flask import Flask, Response, render_template, request
import json
from subprocess import Popen, PIPE
import os
from tempfile import mkdtemp
from werkzeug import secure_filename

app = Flask(__name__)

#Index - contain the list of the different endpoints availabe in this API
@app.route("/")
def index():
    return """
Available API endpoints:

GET /containers                     List all containers\n
GET /containers?state=running       List running containers (only)
GET /containers/<id>                Inspect a specific container
GET /containers/<id>/logs           Dump specific container logs
GET /images                         List all images
GET /nodes			    List all nodes in the swarm
GET /services			    List all services

POST /images                        Create a new image
POST /containers                    Create a new container

PATCH /containers/<id>              Change a container's state
PATCH /images/<id>                  Change a specific image's attributes

DELETE /containers/<id>             Delete a specific container
DELETE /containers                  Delete all containers (including running)
DELETE /images/<id>                 Delete a specific image
DELETE /images                      Delete all images

"""

#--------------------------GET-----------------------------

#This function will display a list of all containers or only those which are running, using the command "docker ps" / "docker ps -a"
#data is transformed to json and then outputed to the user
@app.route('/containers', methods=['GET'])
def containers_index():
    """
    List all containers

    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers | python -mjson.tool
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/containers?state=running | python -mjson.tool

    """
    if request.args.get('state') == 'running': 
        output = docker('ps')
        resp = json.dumps(docker_ps_to_array(output))

    else:
        output = docker('ps', '-a')
        resp = json.dumps(docker_ps_to_array(output))

    return Response(response=resp, mimetype="application/json")

#This function gets all the images using the command "docker images"
#data is parsed to json and displayed to the user
@app.route('/images', methods=['GET'])
def images_index():
    """
    List all image

    """

    output = docker('images')
    resp = json.dumps(docker_images_to_array(output))
    return Response(response=resp, mimetype="application/json")

#Inspect the content  of a particular container using the command "docker inspect" + the id of the container
@app.route('/containers/<id>', methods=['GET'])
def containers_show(id):
    """
    Inspect specific container

    """

    resp = docker('inspect', id)

    return Response(response=resp, mimetype="application/json")

#Gets the logs of a particular contaienr using the command "docker logs " + id of the contaienr
@app.route('/containers/<id>/logs', methods=['GET'])
def containers_log(id):
    """
    Dump specific container logs

    """
    output = docker('logs',id)
    resp = json.dumps(docker_logs_to_object(id, output))
    return Response(response=resp, mimetype="application/json")

#Gets all the services running in the swarm using the command "docker service ls"
@app.route('/services', methods=['GET'])
def services_index():
    resp = docker('service', 'ls')
    return Response(response=resp, mimetype="application/json")

#Gets all nodes in a swarm using the command "docker node ls"
@app.route('/nodes', methods=['GET'])
def nodes_index():
    resp = docker('node', 'ls')
    return Response(response=resp, mimetype="application/json")

#----------------- DELETE -----------------------------------------

#delete an image with a particular id "docker rmi" + id
@app.route('/images/<id>', methods=['DELETE'])
def images_remove(id):
    """
    Delete a specific image

    """
    docker ('rmi', id)
    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")

#delete a container with a particular id "docker rm" + id
@app.route('/containers/<id>', methods=['DELETE'])
def containers_remove(id):
    """
    Delete a specific container - must be already stopped/killed

    """
    docker('rm', id)
    resp = '{"id: "%s"}' % id
    return Response(response=resp, mimetype="application/json")

#delete all containers, we get the list of all contaienrs, we stop them all first one by one, and then we delete them
@app.route('/containers', methods=['DELETE'])
def containers_remove_all():
    """
    Force remove all containers - dangrous!

    """

    output = docker('ps', '-a')
    allcontainers = docker_ps_to_array(output)

    for c in allcontainers:
        docker('stop', c['id'])

    for c in allcontainers:
        docker('rm', c['id'])

    return Response(response='Deleted', mimetype="application/json")

#delete all images, get all images first, then delete them one by one
@app.route('/images', methods=['DELETE'])
def images_remove_all():
    """
    Force remove all images - dangrous!

    """
    output = docker('images')
    allimages = docker_images_to_array(output)

    for i in allimages:
        docker('rmi', i['id'], '-f')

    return Response(response='Deleted', mimetype="application/json")

#-----------------------POST-----------------------------------------------

#create a container from an image using the command "docker run" and the name of the image
@app.route('/containers', methods=['POST'])
def containers_create():
    """
    Create container (from existing image using id or name)

    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "my-app"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e"}'
    curl -X POST -H 'Content-Type: application/json' http://localhost:8080/containers -d '{"image": "b14752a6590e","publish":"8081:22"}'

    """
    body = request.get_json(force=True)
    image = body['image']
    args = ('run', '-d')
    id = docker(*(args + (image,)))[0:12]
    return Response(response='{"id": "%s"}' % id, mimetype="application/json")

#creates an image from a dockerfile, a temporary directory is created and the context path is made up of the temporary directory plus a '.'
#secure_filename is used so that the user doesn't input a harmful file 
@app.route('/images', methods=['POST'])
def images_create():
    """
    Create image (from uploaded Dockerfile)

    curl -H 'Accept: application/json' -F file=@Dockerfile http://localhost:8080/images

    """
    dockerfile = request.files['file']
    dirpath = mkdtemp()
    filename = secure_filename(dockerfile.filename)
    file_path = os.path.join(dirpath, filename)
    context_path = os.path.join(dirpath, '.')
    dockerfile.save(file_path)

    resp = docker('build', '-t', filename.lower(), '-f', file_path, context_path)
    return Response(response=resp, mimetype="application/json")

#-------------------------PATCH--------------------------------

#change a container from running to stopped
@app.route('/containers/<id>', methods=['PATCH'])
def containers_update(id):
    """
    Update container attributes (support: state=running|stopped)

    curl -X PATCH -H 'Content-Type: application/json' http://localhost:5000/containers/b6cd8ea512c8 -d '{"state": "running"}'
    curl -X PATCH -H 'Content-Type: application/json' http://localhost:5000/containers/b6cd8ea512c8 -d '{"state": "stopped"}'

    """
    body = request.get_json(force=True)
    try:
        state = body['state']
        if state == 'running':
            docker('stop', id)
	elif state == 'stopped':
	    docker('run', id)
    except:
        pass

    resp = '{"id": "%s"}' % id
    return Response(response=resp, mimetype="application/json")


#Change the tag and name of an image 
@app.route('/images/<id>', methods=['PATCH'])
def images_update(id):
    """
    Update image attributes (support: name[:tag])  tag name should be lowercase only

    curl -s -X PATCH -H 'Content-Type: application/json' http://localhost:5000/images/7f2619ed1768 -d '{"tag": "test:1.0"}'

    """
    body = request.get_json(force=True)

    resp = docker('tag', id, body['tag'])
    return Response(response=resp, mimetype="application/json")





def docker(*args):
    cmd = ['docker']
    for sub in args:
        cmd.append(sub)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if stderr.startswith('Error'):
        print ('Error: {0} -> {1}'.format(' '.join(cmd), stderr))
    return stderr + stdout

# 
# Docker output parsing helpers
#

#
# Parses the output of a Docker PS command to a python List
# 
def docker_ps_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[0]
        each['image'] = c[1]
        each['name'] = c[-1]
        each['ports'] = c[-2]
        all.append(each)
    return all

#
# Parses the output of a Docker logs command to a python Dictionary
# (Key Value Pair object)
def docker_logs_to_object(id, output):
    logs = {}
    logs['id'] = id
    all = []
    for line in output.splitlines():
        all.append(line)
    logs['logs'] = all
    return logs

#
# Parses the output of a Docker image command to a python List
# 
def docker_images_to_array(output):
    all = []
    for c in [line.split() for line in output.splitlines()[1:]]:
        each = {}
        each['id'] = c[2]
        each['tag'] = c[1]
        each['name'] = c[0]
        all.append(each)
    return all

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)
