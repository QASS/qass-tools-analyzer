from qass_tools.analyzer.buffer_parser import BufferErrorLogger, Buffer







def main():
	bel = BufferErrorLogger(BufferErrorLogger.create_session())

	def my_func(buff, *args, **kwargs):
		return 1
	# The Buffer will fail on opening since "test" is not a valid buffer file
	result = bel.log_errors(Buffer, "test", my_func, "additional_positional_argument", additional_keyword_argument = 1)

if __name__ == "__main__":
	main()
