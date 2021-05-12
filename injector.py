if __name__ == "__main__":
	user_code_file = open("user_code.py", "r")
	user_code = user_code_file.read()
	user_code_file.close()

	injection_code_file = open("injection_code.py", "r")
	injection_code = injection_code_file.read()
	injection_code_file.close()

	combined_code = injection_code + user_code

	global_vars = {
		"ejected_qc": []
	}

	comp_code = compile(combined_code, "injected", "exec")
	exec(comp_code, global_vars)

	print(global_vars["ejected_qc"][0].draw())
