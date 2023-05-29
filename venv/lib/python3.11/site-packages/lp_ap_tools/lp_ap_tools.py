import functools
import time
import os
from rocrate.rocrate import ROCrate
from pydantic import Field, BaseModel, create_model # include pydantic in new tooling

# LP fields to be included within AP input_schema
# TODO: Build schema, and provide flexibility in chosen fields. 
LP_FIELDS = {
   'context_description': (str, Field(..., title="Some required input", description="A useful description")),
   'researcher_comment': (str, Field(..., title="Some required input", description="A useful description")),
}

def union_fields(origin_class: BaseModel, LP_fields):
   original_fields = {name: (field.outer_type_, field.field_info) for name, field in origin_class.__fields__.items()}
   return create_model(type(origin_class).__name__, **{**original_fields, **LP_FIELDS})

# Decorator for creating LP RO-Crates
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
