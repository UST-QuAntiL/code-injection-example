from qiskit import QuantumRegister, ClassicalRegister, execute, Aer
from qiskit import QuantumCircuit

from .external import extern_func

def generate_circuit():
    qc = QuantumCircuit()

    q = QuantumRegister(5, 'q')
    c = ClassicalRegister(3, 'c')

    qc.add_register(q)
    qc.add_register(c)

    qc.h(q[0])
    qc.h(q[1])
    qc.h(q[2])
    qc.h(q[1])
    qc.cx(q[2], q[3])
    qc.cp(0, q[1], q[0])
    qc.cx(q[2], q[4])
    qc.h(q[0])
    qc.cp(0, q[1], q[2])
    qc.cp(0, q[0], q[2])
    qc.h(q[2])
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])
    qc.measure(q[2], c[2])

    return qc

def run_circuit():
    qc = generate_circuit()
    backend = Aer.get_backend("qasm_simulator")
    job = execute(qc, backend)
    result = job.result().get_counts(qc)
    print(result)
    external_result = extern_func()
    return [result, external_result]
