import qiskit

old_execute = qiskit.execute


def new_execute(*args, **kwargs):
	if "experiments" in kwargs:
		ejected_qc.append(kwargs["experiments"])
	else:
		ejected_qc.append(args[0])

	return old_execute(*args, **kwargs)


qiskit.execute = new_execute
