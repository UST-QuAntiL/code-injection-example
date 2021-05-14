from functools import wraps

import qiskit

from .interceptor import QiskitInterceptor


# pass old qiskit.execute method to QiskitInterceptor
QiskitInterceptor.set_qiskit_execute(qiskit.execute)


@wraps(qiskit.execute)
def new_execute(*args, **kwargs):
	return QiskitInterceptor.execute_interceptor(*args, **kwargs)


# patch in new method
qiskit.execute = new_execute
