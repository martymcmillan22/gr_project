type EBookPresentMetadata = {
  id: string;
  title: string;
  accessScope: string;
  artifactType: string;
  hasAudio: boolean;
  hasAV: boolean;
  narrativeMode: string;
};

type EBookPresentLike = {
  metadata: EBookPresentMetadata;
};

export interface EBookPresentViewModel {
  id: string;
  title: string;
  accessScope: string;
  artifactType: string;
  hasAudio: boolean;
  hasAV: boolean;
  narrativeMode: string;
}

export function buildPresentViewModel(ebook: EBookPresentLike): EBookPresentViewModel {
  const { metadata } = ebook;

  return {
    id: metadata.id,
    title: metadata.title,
    accessScope: metadata.accessScope,
    artifactType: metadata.artifactType,
    hasAudio: metadata.hasAudio,
    hasAV: metadata.hasAV,
    narrativeMode: metadata.narrativeMode,
  };
}