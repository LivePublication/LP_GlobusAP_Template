import functools

from rocrate.rocrate import ROCrate

def LP_artefact(func):
    @functools.wraps(func)
    def create_ROcrate(*args, **kwargs):
        # Create ROCrate
        # Add metadata, data, code, workflow, provenance, annotations, preview

        print("create_ROcrate (before execution of code)")
        # do somthing before
        value = func()
        #do somthing after
        return value
    return create_ROcrate
