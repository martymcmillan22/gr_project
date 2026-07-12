import json
import os


class CreatorWorkflowPackageManifest:
    """
    Defines packaging metadata for the Creator Workflow in the BTPE ecosystem.
    Provides versioning, export metadata, distribution fields,
    and compatibility declarations.
    """

    def __init__(self, workflow_id, manifest, index):
        self.workflow_id = workflow_id
        self.manifest = manifest
        self.index = index

    def build(self):
        return {
            "workflow_id": self.workflow_id,
            "name": self.manifest.get("name"),
            "version": self.manifest.get("version"),
            "status": self.manifest.get("status"),
            "classification": self.manifest.get("classification"),
            "semantic_tags": self.manifest.get("semantic", {}).get("tags", []),
            "btif_subjects": self.manifest.get("semantic", {}).get("btif_subjects", []),
            "engine_module": self.manifest.get("engine"),
            "schema_file": self.manifest.get("schema"),
            "metadata_file": self.manifest.get("metadata"),
            "propagation_file": self.manifest.get("propagation"),
            "documentation": self.manifest.get("documentation"),
            "nodes": self.manifest.get("nodes", []),
            "package_format": "btpe-workflow",
            "distribution": {
                "exportable": True,
                "requires_autodiscovery": True,
                "registry_integration": True,
                "engine_integration": True,
            },
            "compatibility": {
                "btpe_version": "1.x",
                "workflow_engine": "1.x",
                "schema_version": "1.x",
            },
        }

    def export(self, output_path):
        data = self.build()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4)

        return output_path
