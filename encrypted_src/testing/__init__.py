from DO_NOT_EDIT import make_module

encrypted_file_source = 'gAAAAABZ7NCWDddc9x1a90coyukP8lhwOnZOx9oWWwIuk_-TRAgq6Kl2Ywf2bFdQJoZkeCGgOcwqGQhITHJtlGrDU8b1EQfqGg==' #to be filled in dynamically

this_module = make_module(encrypted_file_source, globals())

globals().update(this_module.__dict__)

del make_module, encrypted_file_source, this_module
