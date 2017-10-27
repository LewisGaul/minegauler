from DO_NOT_EDIT import make_module

encrypted_file_source = 'gAAAAABZ7NCW7vbI5JAjj2qo5ZxOq3CZvyNv1CpFcby1cjGIp0pgdTNTDqEE7A5AlfLV2hwBwxo8amrU4bYrP30pHhWuKc8olfZ_PF_zhlM8ljhMhSOU6XfsxMuHgrh6AEAjJ8xpgpF7jc0KDlVHe6AF5nPYRfYQGA==' #to be filled in dynamically

this_module = make_module(encrypted_file_source, globals())

globals().update(this_module.__dict__)

del make_module, encrypted_file_source, this_module
