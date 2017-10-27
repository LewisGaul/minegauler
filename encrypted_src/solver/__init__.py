from DO_NOT_EDIT import make_module

encrypted_file_source = 'gAAAAABZ7NCW5E7APk9kY_pBdzykHziJ9e2_kBQRyZz47_q2LaCwrzzd4uC4y4eI0wJRVWhhYiXEM7Fm54tvbxF3qcJKs5B8PQ==' #to be filled in dynamically

this_module = make_module(encrypted_file_source, globals())

globals().update(this_module.__dict__)

del make_module, encrypted_file_source, this_module
