import json
import os


class WorkflowPackageManifest:
    """
    Defines packaging metadata for workflows in the BTPE ecosystem.
    Provides versioning, export metadata, distribution fields,
    and compatibility declarations.
    """

    def __init__(self, workflow_id, manifest, index):
        self.workflow_id = workflow_id
        self.manifest = manifest
        self.index = index

    # ---------------------------------------------------------
    # Core Packaging Metadata
    # ---------------------------------------------------------

    def build(self):
        """
        Returns a structured packaging manifest dictionary.
        """

        return {
            "workflow_id": self.workflow_id,
            "name": self.manifest.get("name"),
            "version": self.manifest.get("version"),
            "status": self.manifest.get("status"),
            "classification": self.manifest.get("classification"),
            "semantic_tags": self.manifest.get("semantic", {}).get("tags", []),
            "btif_subjects": self.manifest.get("semantic", {}).get("btif_subjects", []),

            # Engine + Execution
            "engine_module": self.manifest.get("engine"),
            "schema_file": self.manifest.get("schema"),
            "metadata_file": self.manifest.get("metadata"),
            "propagation_file": self.manifest.get("propagation"),

            # Documentation
            "documentation": self.manifest.get("documentation"),
            "nodes": self.manifest.get("nodes", []),

            # Distribution metadata
            "package_format": "btpe-workflow",
            "distribution": {
                "exportable": True,
                "requires_autodiscovery": True,
                "registry_integration": True,
                "engine_integration": True
            },

            # Compatibility
            "compatibility": {
                "btpe_version": "1.x",
                "workflow_engine": "1.x",
                "schema_version": "1.x"
            }
        }

    # ---------------------------------------------------------
    # Export to JSON
    # ---------------------------------------------------------

    def export(self, output_path):
        """
        Writes the packaging manifest to a JSON file.
        """

        data = self.build()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=4)

        return output_path
