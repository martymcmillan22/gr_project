type EBookAVLike = {
  metadata: {
    id: string;
    narrativeMode?: string;
  };
  structure: {
    avLayer: {
      markers?: string[];
    };
  };
};

export type EBookAVNarrativeMode = "static" | "guided" | "story" | "qpu";

export interface EBookAVPlan {
  ebookId: string;
  mode: EBookAVNarrativeMode;
  markers: string[];
}

export function planEBookAV(ebook: EBookAVLike): EBookAVPlan {
  const mode = (ebook.metadata.narrativeMode as EBookAVNarrativeMode) || "static";

  return {
    ebookId: ebook.metadata.id,
    mode,
    markers: ebook.structure.avLayer.markers || [],
  };
}