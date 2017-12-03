import subprocess
import os


def main():

	while True:

		print """
		Available API endpoints:

		0.      Index                             	Index page
		----------------------------------------------------------------------
		1.      GET /containers                     List all containers
		2.      GET /containers?state=running       List running containers (only)
		3.      GET /containers/<id>                Inspect a specific container
		4.      GET /containers/<id>/logs           Dump specific container logs
		5.      GET /images                         List all images
		6.      GET /nodes                          List all nodes in the swarm
		7.      GET /services                       List all services
		8.      POST /images                        Create a new image
		9.      POST /containers                    Create a new container
		10.     PATCH /containers/<id>              Change a container's state
		11.     PATCH /images/<id>                  Change a specific image's attributes
		12.     DELETE /containers/<id>             Delete a specific container
		13.     DELETE /containers                  Delete all containers (including running)
		14.     DELETE /images/<id>                 Delete a specific image
		15.     DELETE /images                      Delete all images
		16.		Exit
		"""

		opt = input('Select an endpoint: ')

		if opt == 0:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/")

		elif opt == 1:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/containers | python -mjson.tool")

		elif opt == 2:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/containers?state=running | python -mjson.tool")

		elif opt == 3:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/containers/db74d1d16e6b | python -mjson.tool")

		elif opt == 4:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/containers/db74d1d16e6b/logs | python -mjson.tool")

		elif opt == 5:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/images | python -mjson.tool")

		elif opt == 6:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/nodes")

		elif opt == 7:
			result = os.system("curl -s -X GET -H 'Accept: application/json' http://35.197.222.57:5000/services")

		elif opt == 8:
			result = os.system("curl -H 'Accept: application/json' -F file=@./whale-say.Dockerfile http://35.197.222.57:5000/images")

		elif opt == 9:
			result = os.system("""curl -X POST -H 'Content-Type: application/json' http://35.197.222.57:5000/containers -d '{"image": "myapp"}'""")

		elif opt == 10:
			result = os.system("""curl -X PATCH -H 'Content-Type: application/json' http://35.197.222.57:5000/containers/bb5d4237f524 -d '{"state": "running"}'""")

		elif opt == 11:
			result = os.system("""curl -s -X PATCH -H 'Content-Type: application/json' http://35.197.222.57:5000/images/ae25ea956771 -d '{"tag": "test:1"}'""")

		elif opt == 12:
			result = os.system("curl -s -X DELETE -H 'Accept: application/json' http://35.197.222.57:5000/containers/bb5d4237f524" )

		elif opt == 13:
			result = os.system("curl -s -X DELETE -H 'Accept: application/json' http://35.197.222.57:5000/containers")

		elif opt == 14:
			result = os.system("curl -s -X DELETE -H 'Accept: application/json' http://35.197.222.57:5000/containers/2e3c71801c6")

		elif opt == 15:
			result = os.system("curl -s -X DELETE -H 'Accept: application/json' http://35.197.222.57:5000/images")

		elif opt == 16:
			break


if __name__ == "__main__": main()

