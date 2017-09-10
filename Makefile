update:
	bash cloudformation/exec_cfn_command.sh update $(template)
	echo $(template)
