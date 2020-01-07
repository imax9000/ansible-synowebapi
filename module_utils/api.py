import json

from ansible.module_utils.basic import AnsibleModule


class SynoAPIModule(AnsibleModule):
    """Helper class for Synology API modules.

	Despite refering to "web API", it actually runs over ssh, invoking a binary
	called "synowebapi". This sidesteps authentication complexity, shifting it
	to the usual ssh public keys and sudoers configuration.
	"""
    def syno_web_api(self, api, method, params=None, ignore_error=False):
        """Invokes Synology API method.

		Arguments:
		  api: name of the API, e.g. SYNO.FileStation.CreateFolder
		  method: name of the method to invoke, e.g. create
		  params: any additional parameters, which get converted into JSON
		          string.
		  ignore_error: if set to True, error response from the API won't
		                immediately trigger a failure.

		Returns: a boolean indicating success and 'data' section of the
		         response.
		"""
        # Compose a command line.
        command = [
            "/usr/syno/bin/synowebapi",
            "--exec",
            "api=%s" % api,
            "method=%s" % method,
        ]
        if params:
            for k, v in params.items():
                command.append("{}={}".format(k, json.dumps(v)))

        # Run the command.
        _, stdout, _ = self.run_command(command, check_rc=True)
        response = json.loads(stdout)

        # Propagate errors.
        if not response['success'] and not ignore_error:
            self.fail_json(msg=('synowebapi returned failure.\n'
                                'Full response: {}').format(stdout))

        return response['success'], response.get('data')
