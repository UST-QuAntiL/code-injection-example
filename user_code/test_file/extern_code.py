import qiskit
from qiskit import execute as renamed_execute, QuantumCircuit


def extern_func():
	qc = QuantumCircuit(1)
	qc.h(0)
	qc.measure_all()

	backend = qiskit.Aer.get_backend("qasm_simulator")
	job = renamed_execute(qc, backend)

	print(job.result().get_counts(qc))
