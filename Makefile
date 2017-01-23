test:
	# This runs all of the tests. To run an individual test, run py.test with
	# the -k flag, like " s"
	py.test test_figure.py
test_devices:
	# This runs all of the tests. To run an individual test, run py.test with
	# the -k flag, like "py.test -k test_processus"
	py.test test_devices.py