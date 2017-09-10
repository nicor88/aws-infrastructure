create:
	bash cloudformation/exec_cfn_command.sh create $(template)
	echo $(template)

delete:
	bash cloudformation/exec_cfn_command.sh delete $(template)
	echo $(template)

update:
	bash cloudformation/exec_cfn_command.sh update $(template)
	echo $(template)
