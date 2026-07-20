type EBookAVPlayerEBook = {
  metadata: {
    narrativeMode: string;
  };
};

interface EBookAVPlayerProps {
  ebook: EBookAVPlayerEBook;
}

export default function EBookAVPlayer({ ebook }: EBookAVPlayerProps) {
  return (
    <section
      className="ebook-av-player"
      aria-label="E-Book AV player placeholder"
      style={{
        border: "1px dashed #587090",
        borderRadius: "12px",
        padding: "12px",
        display: "grid",
        gap: "8px",
      }}
    >
      <strong>AV Player (Phase 18 placeholder)</strong>
      <p>Narrative mode: {ebook.metadata.narrativeMode}</p>
      <p>This is a deterministic stub surface for future audio/AV playback.</p>
    </section>
  );
}