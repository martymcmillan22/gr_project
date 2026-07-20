import type { EBookPhase18ExportEnvelope } from "./ebookPhase18Export";

type PlaceholderScope = "studio" | "enterprise";

export function buildPhase18PlaceholderExportEnvelope(
  scope: PlaceholderScope,
): EBookPhase18ExportEnvelope {
  const ebookId = `${scope}-placeholder-ebook`;

  return {
    generatedAt: "phase18-placeholder",
    exportId: `${scope}-phase18-export-placeholder`,
    typeCheck: {
      generatedAt: "phase18-placeholder",
      typeCheckId: `${scope}-phase18-typecheck-placeholder`,
      orchestrator: {
        generatedAt: "phase18-placeholder",
        orchestratorId: `${scope}-phase18-orchestrator-placeholder`,
        root: {
          generatedAt: "phase18-placeholder",
          rootId: `${scope}-phase18-root-placeholder`,
          module: {
            generatedAt: "phase18-placeholder",
            moduleId: `${scope}-phase18-module-placeholder`,
            envelope: {
              generatedAt: "phase18-placeholder",
              envelopeId: `${scope}-phase18-envelope-placeholder`,
              aggregate: {
                generatedAt: "phase18-placeholder",
                aggregateId: `${scope}-phase18-aggregate-placeholder`,
                ebookId,
                presentRoot: {
                  generatedAt: "phase18-placeholder",
                  rootId: `${scope}-present-root-placeholder`,
                  module: {
                    generatedAt: "phase18-placeholder",
                    moduleId: `${scope}-present-module-placeholder`,
                    envelope: {
                      generatedAt: "phase18-placeholder",
                      envelopeId: `${scope}-present-envelope-placeholder`,
                      presentEngine: {
                        generatedAt: "phase18-placeholder",
                        engineId: `${scope}-present-engine-placeholder`,
                        envelopeId: `${scope}-narrative-envelope-placeholder`,
                        ebookId,
                        mode: "static",
                      },
                      ebookId,
                      mode: "static",
                    },
                    ebookId,
                    mode: "static",
                  },
                  ebookId,
                  mode: "static",
                },
                avRoot: {
                  generatedAt: "phase18-placeholder",
                  rootId: `${scope}-av-root-placeholder`,
                  pipeline: {
                    generatedAt: "phase18-placeholder",
                    pipelineId: `${scope}-av-pipeline-placeholder`,
                    ebookId,
                    mode: "static",
                    hasAudio: false,
                    hasAV: false,
                    markers: [],
                  },
                  ebookId,
                  mode: "static",
                  hasAudio: false,
                  hasAV: false,
                },
                mode: "static",
                hasAudio: false,
                hasAV: false,
              },
              ebookId,
              mode: "static",
              hasAudio: false,
              hasAV: false,
            },
            ebookId,
            mode: "static",
            hasAudio: false,
            hasAV: false,
          },
          ebookId,
          mode: "static",
          hasAudio: false,
          hasAV: false,
        },
      },
    },
  };
}
