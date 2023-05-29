import functools
import time
import os
from rocrate.rocrate import ROCrate


def LP_artefact(dir_struct: dict,
                description: str = "description",
                creator: str = "creator"):
    
    # Create RO-Crate, and set metadata
    # Add metadata, data, code, workflow, provenance, annotations, preview
    crate = ROCrate()

    def middle(func):
      @functools.wraps(func)
      def create_ROcrate(action_id: str, body):
          print(f"----- Computation for action {action_id} starting -----")

          # Time to execute the code
          start_time = time.time()
          computation = func(action_id, body)
          total_time = time.time() - start_time

          print(f"total computation time: {total_time}")
          print(f"----- Computation for action {action_id} ending -----")

          # Write RO-Crate to disk
          crate.write_crate(os.path.join(dir_struct["crates"], f"crate_{action_id}"))
          return computation
      return create_ROcrate
    return middle
