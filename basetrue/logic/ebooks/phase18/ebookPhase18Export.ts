export interface EBookPhase18ExportEnvelope {
  generatedAt: string;
  exportId: string;
  typeCheck: {
    generatedAt: string;
    typeCheckId: string;
    orchestrator: {
      generatedAt: string;
      orchestratorId: string;
      root: {
        generatedAt: string;
        rootId: string;
        module: {
          generatedAt: string;
          moduleId: string;
          envelope: {
            generatedAt: string;
            envelopeId: string;
            aggregate: {
              generatedAt: string;
              aggregateId: string;
              ebookId: string;
              presentRoot: {
                generatedAt: string;
                rootId: string;
                module: {
                  generatedAt: string;
                  moduleId: string;
                  envelope: {
                    generatedAt: string;
                    envelopeId: string;
                    presentEngine: {
                      generatedAt: string;
                      engineId: string;
                      envelopeId: string;
                      ebookId: string;
                      mode: "static" | "guided" | "story" | "qpu";
                    };
                    ebookId: string;
                    mode: "static" | "guided" | "story" | "qpu";
                  };
                  ebookId: string;
                  mode: "static" | "guided" | "story" | "qpu";
                };
                ebookId: string;
                mode: "static" | "guided" | "story" | "qpu";
              };
              avRoot: {
                generatedAt: string;
                rootId: string;
                pipeline: {
                  generatedAt: string;
                  pipelineId: string;
                  ebookId: string;
                  mode: "static" | "guided" | "story" | "qpu";
                  hasAudio: boolean;
                  hasAV: boolean;
                  markers: string[];
                };
                ebookId: string;
                mode: "static" | "guided" | "story" | "qpu";
                hasAudio: boolean;
                hasAV: boolean;
              };
              mode: "static" | "guided" | "story" | "qpu";
              hasAudio: boolean;
              hasAV: boolean;
            };
            ebookId: string;
            mode: "static" | "guided" | "story" | "qpu";
            hasAudio: boolean;
            hasAV: boolean;
          };
          ebookId: string;
          mode: "static" | "guided" | "story" | "qpu";
          hasAudio: boolean;
          hasAV: boolean;
        };
        ebookId: string;
        mode: "static" | "guided" | "story" | "qpu";
        hasAudio: boolean;
        hasAV: boolean;
      };
    };
  };
}
