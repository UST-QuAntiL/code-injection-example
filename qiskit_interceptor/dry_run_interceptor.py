from .interceptor import ExecuteCallMetadata, QiskitInterceptor

class DryRunInterceptor(QiskitInterceptor, priority=0):
    """Interrupt the execution and return the experiments as result.

    Args:
        priority (int): The priority of this interceptor, this interceptor has a low priority so other interceptors can run first.
    """

    def intercept_execute(self, execute_metadata: ExecuteCallMetadata) -> ExecuteCallMetadata:
        execute_metadata.should_terminate = True
        execute_metadata.termination_result = execute_metadata.kwargs.get("experiments") or execute_metadata.args[0]
        return execute_metadata
